"""Pruebas de verif/scripts/procesos.sh (zombis y huérfanos) contra el servidor real.

Primero se comprueba que el script detecta bien lo que debe detectar y no da
falsos positivos. Después se usa sobre el servidor real (RF-29, RNF-25, RNF-30,
RNF-33; TC-009, TC-020, TC-024).

El cierre controlado con más detalle (SIGTERM, cola, socket, escalamiento a
SIGKILL) está en test_tc009_cierre_controlado.py.
"""
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from helpers import PROCESOS_SH, PruebaDeIntegracion, ServidorDePrueba


def procesos(*args):
    r = subprocess.run([str(PROCESOS_SH), *args], capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout, r.stderr


def matar_grupos(salida):
    """Mata los grupos de procesos que el script marcó como HUERFANO."""
    for pid in re.findall(r"^HUERFANO\t(\d+)", salida, re.M):
        try:
            os.killpg(int(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def pids_con(patron):
    """PID de los procesos cuya linea de comando coincide con `patron` (expresion regular)."""
    r = subprocess.run(["ps", "-eo", "pid=,args="], capture_output=True, text=True, timeout=30)
    encontrados = []
    for linea in r.stdout.splitlines():
        pid, _, args = linea.strip().partition(" ")
        if pid.isdigit() and int(pid) != os.getpid() and re.search(patron, args):
            encontrados.append(int(pid))
    return encontrados


def ppid_de(pid):
    r = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)], capture_output=True, text=True, timeout=30)
    return int(r.stdout.strip()) if r.stdout.strip().isdigit() else None


# Un "adoptante": proceso que se declara subreaper (PR_SET_CHILD_SUBREAPER = 36) y lanza
# un lider de sesion que queda huerfano. Los huerfanos de sus descendientes terminan
# adoptados por este proceso y no por el PID 1, igual que en WSL (DEF-005).
ADOPTANTE = """
import ctypes, subprocess, sys, time
if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
    sys.exit(3)
subprocess.run(["sh", "-c", "setsid sleep 306 >/dev/null 2>&1 &"], check=True)
time.sleep(30)
"""


class BaseConLineaBase(PruebaDeIntegracion):
    """Guarda la línea base de PID ANTES de levantar el servidor."""

    def setUp(self):
        fd, self.base = tempfile.mkstemp(prefix="jobrunner-base-")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self.base) and os.remove(self.base))
        codigo, _, _ = procesos("guardar", self.base)
        self.assertEqual(codigo, 0)
        super().setUp()

    def revisar(self, *extra):
        return procesos("revisar", "--base", self.base, *extra)


class TestProcesosSh(unittest.TestCase):
    """El script en sí, sin servidor."""

    def test_sin_argumentos_es_error_de_uso(self):
        self.assertEqual(procesos()[0], 2)

    def test_revisar_exige_base_o_patron(self):
        codigo, _, err = procesos("revisar")
        self.assertEqual(codigo, 2)
        self.assertIn("--base", err)

    def test_sistema_limpio_da_codigo_0(self):
        with tempfile.TemporaryDirectory() as d:
            base = os.path.join(d, "base")
            procesos("guardar", base)
            codigo, salida, _ = procesos("revisar", "--base", base)
        self.assertEqual(codigo, 0, salida)

    def test_detecta_un_huerfano(self):
        with tempfile.TemporaryDirectory() as d:
            base = os.path.join(d, "base")
            procesos("guardar", base)
            # El intermedio muere y deja al `sleep` (líder de su propia sesión) huérfano.
            subprocess.run(["sh", "-c", "setsid sleep 304 >/dev/null 2>&1 &"], check=True)
            time.sleep(0.3)
            codigo, salida, _ = procesos("revisar", "--base", base, "--patron", "sleep 304")
            self.addCleanup(matar_grupos, salida)
        self.assertEqual(codigo, 1, salida)
        self.assertRegex(salida, r"HUERFANO\t\d+")

    def test_detecta_un_huerfano_adoptado_por_otro_proceso_que_no_es_el_pid_1(self):
        """DEF-005 (RNF-30). En WSL el huerfano lo adopta otro proceso, no el PID 1.

        Aqui el adoptante es un subreaper explicito, asi que la prueba reproduce lo mismo en
        cualquier Linux: un lider de sesion cuyo padre ya no es el servidor es un huerfano.
        """
        with tempfile.TemporaryDirectory() as d:
            base = os.path.join(d, "base")
            procesos("guardar", base)
            adoptante = subprocess.Popen([sys.executable, "-c", ADOPTANTE])
            self.addCleanup(lambda: (adoptante.kill(), adoptante.wait()))
            self.addCleanup(lambda: [matar_grupos("HUERFANO\t%d" % p) for p in pids_con(r"^sleep 306$")])
            for _ in range(50):
                if adoptante.poll() is not None:
                    break
                if any(ppid_de(p) == adoptante.pid for p in pids_con(r"^sleep 306$")):
                    break
                time.sleep(0.1)
            if adoptante.poll() == 3:
                self.skipTest("este sistema no permite declarar un subreaper (prctl)")
            hijos = [p for p in pids_con(r"^sleep 306$") if ppid_de(p) == adoptante.pid]
            self.assertTrue(hijos, "el adoptante no llego a adoptar al sleep")
            self.assertNotEqual(adoptante.pid, 1)
            codigo, salida, _ = procesos("revisar", "--base", base, "--patron", "sleep 306")
        self.assertEqual(codigo, 1, salida)
        self.assertRegex(salida, r"HUERFANO\t\d+\tsid=\d+\tsleep 306")

    def test_detecta_un_zombi_del_servidor(self):
        with tempfile.TemporaryDirectory() as d:
            base = os.path.join(d, "base")
            procesos("guardar", base)
            # Un "servidor" (lleva jobrunner.server en su línea de comando) que no recoge a su hijo.
            padre = subprocess.Popen([
                sys.executable, "-c",
                "import subprocess,time; subprocess.Popen(['true']); time.sleep(15)",
                "jobrunner.server",
            ])
            self.addCleanup(lambda: (padre.kill(), padre.wait()))
            time.sleep(0.6)
            codigo, salida, _ = procesos("revisar", "--base", base)
        self.assertEqual(codigo, 1, salida)
        self.assertRegex(salida, r"ZOMBI\t\d+")


