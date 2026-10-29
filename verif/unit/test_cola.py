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

from jobrunner import bitacora
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


class OrdenFifoTest(ColaBase):
    def test_al_terminar_uno_tick_arranca_el_que_estaba_en_cola(self):
        self.nuevo(max_jobs=1, queue_size=3)
        a = self.mgr.submit(["sleep", "0.3"])["id"]
        b = self.mgr.submit(["sleep", "30"])["id"]
        c = self.mgr.submit(["sleep", "30"])["id"]
        self.assertTrue(self.esperar(lambda: self.mgr.get(a)["state"] == SUCCEEDED))
        self.assertEqual(self.mgr.get(b)["state"], RUNNING)    # el primero en llegar
        self.assertEqual(self.mgr.get(c)["state"], QUEUED)
        self.assertIsNotNone(self.mgr.get(b)["started_at"])    # se marca al salir de la cola

    def test_sin_tick_la_cola_no_avanza_sola(self):
        self.nuevo(max_jobs=1, queue_size=3)
        self.mgr.submit(["sleep", "0.2"])
        b = self.mgr.submit(["sleep", "30"])["id"]
        time.sleep(0.5)
        self.assertEqual(self.mgr.get(b)["state"], QUEUED)
        self.mgr.tick()
        self.assertEqual(self.mgr.get(b)["state"], RUNNING)

    def test_la_cola_se_vacia_sola_con_tick(self):
        self.nuevo(max_jobs=2, queue_size=4)
        for _ in range(6):
            self.mgr.submit(["sleep", "0.2"])
        self.assertTrue(self.esperar(
            lambda: all(s == SUCCEEDED for s in self.estados()), timeout=15))

    def test_nunca_hay_mas_de_max_jobs_en_ejecucion(self):
        self.nuevo(max_jobs=2, queue_size=6)
        for _ in range(8):
            self.mgr.submit(["sleep", "0.2"])
        limite = time.monotonic() + 15
        while time.monotonic() < limite:
            self.mgr.tick()
            self.assertLessEqual(self.estados().count(RUNNING), 2)
            if all(s == SUCCEEDED for s in self.estados()):
                break
            time.sleep(0.05)
        self.assertTrue(all(s == SUCCEEDED for s in self.estados()))

    def test_un_submit_nuevo_no_se_salta_a_los_que_esperan(self):
        self.nuevo(max_jobs=1, queue_size=3)
        self.mgr.submit(["sleep", "0.2"])
        esperando = self.mgr.submit(["sleep", "30"])["id"]
        time.sleep(0.4)
        self.mgr.poll()   # el primero termino y libero su lugar, pero la cola no avanzo
        nuevo = self.mgr.submit(["sleep", "30"])["id"]
        self.assertEqual(self.mgr.get(esperando)["state"], RUNNING)
        self.assertEqual(self.mgr.get(nuevo)["state"], QUEUED)


class CancelarEnColaTest(ColaBase):
    def test_cancelar_en_cola_pasa_a_canceled_y_nunca_arranca(self):  # TC-005
        self.nuevo(max_jobs=1, queue_size=2)
        self.mgr.submit(["sleep", "30"])
        b = self.mgr.submit(["sleep", "30"])["id"]
        cancelado = self.mgr.cancel(b)
        self.assertEqual(cancelado["state"], CANCELED)
        self.assertIsNone(cancelado["started_at"])
        self.assertIsNotNone(cancelado["finished_at"])
        self.assertNotIn(b, self.mgr._cola)
        self.mgr.tick()
        self.assertEqual(self.mgr.get(b)["state"], CANCELED)
        self.assertNotIn(b, self.mgr._procs)

    def test_cancelar_en_cola_libera_su_lugar(self):
        self.nuevo(max_jobs=1, queue_size=1)
        self.mgr.submit(["sleep", "30"])
        b = self.mgr.submit(["sleep", "30"])["id"]
        with self.assertRaises(ColaLlena):
            self.mgr.submit(["sleep", "30"])
        self.mgr.cancel(b)
        self.assertEqual(self.mgr.submit(["sleep", "30"])["state"], QUEUED)

    def test_el_cancelado_en_cola_no_se_salta_a_los_demas(self):
        self.nuevo(max_jobs=1, queue_size=3)
        a = self.mgr.submit(["sleep", "0.3"])["id"]
        b = self.mgr.submit(["sleep", "30"])["id"]
        c = self.mgr.submit(["sleep", "30"])["id"]
        self.mgr.cancel(b)
        self.assertTrue(self.esperar(lambda: self.mgr.get(a)["state"] == SUCCEEDED))
        self.assertEqual(self.mgr.get(b)["state"], CANCELED)
        self.assertEqual(self.mgr.get(c)["state"], RUNNING)

    def test_la_cancelacion_en_cola_queda_guardada(self):
        ruta_db = os.path.join(self.dir, "jobrunner.db")
        store = Store(ruta_db)
        try:
            self.mgr = JobManager(data_dir=self.dir, store=store, max_jobs=1, queue_size=2)
            self.mgr.submit(["sleep", "30"])
            b = self.mgr.submit(["sleep", "30"])["id"]
            self.assertEqual(store.get(b).state, QUEUED)   # guardado al encolar
            self.mgr.cancel(b)
            self.assertEqual(store.get(b).state, CANCELED)
            self.limpiar(self.mgr)
        finally:
            self.mgr = None
            store.close()


