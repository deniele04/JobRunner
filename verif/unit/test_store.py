"""Pruebas unitarias de la persistencia en SQLite (ADR-0002, TC-007).

Cubre: guardar y leer, actualizar sin duplicar, listar por estado y orden,
unicidad de request_id, estado invalido y que los datos sobreviven a cerrar
y volver a abrir la base (reinicio del servidor).
"""
import os
import sqlite3
import tempfile
import unittest

from jobrunner.jobs import CANCELED, FAILED, QUEUED, RUNNING, SUCCEEDED, Job
from jobrunner.store import Store


def nuevo(argv=("sleep", "1"), **campos):
    job = Job.new(list(argv))
    for nombre, valor in campos.items():
        setattr(job, nombre, valor)
    return job


class StoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self._tmp.name, "data", "jobrunner.db")
        self.store = Store(self.ruta)

    def tearDown(self):
        self.store.close()
        self._tmp.cleanup()

    def test_guarda_y_lee_el_mismo_trabajo(self):
        job = nuevo(request_id="req-1", stdout_path="a.out", stderr_path="a.err")
        self.store.save(job)
        self.assertEqual(self.store.get(job.id).to_dict(), job.to_dict())

    def test_get_de_id_inexistente_devuelve_none(self):
        self.assertIsNone(self.store.get("no-existe"))

    def test_guardar_dos_veces_actualiza_sin_duplicar(self):
        job = nuevo()
        self.store.save(job)
        job.state = RUNNING
        job.pid = 4321
        self.store.save(job)
        self.assertEqual(len(self.store.list()), 1)
        guardado = self.store.get(job.id)
        self.assertEqual(guardado.state, RUNNING)
        self.assertEqual(guardado.pid, 4321)

    def test_argv_con_caracteres_especiales(self):
        job = nuevo(argv=("echo", "hola mundo", "acentos: aeiou", 'comilla"'))
        self.store.save(job)
        self.assertEqual(self.store.get(job.id).argv, job.argv)

    def test_list_filtra_por_estado_y_conserva_el_orden(self):
        a = nuevo(created_at="2026-10-27T10:00:00+00:00")
        b = nuevo(created_at="2026-10-27T10:00:01+00:00", state=RUNNING)
        c = nuevo(created_at="2026-10-27T10:00:02+00:00")
        for job in (c, a, b):
            self.store.save(job)
        self.assertEqual([j.id for j in self.store.list()], [a.id, b.id, c.id])
        self.assertEqual([j.id for j in self.store.list(QUEUED)], [a.id, c.id])
        self.assertEqual([j.id for j in self.store.list(RUNNING)], [b.id])
        self.assertEqual(self.store.list(SUCCEEDED), [])

    def test_busca_por_request_id(self):
        job = nuevo(request_id="req-7")
        self.store.save(job)
        self.assertEqual(self.store.get_by_request_id("req-7").id, job.id)
        self.assertIsNone(self.store.get_by_request_id("otro"))
        self.assertIsNone(self.store.get_by_request_id(None))

    def test_request_id_repetido_es_rechazado_y_no_cambia_nada(self):
        original = nuevo(request_id="req-dup")
        self.store.save(original)
        otro = nuevo(request_id="req-dup")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.save(otro)
        self.assertEqual(len(self.store.list()), 1)
        self.assertIsNone(self.store.get(otro.id))
        self.assertEqual(self.store.get_by_request_id("req-dup").id, original.id)

    def test_trabajos_sin_request_id_no_chocan(self):
        for _ in range(3):
            self.store.save(nuevo())
        self.assertEqual(len(self.store.list()), 3)

    def test_estado_invalido_es_rechazado(self):
        job = nuevo(state="INVENTADO")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.save(job)
        self.assertEqual(self.store.list(), [])

    def test_los_datos_sobreviven_a_cerrar_y_reabrir(self):
        en_cola = nuevo(request_id="req-cola")
        corriendo = nuevo(state=RUNNING, pid=999)
        fallido = nuevo(state=FAILED, exit_code=1, error="fallo")
        cancelado = nuevo(state=CANCELED, exit_code=-15)
        esperado = {}
        for job in (en_cola, corriendo, fallido, cancelado):
            self.store.save(job)
            esperado[job.id] = job.to_dict()
        self.store.close()

        self.store = Store(self.ruta)
        recuperado = {j.id: j.to_dict() for j in self.store.list()}
        self.assertEqual(recuperado, esperado)


if __name__ == "__main__":
    unittest.main()