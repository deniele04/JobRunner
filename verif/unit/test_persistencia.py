"""Persistencia, recuperacion al arrancar y solicitudes duplicadas (ADR-0002, ADR-0005).

Cubre: cada cambio de estado queda guardado, el reinicio no pierde el historial
(TC-007), los trabajos RUNNING interrumpidos pasan a FAILED y su proceso se
termina, los QUEUED se reanudan y un request_id repetido devuelve el mismo
trabajo sin crear otro (tambien despues de reiniciar).
"""
import os
import tempfile
import threading
import time
import unittest

from jobrunner.executor import JobManager
from jobrunner.jobs import CANCELED, FAILED, FINAL_STATES, QUEUED, RUNNING, SUCCEEDED, Job
from jobrunner.store import Store


class PersistenciaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.ruta_db = os.path.join(self.dir, "jobrunner.db")
        self.abiertos = []
        self.mgr = self.nuevo_manager()

    def tearDown(self):
        for job in self.mgr.list(state=RUNNING):
            try:
                self.mgr.cancel(job["id"])
            except (KeyError, ValueError):
                pass
        for store in self.abiertos:
            store.close()
        self._tmp.cleanup()

    def nuevo_manager(self):
        store = Store(self.ruta_db)
        self.abiertos.append(store)
        return JobManager(data_dir=self.dir, store=store)

    def leer_db(self, job_id):
        store = Store(self.ruta_db)
        try:
            return store.get(job_id)
        finally:
            store.close()

    def esperar_final(self, mgr, job_id, timeout=5.0):
        limite = time.monotonic() + timeout
        while time.monotonic() < limite:
            mgr.poll()
            job = mgr.get(job_id)
            if job["state"] in FINAL_STATES:
                return job
            time.sleep(0.05)
        self.fail("el trabajo no termino a tiempo")

    def grupo_vivo(self, pid):
        try:
            os.killpg(pid, 0)
        except ProcessLookupError:
            return False
        return True

    def test_submit_guarda_el_trabajo_en_ejecucion_con_su_pid(self):
        job = self.mgr.submit(["sleep", "30"])
        guardado = self.leer_db(job["id"])
        self.assertEqual(guardado.state, RUNNING)
        self.assertEqual(guardado.pid, job["pid"])
        self.assertEqual(guardado.argv, ["sleep", "30"])

    def test_el_estado_final_queda_guardado(self):
        job = self.mgr.submit(["true"])
        self.esperar_final(self.mgr, job["id"])
        guardado = self.leer_db(job["id"])
        self.assertEqual(guardado.state, SUCCEEDED)
        self.assertEqual(guardado.exit_code, 0)
        self.assertIsNotNone(guardado.finished_at)

    def test_la_cancelacion_queda_guardada(self):
        job = self.mgr.submit(["sleep", "30"])
        self.mgr.cancel(job["id"])
        self.esperar_final(self.mgr, job["id"])
        self.assertEqual(self.leer_db(job["id"]).state, CANCELED)

    def test_reinicio_conserva_el_historial_de_trabajos_terminados(self):
        ok = self.mgr.submit(["true"])
        mal = self.mgr.submit(["false"])
        self.esperar_final(self.mgr, ok["id"])
        self.esperar_final(self.mgr, mal["id"])
        antes = {j["id"]: j for j in self.mgr.list()}

        nuevo = self.nuevo_manager()
        nuevo.recuperar()
        despues = {j["id"]: j for j in nuevo.list()}
        self.assertEqual(despues, antes)
        self.assertEqual(nuevo.get(ok["id"])["state"], SUCCEEDED)
        self.assertEqual(nuevo.get(mal["id"])["state"], FAILED)

    def test_recuperacion_marca_running_como_failed_y_termina_su_proceso(self):
        job = self.mgr.submit(["sleep", "60"])
        pid = job["pid"]
        proc = self.mgr._procs[job["id"]]
        # Simula que init recoge al proceso huerfano cuando muere.
        threading.Thread(target=proc.wait, daemon=True).start()
        self.assertTrue(self.grupo_vivo(pid))

        nuevo = self.nuevo_manager()
        nuevo.recuperar()

        recuperado = nuevo.get(job["id"])
        self.assertEqual(recuperado["state"], FAILED)
        self.assertEqual(recuperado["error"], "interrumpido por reinicio")
        self.assertIsNotNone(recuperado["finished_at"])
        self.assertFalse(self.grupo_vivo(pid))
        self.assertEqual(self.leer_db(job["id"]).state, FAILED)

    def test_recuperar_dos_veces_da_el_mismo_resultado(self):
        job = self.mgr.submit(["sleep", "60"])
        proc = self.mgr._procs[job["id"]]
        threading.Thread(target=proc.wait, daemon=True).start()

        primero = self.nuevo_manager()
        primero.recuperar()
        estado_1 = primero.get(job["id"])
        segundo = self.nuevo_manager()
        segundo.recuperar()
        self.assertEqual(segundo.get(job["id"]), estado_1)

    def test_recuperacion_reanuda_los_trabajos_en_cola(self):
        en_cola = Job.new(["true"])
        en_cola.state = QUEUED
        en_cola.stdout_path = os.path.join(self.dir, en_cola.id + ".out")
        en_cola.stderr_path = os.path.join(self.dir, en_cola.id + ".err")
        self.abiertos[0].save(en_cola)

        nuevo = self.nuevo_manager()
        nuevo.recuperar()
        final = self.esperar_final(nuevo, en_cola.id)
        self.assertEqual(final["state"], SUCCEEDED)

    def test_request_id_repetido_devuelve_el_mismo_trabajo(self):
        primero = self.mgr.submit(["sleep", "30"], request_id="req-1")
        segundo = self.mgr.submit(["sleep", "30"], request_id="req-1")
        self.assertEqual(primero["id"], segundo["id"])
        self.assertEqual(len(self.mgr.list()), 1)
        self.assertEqual(len(self.mgr._procs), 1)

    def test_request_id_repetido_despues_de_reiniciar(self):
        primero = self.mgr.submit(["true"], request_id="req-2")
        self.esperar_final(self.mgr, primero["id"])

        nuevo = self.nuevo_manager()
        nuevo.recuperar()
        repetido = nuevo.submit(["true"], request_id="req-2")
        self.assertEqual(repetido["id"], primero["id"])
        self.assertEqual(len(nuevo.list()), 1)

    def test_request_id_invalido_es_rechazado(self):
        for invalido in ("", 5, ["x"]):
            with self.assertRaises(ValueError):
                self.mgr.submit(["true"], request_id=invalido)
        self.assertEqual(self.mgr.list(), [])

    def test_sin_request_id_cada_envio_es_un_trabajo_nuevo(self):
        a = self.mgr.submit(["true"])
        b = self.mgr.submit(["true"])
        self.assertNotEqual(a["id"], b["id"])


if __name__ == "__main__":
    unittest.main()