class RecuperacionColaTest(ColaBase):
    def _guardar_queued(self, store, cantidad):
        ids = []
        for _ in range(cantidad):
            job = Job.new(["sleep", "30"])
            job.stdout_path = os.path.join(self.dir, job.id + ".out")
            job.stderr_path = os.path.join(self.dir, job.id + ".err")
            store.save(job)
            ids.append(job.id)
        return ids

    def test_los_queued_reanudan_respetando_max_jobs_y_el_orden(self):
        store = Store(os.path.join(self.dir, "jobrunner.db"))
        try:
            ids = self._guardar_queued(store, 4)
            self.mgr = JobManager(data_dir=self.dir, store=store, max_jobs=2, queue_size=5)
            self.mgr.recuperar()
            self.assertEqual([self.mgr.get(i)["state"] for i in ids],
                             [RUNNING, RUNNING, QUEUED, QUEUED])
            self.limpiar(self.mgr)
        finally:
            self.mgr = None
            store.close()

    def test_los_queued_recuperados_siguen_avanzando_con_tick(self):
        store = Store(os.path.join(self.dir, "jobrunner.db"))
        try:
            ids = self._guardar_queued(store, 3)
            self.mgr = JobManager(data_dir=self.dir, store=store, max_jobs=1, queue_size=5)
            self.mgr.recuperar()
            self.mgr.cancel(ids[0])
            self.assertTrue(self.esperar(lambda: self.mgr.get(ids[1])["state"] == RUNNING))
            self.assertEqual(self.mgr.get(ids[2])["state"], QUEUED)
            self.limpiar(self.mgr)
        finally:
            self.mgr = None
            store.close()


class CancelarSinBloqueoTest(ColaBase):
    def test_cancel_responde_de_inmediato_y_el_trabajo_termina_en_canceled(self):
        self.nuevo()
        job = self.mgr.submit(["sleep", "30"])["id"]
        inicio = time.monotonic()
        respuesta = self.mgr.cancel(job)
        self.assertLess(time.monotonic() - inicio, 1.0)
        self.assertEqual(respuesta["state"], RUNNING)      # aun no se recoge el proceso
        self.assertTrue(self.esperar(lambda: self.mgr.get(job)["state"] == CANCELED, timeout=3))
        final = self.mgr.get(job)
        self.assertEqual(final["exit_code"], -15)
        self.assertIsNotNone(final["finished_at"])
        self.assertNotIn(job, self.mgr._cancelando)

    def test_cancelar_libera_el_lugar_para_el_siguiente_de_la_cola(self):
        self.nuevo(max_jobs=1, queue_size=2)
        a = self.mgr.submit(["sleep", "30"])["id"]
        b = self.mgr.submit(["sleep", "30"])["id"]
        self.mgr.cancel(a)
        self.assertTrue(self.esperar(lambda: self.mgr.get(b)["state"] == RUNNING, timeout=3))
        self.assertEqual(self.mgr.get(a)["state"], CANCELED)

    def test_un_trabajo_que_termino_solo_no_se_marca_canceled(self):
        self.nuevo()
        job = self.mgr.submit(["true"])["id"]
        time.sleep(0.3)   # termino, pero nadie lo ha recogido
        with self.assertRaises(ValueError):
            self.mgr.cancel(job)
        self.assertEqual(self.mgr.get(job)["state"], SUCCEEDED)


