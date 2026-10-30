"""TC-022: interrupcion del proceso durante una escritura en SQLite.

Un proceso hijo escribe en la base y muere con SIGKILL en dos momentos: antes
de confirmar la transaccion y justo despues de confirmarla. Se repite varias
veces. Resultado esperado (ADR-0002): una escritura no confirmada no deja
rastro, una confirmada sobrevive, y la base queda integra y utilizable.
"""
import os
import subprocess
import sys
import tempfile
import unittest

from jobrunner.jobs import FAILED, RUNNING, SUCCEEDED, Job
from jobrunner.store import Store

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPETICIONES = 10

SIN_CONFIRMAR = """
import os, signal, sys
from jobrunner.store import Store
store = Store(sys.argv[1])
store._conn.execute(
    "UPDATE jobs SET state = 'SUCCEEDED', exit_code = 0 WHERE id = ?", (sys.argv[2],)
)
os.kill(os.getpid(), signal.SIGKILL)
"""

CONFIRMADA = """
import os, signal, sys
from jobrunner.store import Store
store = Store(sys.argv[1])
job = store.get(sys.argv[2])
job.state = "SUCCEEDED"
job.exit_code = 0
store.save(job)
os.kill(os.getpid(), signal.SIGKILL)
"""


class InterrupcionEscrituraTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self._tmp.name, "jobrunner.db")

    def tearDown(self):
        self._tmp.cleanup()

    def preparar(self, cantidad):
        store = Store(self.ruta)
        jobs = []
        for _ in range(cantidad):
            job = Job.new(["sleep", "1"])
            job.state = RUNNING
            job.pid = 4242
            store.save(job)
            jobs.append(job)
        store.close()
        return jobs

    def matar_en_escritura(self, codigo, job_id):
        entorno = dict(os.environ, PYTHONPATH=os.path.join(RAIZ, "src"))
        proc = subprocess.run(
            [sys.executable, "-c", codigo, self.ruta, job_id],
            env=entorno, capture_output=True, timeout=30,
        )
        self.assertEqual(proc.returncode, -9, "el proceso hijo debio morir por SIGKILL")

    def integridad(self):
        store = Store(self.ruta)
        try:
            return store._conn.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            store.close()

    def test_escritura_no_confirmada_no_deja_rastro(self):
        jobs = self.preparar(REPETICIONES)
        for job in jobs:
            self.matar_en_escritura(SIN_CONFIRMAR, job.id)
        store = Store(self.ruta)
        for job in jobs:
            guardado = store.get(job.id)
            self.assertEqual(guardado.state, RUNNING)
            self.assertIsNone(guardado.exit_code)
        self.assertEqual(len(store.list()), REPETICIONES)
        store.close()
        self.assertEqual(self.integridad(), "ok")

    def test_escritura_confirmada_sobrevive_a_la_muerte_del_proceso(self):
        jobs = self.preparar(REPETICIONES)
        for job in jobs:
            self.matar_en_escritura(CONFIRMADA, job.id)
        store = Store(self.ruta)
        for job in jobs:
            self.assertEqual(store.get(job.id).state, SUCCEEDED)
        store.close()
        self.assertEqual(self.integridad(), "ok")

    def test_la_base_sigue_siendo_utilizable_despues_de_la_interrupcion(self):
        jobs = self.preparar(1)
        self.matar_en_escritura(SIN_CONFIRMAR, jobs[0].id)
        store = Store(self.ruta)
        job = store.get(jobs[0].id)
        job.state = FAILED
        job.error = "interrumpido por reinicio"
        store.save(job)
        self.assertEqual(store.get(job.id).state, FAILED)
        store.close()


if __name__ == "__main__":
    unittest.main()