class TestProcesosConServidor(BaseConLineaBase):
    """El script usado sobre el servidor real."""

    def test_servidor_en_reposo_no_deja_nada(self):
        self.servidor.detener()
        codigo, salida, _ = self.revisar("--patron", "sleep|jobrunner")
        self.assertEqual(codigo, 0, salida)

    def test_un_trabajo_en_ejecucion_no_es_un_huerfano(self):
        """DEF-005: al no exigir PPID 1, un trabajo vivo no debe confundirse con un huérfano.

        Es lider de sesion, pero su padre sigue siendo el servidor.
        """
        self.servidor.enviar("--", "sleep", "301")
        self.assertTrue(pids_con(r"^sleep 301$"), "el trabajo no esta corriendo")
        codigo, salida, _ = self.revisar("--patron", "sleep 301")
        self.assertEqual(codigo, 0, salida)

    def test_si_el_servidor_muere_de_golpe_el_trabajo_queda_huerfano(self):
        # Falla dura (kill -9): el script debe detectar al hijo huérfano.
        # Es el caso que cubre ADR-0005 al arrancar de nuevo (RNF-30).
        self.servidor.enviar("--", "sleep", "300")
        self.servidor.matar()
        codigo, salida, _ = self.revisar("--patron", "sleep 300")
        self.addCleanup(matar_grupos, salida)
        self.assertEqual(codigo, 1, salida)
        self.assertRegex(salida, r"HUERFANO\t\d+\tsid=\d+\tsleep 300")

    def test_servidor_inactivo_no_deja_zombis(self):
        """RF-29 / RNF-33 (TC-020, TC-024). DEF-004, corregido con el ciclo de 0,5 s.

        Un trabajo que termina y nadie consulta debe ser recogido por el servidor
        (`tick()` cada 0,5 s, ADR-0004) y no quedar como proceso zombi.
        """
        self.servidor.enviar("--", "true")
        time.sleep(1.5)
        codigo, salida, _ = self.revisar()
        self.assertEqual(codigo, 0, salida)

    def test_cierre_ordenado_no_deja_huerfanos(self):
        """RF-15 / RNF-25 / RNF-30 (TC-009). Cierre controlado de ADR-0006.

        Al recibir Ctrl+C el servidor cancela los trabajos RUNNING; no debe quedar
        ningún `sleep` huérfano.
        """
        self.servidor.enviar("--", "sleep", "300")
        self.servidor.detener()
        codigo, salida, _ = self.revisar("--patron", "sleep 300")
        self.addCleanup(matar_grupos, salida)
        self.assertEqual(codigo, 0, salida)


if __name__ == "__main__":
    unittest.main()