class DobleCancelacionTest(ColaBase):
    def test_la_segunda_cancelacion_no_cambia_nada(self):            # TC-017
        self.nuevo()
        job = self.mgr.submit(["sleep", "30"])["id"]
        primera = self.mgr.cancel(job)
        limite = self.mgr._cancelando[job]
        segunda = self.mgr.cancel(job)
        self.assertEqual(primera["state"], RUNNING)
        self.assertEqual(segunda, primera)                          # mismo estado real
        self.assertEqual(self.mgr._cancelando[job], limite)         # no se reinicia el plazo
        self.assertTrue(self.esperar(lambda: self.mgr.get(job)["state"] == CANCELED, timeout=3))

    def test_dos_cancelaciones_seguidas_dejan_un_solo_estado_final(self):   # TC-017
        self.nuevo()
        job = self.mgr.submit(["sleep", "30"])["id"]
        self.mgr.cancel(job)
        self.mgr.cancel(job)
        self.assertTrue(self.esperar(lambda: self.mgr.get(job)["state"] == CANCELED, timeout=3))
        self.assertEqual(self.mgr.get(job)["exit_code"], -15)

    def test_cancelar_un_trabajo_ya_cancelado_da_error_y_no_lo_cambia(self):  # TC-017
        self.nuevo()
        job = self.mgr.submit(["sleep", "30"])["id"]
        self.mgr.cancel(job)
        self.assertTrue(self.esperar(lambda: self.mgr.get(job)["state"] == CANCELED, timeout=3))
        antes = self.mgr.get(job)
        with self.assertRaises(ValueError):
            self.mgr.cancel(job)
        self.assertEqual(self.mgr.get(job), antes)

    def test_cancelar_un_id_inexistente_no_afecta_a_los_demas(self):          # TC-017
        self.nuevo()
        job = self.mgr.submit(["sleep", "30"])["id"]
        with self.assertRaises(KeyError):
            self.mgr.cancel("no-existe")
        self.assertEqual(self.mgr.get(job)["state"], RUNNING)


class EscalamientoTest(ColaBase):
    def test_trabajo_que_ignora_sigterm_termina_con_sigkill(self):           # TC-021
        ruta = bitacora.configurar(self.dir)
        self.addCleanup(bitacora.cerrar)
        self.nuevo()
        job = self.mgr.submit(["sh", "-c", 'trap "" TERM; sleep 60'])["id"]
        time.sleep(0.3)   # que el shell instale el trap

        inicio = time.monotonic()
        respuesta = self.mgr.cancel(job)
        self.assertLess(time.monotonic() - inicio, 1.0)              # no bloquea
        self.assertEqual(respuesta["state"], RUNNING)

        time.sleep(1.0)
        self.mgr.tick()
        self.assertEqual(self.mgr.get(job)["state"], RUNNING)        # antes de los 5 s sigue vivo

        self.assertTrue(self.esperar(lambda: self.mgr.get(job)["state"] == CANCELED, timeout=6))
        self.assertLessEqual(time.monotonic() - inicio, 6.5)
        self.assertEqual(self.mgr.get(job)["exit_code"], -9)

        eventos = [l.split()[2] for l in ruta.read_text(encoding="utf-8").splitlines()
                   if "job=" + job in l]
        self.assertEqual(eventos, ["recibido", "iniciado", "cancelacion_solicitada",
                                   "escalamiento", "cancelado"])

    def test_el_escalamiento_no_bloquea_a_los_demas_trabajos(self):          # TC-021
        self.nuevo(max_jobs=2, queue_size=2)
        terco = self.mgr.submit(["sh", "-c", 'trap "" TERM; sleep 60'])["id"]
        otro = self.mgr.submit(["sleep", "30"])["id"]
        time.sleep(0.3)
        self.mgr.cancel(terco)
        inicio = time.monotonic()
        self.assertEqual(self.mgr.get(otro)["state"], RUNNING)
        self.mgr.cancel(otro)                                        # responde mientras el otro escala
        self.assertLess(time.monotonic() - inicio, 1.0)
        self.assertTrue(self.esperar(lambda: self.mgr.get(otro)["state"] == CANCELED, timeout=3))
        self.assertEqual(self.mgr.get(terco)["state"], RUNNING)      # el terco aun espera su SIGKILL

    def test_un_trabajo_que_obedece_sigterm_no_escala(self):
        ruta = bitacora.configurar(self.dir)
        self.addCleanup(bitacora.cerrar)
        self.nuevo()
        job = self.mgr.submit(["sleep", "30"])["id"]
        self.mgr.cancel(job)
        self.assertTrue(self.esperar(lambda: self.mgr.get(job)["state"] == CANCELED, timeout=3))
        self.assertNotIn("escalamiento", ruta.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
