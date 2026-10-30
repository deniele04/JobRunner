"""TC-009 — Cierre controlado (RF-15, RNF-25, RNF-30). ADR-0006.

Servidor real. Al recibir Ctrl+C (SIGINT) o SIGTERM el servicio debe: dejar de
aceptar solicitudes, cancelar los trabajos RUNNING (SIGTERM al grupo y SIGKILL a
los 5 s), conservar los QUEUED para el siguiente arranque, eliminar el socket y
no dejar procesos huérfanos.
"""
import os
import re
import signal
import subprocess
import tempfile
import time
import unittest

from helpers import PROCESOS_SH, PruebaDeIntegracion

IGNORA_SIGTERM = "trap '' TERM; while :; do sleep 1; done"


def procesos(*args):
    r = subprocess.run([str(PROCESOS_SH), *args], capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout


def matar_grupos(salida):
    for pid in re.findall(r"^HUERFANO\t(\d+)", salida, re.M):
        try:
            os.killpg(int(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


class PruebaDeCierre(PruebaDeIntegracion):
    """Guarda la línea base de procesos antes de levantar el servidor."""

    def setUp(self):
        fd, self.base = tempfile.mkstemp(prefix="jobrunner-base-")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self.base) and os.remove(self.base))
        procesos("guardar", self.base)
        super().setUp()

    def sin_huerfanos(self, patron):
        codigo, salida = procesos("revisar", "--base", self.base, "--patron", patron)
        self.addCleanup(matar_grupos, salida)
        self.assertEqual(codigo, 0, salida)


class TestTC009CierreControlado(PruebaDeCierre):

    def test_ctrl_c_cancela_los_trabajos_en_ejecucion_sin_huerfanos(self):
        _, trabajo = self.servidor.enviar("--", "sleep", "300")
        self.servidor.detener()
        self.assertEqual(self.servidor.proceso.returncode, 0, "el servidor debe terminar con código 0")
        self.sin_huerfanos("sleep 300")

    def test_sigterm_tambien_cierra_de_forma_controlada(self):
        self.servidor.enviar("--", "sleep", "301")
        self.servidor.detener(senal=signal.SIGTERM)
        self.assertEqual(self.servidor.proceso.returncode, 0)
        self.sin_huerfanos("sleep 301")

    def test_el_trabajo_cancelado_queda_canceled_tras_reiniciar(self):
        _, trabajo = self.servidor.enviar("--", "sleep", "302")
        self.servidor.detener()
        self.servidor.iniciar()
        final = self.servidor.estado(trabajo["id"])
        self.assertEqual(final["state"], "CANCELED")
        self.assertIsNotNone(final["finished_at"])

    def test_se_elimina_el_socket(self):
        self.servidor.detener()
        self.assertFalse(os.path.exists(self.servidor.socket), "el socket sigue en disco")

    def test_se_conserva_la_cola_para_el_siguiente_arranque(self):
        # Con un solo lugar, el segundo trabajo espera en la cola.
        self.servidor.detener()
        self.servidor.iniciar(opciones=["--max-jobs", "1"])
        _, primero = self.servidor.enviar("--", "sleep", "303")
        _, segundo = self.servidor.enviar("--", "sh", "-c", "exit 0")
        self.assertEqual(segundo["state"], "QUEUED")

        self.servidor.detener()
        # El que corría se canceló; el de la cola no se tocó ni se perdió.
        self.servidor.iniciar()
        self.assertEqual(self.servidor.estado(primero["id"])["state"], "CANCELED")
        reanudado = self.servidor.esperar_estado_final(segundo["id"])
        self.assertEqual(reanudado["state"], "SUCCEEDED", "el trabajo en cola no se reanudó")
        self.assertEqual(reanudado["exit_code"], 0)

    def test_no_arranca_trabajos_de_la_cola_durante_el_cierre(self):
        self.servidor.detener()
        self.servidor.iniciar(opciones=["--max-jobs", "1"])
        self.servidor.enviar("--", "sleep", "304")
        _, en_cola = self.servidor.enviar("--", "sleep", "305")
        self.servidor.detener()
        # Si la cola hubiera arrancado al morir el primero, quedaría un `sleep 305` vivo.
        self.sin_huerfanos("sleep 305")
        self.servidor.iniciar()
        self.assertNotEqual(self.servidor.estado(en_cola["id"])["state"], "CANCELED")

    def test_trabajo_que_ignora_sigterm_se_mata_a_los_5_segundos(self):
        _, trabajo = self.servidor.enviar("--", "sh", "-c", IGNORA_SIGTERM)
        time.sleep(0.3)
        inicio = time.monotonic()
        self.servidor.detener()
        duracion = time.monotonic() - inicio
        self.assertGreaterEqual(duracion, 4.5, "debió esperar el plazo de SIGTERM")
        self.assertLess(duracion, 9.0, "el cierre se alargó demasiado")
        self.sin_huerfanos("sleep 1|while")
        self.servidor.iniciar()
        final = self.servidor.estado(trabajo["id"])
        self.assertEqual(final["state"], "CANCELED")
        self.assertEqual(final["exit_code"], -9)

    def test_no_acepta_solicitudes_mientras_cierra(self):
        # RF-15: durante el cierre (aquí dura ~5 s por un trabajo terco) no entran trabajos nuevos.
        self.servidor.enviar("--", "sh", "-c", IGNORA_SIGTERM)
        time.sleep(0.3)
        self.servidor.proceso.send_signal(signal.SIGINT)
        time.sleep(1.5)
        codigo, _, err = self.servidor.cli("submit", "--", "true")
        self.assertNotEqual(codigo, 0, "el servicio aceptó un trabajo durante el cierre")
        self.assertIn("no se pudo conectar", err)

    def test_segundo_ctrl_c_fuerza_el_cierre_inmediato(self):
        self.servidor.enviar("--", "sh", "-c", IGNORA_SIGTERM)
        time.sleep(0.3)
        inicio = time.monotonic()
        self.servidor.proceso.send_signal(signal.SIGINT)
        time.sleep(1.0)
        self.servidor.proceso.send_signal(signal.SIGINT)
        self.servidor.proceso.wait(timeout=8)
        self.assertLess(time.monotonic() - inicio, 4.0, "el segundo Ctrl+C no adelantó el SIGKILL")
        self.sin_huerfanos("sleep 1|while")


if __name__ == "__main__":
    unittest.main()
