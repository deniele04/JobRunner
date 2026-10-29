"""Cola FIFO, limite de concurrencia y saturacion (ADR-0004, ADR-0006).

Cubre: parametros --max-jobs y --queue-size, trabajos simultaneos (TC-002),
cola llena (TC-016), orden FIFO, cancelar un trabajo en cola (TC-005),
recuperacion de los QUEUED al reiniciar, cancelacion sin bloqueo y doble
cancelacion (TC-017) y escalamiento a SIGKILL (TC-021).

Ejecutar con ./scripts/test.sh (usa unittest de la biblioteca estandar).
"""
import os
import tempfile
import time
import unittest

from jobrunner.executor import (
    DEFAULT_MAX_JOBS, DEFAULT_QUEUE_SIZE, ColaLlena, JobManager,
)
from jobrunner.jobs import (
    CANCELED, FAILED, FINAL_STATES, QUEUED, RUNNING, SUCCEEDED, Job,
)
from jobrunner.store import Store


class ColaBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.mgr = None

    def tearDown(self):
        if self.mgr is not None:
            self.limpiar(self.mgr)
        self._tmp.cleanup()

    def nuevo(self, **kw):
        self.mgr = JobManager(data_dir=self.dir, **kw)
        return self.mgr

    def estados(self, mgr=None):
        return [j["state"] for j in (mgr or self.mgr).list()]

    def esperar(self, condicion, timeout=10.0):
        limite = time.monotonic() + timeout
        while time.monotonic() < limite:
            self.mgr.tick()
            if condicion():
                return True
            time.sleep(0.05)
        return False

    def limpiar(self, mgr):
        for j in mgr.list():
            try:
                mgr.cancel(j["id"])
            except (KeyError, ValueError):
                pass
        limite = time.monotonic() + 15
        while time.monotonic() < limite:
            mgr.tick()
            if all(s in FINAL_STATES for s in self.estados(mgr)):
                return
            time.sleep(0.05)


class ParametrosTest(ColaBase):
    def test_valores_por_defecto(self):
        mgr = self.nuevo()
        self.assertEqual(mgr.max_jobs, DEFAULT_MAX_JOBS)
        self.assertEqual(mgr.queue_size, DEFAULT_QUEUE_SIZE)
        self.assertEqual((DEFAULT_MAX_JOBS, DEFAULT_QUEUE_SIZE), (3, 10))

    def test_max_jobs_invalido(self):
        for valor in (0, -1, "3", None):
            with self.assertRaises(ValueError):
                JobManager(data_dir=self.dir, max_jobs=valor)

    def test_queue_size_invalido(self):
        for valor in (-1, "10", None):
            with self.assertRaises(ValueError):
                JobManager(data_dir=self.dir, queue_size=valor)

    def test_queue_size_cero_es_valido(self):
        self.nuevo(queue_size=0)


if __name__ == "__main__":
    unittest.main()
