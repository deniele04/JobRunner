"""Servidor: cola llena y ciclo de 0.5 s (ADR-0004).

handle_request debe responder con un error legible cuando la cola esta llena,
sin tumbar al servidor, y status/list deben dejar avanzar la cola.
"""
import tempfile
import time
import unittest

from jobrunner.executor import JobManager
from jobrunner.jobs import QUEUED, RUNNING
from jobrunner.server import INTERVALO_TICK, handle_request


class ServidorColaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mgr = JobManager(data_dir=self._tmp.name, max_jobs=1, queue_size=1)

    def tearDown(self):
        for job in self.mgr.list():
            try:
                self.mgr.cancel(job["id"])
            except (KeyError, ValueError):
                pass
        limite = time.monotonic() + 10
        while time.monotonic() < limite and self.mgr.list(state=RUNNING):
            self.mgr.tick()
            time.sleep(0.05)
        self._tmp.cleanup()

    def test_el_intervalo_del_ciclo_es_medio_segundo(self):
        self.assertEqual(INTERVALO_TICK, 0.5)

    def test_submit_con_cola_llena_responde_error_y_no_crea_trabajo(self):   # TC-016
        handle_request(self.mgr, {"cmd": "submit", "argv": ["sleep", "30"]})
        handle_request(self.mgr, {"cmd": "submit", "argv": ["sleep", "30"]})
        respuesta = handle_request(self.mgr, {"cmd": "submit", "argv": ["sleep", "30"]})
        self.assertEqual(respuesta, {"error": "cola llena (capacidad 1); intenta más tarde"})
        self.assertEqual(len(self.mgr.list()), 2)

    def test_el_servidor_sigue_respondiendo_despues_del_rechazo(self):
        for _ in range(3):
            handle_request(self.mgr, {"cmd": "submit", "argv": ["sleep", "30"]})
        listado = handle_request(self.mgr, {"cmd": "list"})
        self.assertEqual([j["state"] for j in listado["jobs"]], [RUNNING, QUEUED])

    def test_status_hace_avanzar_la_cola(self):
        a = handle_request(self.mgr, {"cmd": "submit", "argv": ["sleep", "0.2"]})
        b = handle_request(self.mgr, {"cmd": "submit", "argv": ["sleep", "30"]})
        self.assertEqual(b["state"], QUEUED)
        time.sleep(0.5)
        handle_request(self.mgr, {"cmd": "status", "id": a["id"]})
        self.assertEqual(handle_request(self.mgr, {"cmd": "status", "id": b["id"]})["state"], RUNNING)


if __name__ == "__main__":
    unittest.main()
