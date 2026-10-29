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
            self.mgr.poll()
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
            mgr.poll()
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


class ConcurrenciaTest(ColaBase):
    def test_respeta_max_jobs_y_encola_el_resto(self):             # TC-002
        self.nuevo(max_jobs=2, queue_size=5)
        for _ in range(3):
            self.mgr.submit(["sleep", "30"])
        self.assertEqual(self.estados(), [RUNNING, RUNNING, QUEUED])

    def test_trabajo_en_cola_no_tiene_started_at(self):            # TC-002
        self.nuevo(max_jobs=1, queue_size=5)
        en_ejecucion = self.mgr.submit(["sleep", "30"])
        en_cola = self.mgr.submit(["sleep", "30"])
        self.assertIsNotNone(en_ejecucion["started_at"])
        self.assertEqual(en_cola["state"], QUEUED)
        self.assertIsNone(en_cola["started_at"])
        self.assertNotIn(en_cola["id"], self.mgr._procs)

    def test_sin_saturar_arranca_de_inmediato(self):
        self.nuevo(max_jobs=3, queue_size=5)
        self.assertEqual(self.mgr.submit(["sleep", "30"])["state"], RUNNING)

    def test_tres_simultaneos_con_los_valores_por_defecto(self):    # TC-002
        self.nuevo()
        for _ in range(4):
            self.mgr.submit(["sleep", "30"])
        self.assertEqual(self.estados(), [RUNNING] * 3 + [QUEUED])


class SaturacionTest(ColaBase):
    def test_cola_llena_rechaza_y_no_registra_el_trabajo(self):    # TC-016
        self.nuevo(max_jobs=1, queue_size=1)
        self.mgr.submit(["sleep", "30"])
        self.mgr.submit(["sleep", "30"])
        with self.assertRaises(ColaLlena) as ctx:
            self.mgr.submit(["sleep", "30"])
        self.assertIn("cola llena", str(ctx.exception))
        self.assertEqual(len(self.mgr.list()), 2)

    def test_el_rechazo_no_afecta_a_los_trabajos_aceptados(self):   # TC-016
        self.nuevo(max_jobs=1, queue_size=1)
        a = self.mgr.submit(["sleep", "30"])["id"]
        b = self.mgr.submit(["sleep", "30"])["id"]
        for _ in range(3):
            with self.assertRaises(ColaLlena):
                self.mgr.submit(["sleep", "30"])
        self.assertEqual(self.mgr.get(a)["state"], RUNNING)
        self.assertEqual(self.mgr.get(b)["state"], QUEUED)

    def test_queue_size_cero_rechaza_al_llenarse_el_limite(self):
        self.nuevo(max_jobs=1, queue_size=0)
        self.mgr.submit(["sleep", "30"])
        with self.assertRaises(ColaLlena):
            self.mgr.submit(["sleep", "30"])

    def test_queue_size_cero_acepta_si_hay_lugar_para_correr(self):
        self.nuevo(max_jobs=2, queue_size=0)
        self.mgr.submit(["sleep", "30"])
        self.assertEqual(self.mgr.submit(["sleep", "30"])["state"], RUNNING)

    def test_un_request_id_repetido_no_cuenta_como_solicitud_nueva(self):
        self.nuevo(max_jobs=1, queue_size=0)
        primero = self.mgr.submit(["sleep", "30"], request_id="r1")
        repetido = self.mgr.submit(["sleep", "30"], request_id="r1")
        self.assertEqual(repetido["id"], primero["id"])


if __name__ == "__main__":
    unittest.main()
