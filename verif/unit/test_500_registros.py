"""TC-026 (RNF-06): 500 registros sin pérdida de metadatos, a nivel del almacén y del gestor.

Complementa la prueba de integración (`verif/integration/test_tc026_500_registros.py`),
que lo repite con el servidor real y el CLI. Aquí no se levanta ningún servidor:
se guardan y recuperan 500 trabajos con todos sus campos llenos y se comprueba,
campo por campo, que al cerrar y volver a abrir la base no se perdió ni cambió nada.
"""
import os
import tempfile
import time
import unittest

from jobrunner.executor import JobManager
from jobrunner.jobs import CANCELED, FAILED, QUEUED, RUNNING, SUCCEEDED, Job
from jobrunner.store import Store

TOTAL = 500
ESTADOS = (SUCCEEDED, FAILED, CANCELED, QUEUED, RUNNING)


def trabajo_completo(i):
    """Un trabajo con TODOS los campos de Job llenos, para que ninguno pueda perderse en silencio."""
    job = Job(id="id-%04d" % i, argv=["prog-%d" % i, "--opcion", "valor con espacios y acentos: áé"],
              created_at="2026-11-01T10:%02d:%02d.%06d+00:00" % (i // 3600 % 60, i // 60 % 60, i))
    job.state = ESTADOS[i % len(ESTADOS)]
    job.request_id = "req-%04d" % i
    job.pid = 1000 + i
    job.stdout_path = "data/id-%04d.out" % i
    job.stderr_path = "data/id-%04d.err" % i
    if job.state != QUEUED:
        job.started_at = "2026-11-01T11:00:00.%06d+00:00" % i
    if job.state in (SUCCEEDED, FAILED, CANCELED):
        job.finished_at = "2026-11-01T12:00:00.%06d+00:00" % i
        job.exit_code = {SUCCEEDED: 0, FAILED: 1 + i % 200, CANCELED: -15}[job.state]
    if job.state == FAILED:
        job.error = "falló %d" % i
    return job


class QuinientosRegistrosEnElAlmacenTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta = os.path.join(self._tmp.name, "data", "jobrunner.db")

    def test_el_almacen_guarda_y_recupera_500_trabajos_sin_perder_campos(self):
        originales = [trabajo_completo(i) for i in range(TOTAL)]
        store = Store(self.ruta)
        for job in originales:
            store.save(job)
        store.close()

        reabierto = Store(self.ruta)   # equivale a reiniciar el servidor
        self.addCleanup(reabierto.close)
        recuperados = reabierto.list()
        self.assertEqual(len(recuperados), TOTAL)
        self.assertEqual([j.to_dict() for j in recuperados], [j.to_dict() for j in originales])

    def test_cada_estado_conserva_su_cantidad_tras_reabrir(self):
        store = Store(self.ruta)
        for i in range(TOTAL):
            store.save(trabajo_completo(i))
        store.close()
        reabierto = Store(self.ruta)
        self.addCleanup(reabierto.close)
        for estado in ESTADOS:
            esperados = len([i for i in range(TOTAL) if ESTADOS[i % len(ESTADOS)] == estado])
            self.assertEqual(len(reabierto.list(state=estado)), esperados, estado)

    def test_actualizar_500_veces_no_duplica_ni_pierde_registros(self):
        store = Store(self.ruta)
        jobs = [trabajo_completo(i) for i in range(TOTAL)]
        for job in jobs:
            store.save(job)
        for job in jobs:   # segunda escritura del mismo id: actualiza, no duplica
            job.error = "revisado " + job.id
            store.save(job)
        store.close()
        reabierto = Store(self.ruta)
        self.addCleanup(reabierto.close)
        self.assertEqual(len(reabierto.list()), TOTAL)
        self.assertTrue(all(j.error == "revisado " + j.id for j in reabierto.list()))


class QuinientosTrabajosPorElGestorTest(unittest.TestCase):
    def test_500_trabajos_enviados_al_gestor_sobreviven_al_reinicio(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "jobrunner.db")
            store = Store(ruta)
            manager = JobManager(data_dir=tmp, store=store, max_jobs=50, queue_size=TOTAL)
            for i in range(TOTAL):
                argv = ["sh", "-c", "exit 3"] if i % 10 == 0 else ["echo", "trabajo-%d" % i]
                manager.submit(argv, request_id="rnf06-%04d" % i)
            limite = time.monotonic() + 60
            while time.monotonic() < limite:
                manager.tick()
                if all(j["state"] in ("SUCCEEDED", "FAILED", "CANCELED") for j in manager.list()):
                    break
                time.sleep(0.05)
            antes = manager.list()
            self.assertEqual(len(antes), TOTAL)
            self.assertTrue(all(j["state"] in ("SUCCEEDED", "FAILED") for j in antes), "no terminaron todos")
            store.close()

            store2 = Store(ruta)
            self.addCleanup(store2.close)
            manager2 = JobManager(data_dir=tmp, store=store2, max_jobs=50, queue_size=TOTAL)
            manager2.recuperar()
            despues = manager2.list()
            self.assertEqual(len(despues), TOTAL)
            self.assertEqual(despues, antes)   # ningún campo cambió
            fallidos = [j for j in despues if j["state"] == "FAILED"]
            self.assertEqual(len(fallidos), TOTAL // 10)
            self.assertTrue(all(j["exit_code"] == 3 for j in fallidos))
            self.assertEqual(len({j["id"] for j in despues}), TOTAL)
            self.assertEqual(len({j["request_id"] for j in despues}), TOTAL)


if __name__ == "__main__":
    unittest.main()
