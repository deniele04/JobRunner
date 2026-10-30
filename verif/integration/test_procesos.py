"""Pruebas de verif/scripts/procesos.sh (zombis y huérfanos) contra el servidor real.

Primero se comprueba que el script detecta bien lo que debe detectar y no da
falsos positivos. Después se usa sobre el servidor real (RF-29, RNF-25, RNF-30,
RNF-33; TC-009, TC-020, TC-024).

La última prueba describe comportamiento que el servidor todavía no tiene (ver
su docstring). Va marcada `expectedFailure` para que la suite siga en verde y
avise (`unexpected success`) el día que se implemente, momento de quitar la marca.
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

    @unittest.expectedFailure
    def test_cierre_ordenado_no_deja_huerfanos(self):
        """RF-15 / RNF-25 / RNF-30 (TC-009). Pendiente de implementar: ADR-0006.

        Hoy el servidor, al recibir Ctrl+C, no cancela los trabajos RUNNING y el
        `sleep` queda huérfano. Con el cierre controlado de ADR-0006 debe terminar.
        """
        self.servidor.enviar("--", "sleep", "300")
        self.servidor.detener()
        codigo, salida, _ = self.revisar("--patron", "sleep 300")
        self.addCleanup(matar_grupos, salida)
        self.assertEqual(codigo, 0, salida)


if __name__ == "__main__":
    unittest.main()
