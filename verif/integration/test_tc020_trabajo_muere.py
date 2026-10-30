"""TC-020: muerte inesperada de un proceso hijo (RF-29, RNF-30, RNF-33).

Con el servidor real, el proceso de un trabajo muere por una senal ajena al
servicio (kill -9 o kill -15 desde fuera). El servidor debe detectarlo, dejar el
trabajo en un estado terminal con diagnostico, no dejar zombis ni huerfanos, no
afectar a los demas trabajos y reutilizar el lugar liberado.
"""
import os
import signal
import time
import unittest

from helpers_procesos import ConLineaBase


class TestTC020TrabajoMuere(ConLineaBase):
    def lanzar(self, *argv):
        codigo, trabajo = self.servidor.enviar("--", *argv)
        self.assertEqual(codigo, 0, trabajo)
        return trabajo

    def esperar_estado(self, job_id, estado, limite=8.0):
        fin = time.monotonic() + limite
        while time.monotonic() < fin:
            if self.servidor.estado(job_id)["state"] == estado:
                return
            time.sleep(0.1)
        self.fail("el trabajo %s no llego a %s en %.0f s" % (job_id, estado, limite))

    def test_kill_9_al_trabajo_lo_deja_failed_con_diagnostico(self):
        trabajo = self.lanzar("sleep", "300")
        os.kill(trabajo["pid"], signal.SIGKILL)
        final = self.servidor.esperar_estado_final(trabajo["id"])
        self.assertEqual(final["state"], "FAILED")
        self.assertEqual(final["exit_code"], -9)
        self.assertEqual(final["error"], "SIGKILL")
        self.assertIsNotNone(final["finished_at"])
        self.assertSinZombisNiHuerfanos()
        lineas = [l for l in self.bitacora().splitlines() if "terminado job=" + trabajo["id"] in l]
        self.assertTrue(any("estado=FAILED" in l and "codigo=-9" in l for l in lineas), lineas)

    def test_kill_15_externo_lo_deja_failed_con_sigterm(self):
        trabajo = self.lanzar("sleep", "300")
        os.kill(trabajo["pid"], signal.SIGTERM)
        final = self.servidor.esperar_estado_final(trabajo["id"])
        self.assertEqual(final["state"], "FAILED")   # no fue una cancelacion pedida al servicio
        self.assertEqual(final["exit_code"], -15)
        self.assertEqual(final["error"], "SIGTERM")

    def test_los_demas_trabajos_siguen_en_ejecucion(self):
        a = self.lanzar("sleep", "300")
        b = self.lanzar("sleep", "300")
        os.kill(a["pid"], signal.SIGKILL)
        self.servidor.esperar_estado_final(a["id"])
        self.assertEqual(self.servidor.estado(b["id"])["state"], "RUNNING")
        self.assertIsNone(self.servidor.proceso.poll(), "el servidor termino")

    def test_el_lugar_liberado_lo_ocupa_el_siguiente_de_la_cola(self):
        # Con el limite por defecto (3 simultaneos) el cuarto trabajo espera en la cola.
        trabajos = [self.lanzar("sleep", "300") for _ in range(4)]
        self.assertEqual(self.servidor.estado(trabajos[3]["id"])["state"], "QUEUED")
        os.kill(trabajos[0]["pid"], signal.SIGKILL)
        self.esperar_estado(trabajos[3]["id"], "RUNNING")
        estados = sorted(self.servidor.estado(t["id"])["state"] for t in trabajos)
        self.assertEqual(estados, ["FAILED", "RUNNING", "RUNNING", "RUNNING"])

    def test_trabajo_que_termina_sin_que_nadie_lo_consulte_no_queda_zombi(self):
        # Antes (DEF-004) quedaba como zombi hasta la siguiente consulta.
        trabajo = self.lanzar("true")
        time.sleep(1.5)
        self.assertSinZombisNiHuerfanos()
        self.assertEqual(self.servidor.estado(trabajo["id"])["state"], "SUCCEEDED")


if __name__ == "__main__":
    unittest.main()
