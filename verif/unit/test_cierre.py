"""Cierre controlado del JobManager (ADR-0006, RF-15, RNF-25, RNF-30).

cerrar() cancela los RUNNING (SIGTERM y, a los 5 s, SIGKILL), no arranca nada de
la cola, deja los QUEUED intactos y no acepta trabajos nuevos.
"""
import os
import tempfile
import time
import unittest
from unittest import mock

from jobrunner import executor
from jobrunner.executor import Cerrando, JobManager
from jobrunner.jobs import CANCELED, QUEUED, RUNNING, SUCCEEDED
from jobrunner.store import Store

IGNORA_SIGTERM = ["sh", "-c", "trap '' TERM; while :; do sleep 1; done"]


def grupo_vivo(pid):
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return False
    try:
        with open("/proc/" + str(pid) + "/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


class CierreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.pids = []
        self.stores = []

    def tearDown(self):
        for pid in self.pids:
            try:
                os.killpg(pid, 9)
            except (ProcessLookupError, PermissionError):
                pass
        for store in self.stores:
            store.close()
        self._tmp.cleanup()

    def manager(self, **kwargs):
        store = Store(os.path.join(self.dir, "jobrunner.db"))
        self.stores.append(store)
        return JobManager(data_dir=self.dir, store=store, **kwargs)

    def enviar(self, mgr, argv):
        job = mgr.submit(argv)
        if job.get("pid"):
            self.pids.append(job["pid"])
        return job

    def test_cierra_los_running_sin_dejar_procesos(self):
        mgr = self.manager()
        job = self.enviar(mgr, ["sleep", "300"])
        resumen = mgr.cerrar()
        final = mgr.get(job["id"])
        self.assertEqual(final["state"], CANCELED)
        self.assertEqual(final["exit_code"], -15)
        self.assertFalse(grupo_vivo(job["pid"]), "el proceso del trabajo sigue vivo")
        self.assertEqual(resumen, {"cancelados": 1, "en_cola": 0})

    def test_los_queued_se_conservan_y_no_arrancan(self):
        mgr = self.manager(max_jobs=1, queue_size=3)
        primero = self.enviar(mgr, ["sleep", "300"])
        segundo = self.enviar(mgr, ["sleep", "301"])
        self.assertEqual(segundo["state"], QUEUED)
        resumen = mgr.cerrar()
        self.assertEqual(mgr.get(primero["id"])["state"], CANCELED)
        self.assertEqual(mgr.get(segundo["id"])["state"], QUEUED)
        self.assertIsNone(mgr.get(segundo["id"])["pid"], "la cola arrancó durante el cierre")
        self.assertEqual(resumen["en_cola"], 1)

    def test_la_cola_conservada_se_reanuda_en_el_siguiente_arranque(self):
        mgr = self.manager(max_jobs=1, queue_size=3)
        self.enviar(mgr, ["sleep", "300"])
        segundo = self.enviar(mgr, ["true"])
        mgr.cerrar()
        self.stores.pop().close()

        nuevo = self.manager(max_jobs=1, queue_size=3)
        nuevo.recuperar()
        limite = time.monotonic() + 5
        while time.monotonic() < limite and nuevo.get(segundo["id"])["state"] != SUCCEEDED:
            nuevo.tick()
            time.sleep(0.05)
        self.assertEqual(nuevo.get(segundo["id"])["state"], SUCCEEDED)

    def test_no_acepta_trabajos_nuevos_durante_el_cierre(self):
        mgr = self.manager()
        mgr.cerrar()
        with self.assertRaises(Cerrando):
            mgr.submit(["true"])

    def test_el_estado_final_de_un_trabajo_ya_terminado_no_se_reescribe(self):
        mgr = self.manager()
        job = self.enviar(mgr, ["true"])
        time.sleep(0.5)
        resumen = mgr.cerrar()
        self.assertEqual(mgr.get(job["id"])["state"], SUCCEEDED)
        self.assertEqual(resumen["cancelados"], 0)

    def test_escala_a_sigkill_si_el_trabajo_ignora_sigterm(self):
        mgr = self.manager()
        job = self.enviar(mgr, IGNORA_SIGTERM)
        time.sleep(0.3)
        with mock.patch.object(executor, "ESPERA_SIGKILL", 1.0):
            inicio = time.monotonic()
            mgr.cerrar()
            duracion = time.monotonic() - inicio
        final = mgr.get(job["id"])
        self.assertEqual(final["state"], CANCELED)
        self.assertEqual(final["exit_code"], -9)
        self.assertGreaterEqual(duracion, 0.9)
        self.assertLess(duracion, 4.0)
        self.assertFalse(grupo_vivo(job["pid"]))

    def test_forzar_envia_sigkill_de_inmediato(self):
        mgr = self.manager()
        job = self.enviar(mgr, IGNORA_SIGTERM)
        time.sleep(0.3)
        inicio = time.monotonic()
        mgr.cerrar(forzar=lambda: True)
        self.assertLess(time.monotonic() - inicio, 2.0)
        self.assertEqual(mgr.get(job["id"])["exit_code"], -9)
        self.assertFalse(grupo_vivo(job["pid"]))

    def test_el_resultado_del_cierre_queda_guardado(self):
        mgr = self.manager()
        job = self.enviar(mgr, ["sleep", "300"])
        mgr.cerrar()
        guardado = self.stores[0].get(job["id"])
        self.assertEqual(guardado.state, CANCELED)


if __name__ == "__main__":
    unittest.main()
