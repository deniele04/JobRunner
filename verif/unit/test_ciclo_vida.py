"""Pruebas unitarias del ciclo de vida de un job (QUEUED -> RUNNING -> estado final).

Cubre: éxito, fallo por código de salida, fallo al lanzar el comando, entrada
inválida, transiciones no permitidas y cancelación. Los errores no deben tumbar
el JobManager: después de cada fallo el gestor sigue aceptando trabajos.

Ejecutar con ./scripts/test.sh (usa unittest de la biblioteca estándar).
"""
import os
import tempfile
import time
import unittest

from jobrunner.executor import JobManager
from jobrunner.jobs import (
    CANCELED, FAILED, FINAL_STATES, QUEUED, RUNNING, SUCCEEDED, Job,
)


class CicloDeVidaTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mgr = JobManager(data_dir=self._tmp.name)

    def tearDown(self):
        # No dejar procesos vivos si una prueba falla a medias.
        for job in self.mgr.list(state=RUNNING):
            try:
                self.mgr.cancel(job["id"])
            except (KeyError, ValueError):
                pass
        self._tmp.cleanup()

    def esperar_estado_final(self, job_id, timeout=5.0):
        limite = time.monotonic() + timeout
        while time.monotonic() < limite:
            self.mgr.poll()
            job = self.mgr.get(job_id)
            if job["state"] in FINAL_STATES:
                return job
            time.sleep(0.05)
        self.fail(f"El trabajo {job_id} no llegó a un estado final en {timeout} s")

    # --- éxito ---------------------------------------------------------

    def test_exito_termina_en_succeeded_con_codigo_0(self):
        job = self.mgr.submit(["true"])
        self.assertEqual(job["state"], RUNNING)
        self.assertIsNotNone(job["started_at"])

        final = self.esperar_estado_final(job["id"])
        self.assertEqual(final["state"], SUCCEEDED)
        self.assertEqual(final["exit_code"], 0)
        self.assertIsNotNone(final["finished_at"])

    def test_trabajo_corre_en_proceso_separado(self):
        job = self.mgr.submit(["sleep", "30"])
        proc = self.mgr._procs[job["id"]]
        # Proceso distinto al del gestor y en su propio grupo de procesos.
        self.assertNotEqual(proc.pid, os.getpid())
        self.assertEqual(os.getpgid(proc.pid), proc.pid)
        self.assertNotEqual(os.getpgid(proc.pid), os.getpgid(0))

    # --- fallos controlados ---------------------------------------------

    def test_codigo_de_salida_distinto_de_cero_termina_en_failed(self):
        job = self.mgr.submit(["sh", "-c", "exit 3"])
        final = self.esperar_estado_final(job["id"])
        self.assertEqual(final["state"], FAILED)
        self.assertEqual(final["exit_code"], 3)

    def test_stderr_del_trabajo_se_guarda_en_archivo(self):
        job = self.mgr.submit(["sh", "-c", "echo fallo-simulado >&2; exit 1"])
        final = self.esperar_estado_final(job["id"])
        self.assertEqual(final["state"], FAILED)
        with open(final["stderr_path"], encoding="utf-8") as f:
            self.assertIn("fallo-simulado", f.read())

    def test_comando_inexistente_falla_sin_tumbar_el_gestor(self):
        job = self.mgr.submit(["comando-que-no-existe-jobrunner"])
        self.assertEqual(job["state"], FAILED)
        self.assertIsNone(job["exit_code"])
        self.assertIn("No se pudo ejecutar", job["error"])
        self.assertIsNotNone(job["finished_at"])

        # El gestor sigue operativo después del error.
        siguiente = self.mgr.submit(["true"])
        final = self.esperar_estado_final(siguiente["id"])
        self.assertEqual(final["state"], SUCCEEDED)

    def test_argv_vacio_se_rechaza_y_no_registra_trabajo(self):
        with self.assertRaises(ValueError):
            self.mgr.submit([])
        self.assertEqual(self.mgr.list(), [])

    # --- transiciones ----------------------------------------------------

    def test_transiciones_validas(self):
        job = Job.new(["true"])
        self.assertEqual(job.state, QUEUED)
        job.transition(RUNNING)
        job.transition(SUCCEEDED)
        self.assertEqual(job.state, SUCCEEDED)

    def test_transiciones_invalidas_lanzan_error(self):
        casos = [
            (QUEUED, SUCCEEDED),
            (QUEUED, FAILED),
            (SUCCEEDED, RUNNING),
            (FAILED, RUNNING),
            (CANCELED, RUNNING),
        ]
        for origen, destino in casos:
            with self.subTest(origen=origen, destino=destino):
                job = Job.new(["true"])
                job.state = origen
                with self.assertRaises(ValueError):
                    job.transition(destino)
                self.assertEqual(job.state, origen)

    # --- cancelación -----------------------------------------------------

    def test_cancelar_trabajo_en_ejecucion(self):
        job = self.mgr.submit(["sleep", "30"])
        cancelado = self.mgr.cancel(job["id"])
        self.assertEqual(cancelado["state"], CANCELED)
        self.assertIsNotNone(cancelado["finished_at"])
        self.assertNotIn(job["id"], self.mgr._procs)

        with self.assertRaises(ValueError):
            self.mgr.cancel(job["id"])

    def test_cancelar_trabajo_inexistente(self):
        with self.assertRaises(KeyError):
            self.mgr.cancel("zzzz")

    def test_trabajo_cancelado_no_cambia_de_estado_en_poll(self):
        job = self.mgr.submit(["sleep", "30"])
        self.mgr.cancel(job["id"])
        self.mgr.poll()
        self.assertEqual(self.mgr.get(job["id"])["state"], CANCELED)


if __name__ == "__main__":
    unittest.main()
