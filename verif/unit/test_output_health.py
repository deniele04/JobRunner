"""JobManager.output y JobManager.health, y los comandos output y health de handle_request (U2).

Sin servidor ni red: se usa el gestor de trabajos directamente. Cubre RF-18, RF-24 y la
forma de las respuestas documentada en la guia del protocolo (seccion 1.8).
"""
import os
import sys
import tempfile
import time
import unittest

from jobrunner import __version__
from jobrunner.executor import MAX_SALIDA, JobManager
from jobrunner.jobs import CANCELED, FAILED, QUEUED, RUNNING, SUCCEEDED
from jobrunner.server import handle_request
from jobrunner.store import Store


def esperar_final(manager, job_id, limite=15.0):
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        manager.tick()
        if manager.get(job_id)["state"] in (SUCCEEDED, FAILED, CANCELED):
            return manager.get(job_id)
        time.sleep(0.05)
    raise AssertionError("el trabajo no termino")


class Base(unittest.TestCase):
    max_jobs = 3
    queue_size = 10

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = Store(os.path.join(self._tmp.name, "jobrunner.db"))
        self.mgr = JobManager(data_dir=self._tmp.name, store=self.store,
                              max_jobs=self.max_jobs, queue_size=self.queue_size)
        self.addCleanup(self._limpiar)

    def _limpiar(self):
        for job in self.mgr.list():
            try:
                self.mgr.cancel(job["id"])
            except (KeyError, ValueError):
                pass
        fin = time.monotonic() + 10
        while time.monotonic() < fin and self.mgr.list(state=RUNNING):
            self.mgr.tick()
            time.sleep(0.05)
        try:
            self.store.close()
        except Exception:
            pass
        self._tmp.cleanup()

    def correr(self, *argv):
        job = self.mgr.submit(list(argv))
        return esperar_final(self.mgr, job["id"])

    def python(self, codigo):
        return self.correr(sys.executable, "-c", codigo)


class OutputTest(Base):
    def test_devuelve_id_stream_data_y_truncated(self):
        job = self.correr("echo", "hola")
        r = self.mgr.output(job["id"])
        self.assertEqual(r, {"id": job["id"], "stream": "stdout", "data": "hola\n", "truncated": False})

    def test_stderr_es_otro_archivo(self):
        job = self.python("import sys; print('normal'); print('fallo', file=sys.stderr)")
        self.assertEqual(self.mgr.output(job["id"], "stdout")["data"], "normal\n")
        r = self.mgr.output(job["id"], "stderr")
        self.assertEqual((r["stream"], r["data"]), ("stderr", "fallo\n"))

    def test_sin_salida_devuelve_data_vacio(self):
        job = self.correr("true")
        self.assertEqual(self.mgr.output(job["id"])["data"], "")
        self.assertFalse(self.mgr.output(job["id"])["truncated"])

    def test_devuelve_el_final_y_marca_truncated(self):
        job = self.python("print('A' * 100); print('FIN')")   # 'A'*100 + '\n' + 'FIN\n'
        r = self.mgr.output(job["id"], "stdout", 10)
        self.assertTrue(r["truncated"])
        self.assertEqual(r["data"], "AAAAA\nFIN\n")   # los ultimos 10 bytes
        self.assertEqual(len(r["data"].encode()), 10)

    def test_si_cabe_completa_no_esta_truncada(self):
        job = self.python("print('A' * 9)")   # 10 bytes con el salto de linea
        self.assertFalse(self.mgr.output(job["id"], "stdout", 10)["truncated"])
        self.assertTrue(self.mgr.output(job["id"], "stdout", 9)["truncated"])

    def test_por_defecto_el_limite_es_64_kib(self):
        self.assertEqual(MAX_SALIDA, 65536)
        job = self.python("import sys; sys.stdout.write('x' * 100000)")
        r = self.mgr.output(job["id"])
        self.assertTrue(r["truncated"])
        self.assertEqual(len(r["data"]), 65536)

    def test_un_corte_a_la_mitad_de_un_caracter_no_deja_basura_al_inicio(self):
        job = self.python("import sys; sys.stdout.buffer.write('ñ'.encode() * 10)")   # 20 bytes
        r = self.mgr.output(job["id"], "stdout", 5)   # empezaria en medio de una ñ
        self.assertTrue(r["truncated"])
        self.assertNotIn("�", r["data"])
        self.assertEqual(r["data"], "ñ" * 2)

    def test_los_bytes_que_no_son_utf8_se_sustituyen(self):
        job = self.python("import sys; sys.stdout.buffer.write(bytes([0xff, 0x41]))")
        self.assertEqual(self.mgr.output(job["id"])["data"], "�A")

    def test_trabajo_en_cola_no_tiene_salida_todavia(self):
        for _ in range(self.max_jobs):
            self.mgr.submit(["sleep", "30"])
        en_cola = self.mgr.submit(["sleep", "30"])
        self.assertEqual(en_cola["state"], QUEUED)
        self.assertEqual(self.mgr.output(en_cola["id"]),
                         {"id": en_cola["id"], "stream": "stdout", "data": "", "truncated": False})

    def test_trabajo_en_ejecucion_devuelve_lo_que_lleva(self):
        job = self.mgr.submit([sys.executable, "-u", "-c", "print('parcial'); import time; time.sleep(30)"])
        fin = time.monotonic() + 10
        while time.monotonic() < fin and self.mgr.output(job["id"])["data"] == "":
            time.sleep(0.05)
        self.assertEqual(self.mgr.output(job["id"])["data"], "parcial\n")
        self.assertEqual(self.mgr.get(job["id"])["state"], RUNNING)

    def test_leer_la_salida_no_cambia_el_trabajo(self):
        job = self.correr("echo", "x")
        antes = self.mgr.get(job["id"])
        self.mgr.output(job["id"])
        self.assertEqual(self.mgr.get(job["id"]), antes)

    def test_id_inexistente(self):
        with self.assertRaises(KeyError):
            self.mgr.output("no-existe")

    def test_stream_invalido(self):
        job = self.correr("true")
        for valor in ("stdin", "", None, 1, "STDOUT"):
            with self.subTest(stream=valor):
                with self.assertRaisesRegex(ValueError, "stdout o stderr"):
                    self.mgr.output(job["id"], valor)

    def test_max_bytes_invalido(self):
        job = self.correr("true")
        for valor in (0, -1, MAX_SALIDA + 1, True, "5", 1.5, None):
            with self.subTest(max_bytes=valor):
                with self.assertRaisesRegex(ValueError, "max_bytes"):
                    self.mgr.output(job["id"], "stdout", valor)

    def test_archivo_borrado_de_un_trabajo_terminado_es_un_error_claro(self):
        job = self.correr("echo", "x")
        os.remove(job["stdout_path"])
        with self.assertRaisesRegex(ValueError, "no esta disponible"):
            self.mgr.output(job["id"])


class HealthTest(Base):
    max_jobs = 2
    queue_size = 3

    def test_campos_y_limites(self):
        h = self.mgr.health()
        self.assertEqual(set(h), {"version", "uptime_seconds", "jobs_by_state", "running", "max_jobs",
                                  "queued", "queue_size", "database"})
        self.assertEqual(h["version"], __version__)
        self.assertEqual((h["max_jobs"], h["queue_size"]), (2, 3))
        self.assertEqual(h["database"], "ok")

    def test_sin_trabajos_todo_en_cero(self):
        h = self.mgr.health()
        self.assertEqual(h["jobs_by_state"],
                         {"QUEUED": 0, "RUNNING": 0, "SUCCEEDED": 0, "FAILED": 0, "CANCELED": 0})
        self.assertEqual((h["running"], h["queued"]), (0, 0))

    def test_refleja_los_trabajos_por_estado(self):
        self.correr("true")                      # SUCCEEDED
        self.correr("sh", "-c", "exit 1")        # FAILED
        a = self.mgr.submit(["sleep", "30"])     # RUNNING
        self.mgr.submit(["sleep", "30"])         # RUNNING (2 de 2)
        q = self.mgr.submit(["sleep", "30"])     # QUEUED
        self.mgr.submit(["sleep", "30"])         # QUEUED
        self.mgr.cancel(q["id"])                 # CANCELED (estaba en cola)
        h = self.mgr.health()
        self.assertEqual(h["jobs_by_state"],
                         {"QUEUED": 1, "RUNNING": 2, "SUCCEEDED": 1, "FAILED": 1, "CANCELED": 1})
        self.assertEqual((h["running"], h["queued"]), (2, 1))
        self.assertIsNotNone(a)

    def test_el_total_por_estado_es_el_total_de_trabajos(self):
        for _ in range(4):
            self.mgr.submit(["sleep", "30"])
        h = self.mgr.health()
        self.assertEqual(sum(h["jobs_by_state"].values()), len(self.mgr.list()))

    def test_el_tiempo_activo_avanza(self):
        primero = self.mgr.health()["uptime_seconds"]
        time.sleep(0.25)
        segundo = self.mgr.health()["uptime_seconds"]
        self.assertGreaterEqual(primero, 0)
        self.assertGreater(segundo, primero)

    def test_base_con_problemas_se_informa_sin_romper_health(self):
        self.store.close()
        h = self.mgr.health()
        self.assertTrue(h["database"].startswith("error: "), h["database"])

    def test_sin_base_configurada(self):
        with tempfile.TemporaryDirectory() as d:
            h = JobManager(data_dir=d).health()
        self.assertEqual(h["database"], "no configurada")


class FalsaRed:
    def __init__(self, clientes, rechazados):
        self._datos = {"clientes": clientes, "rechazados": rechazados}

    def estadisticas(self):
        return self._datos


class ComandosDelServidorTest(Base):
    def test_health_agrega_los_datos_de_red(self):
        r = handle_request(self.mgr, {"cmd": "health"}, FalsaRed(3, 7))
        self.assertEqual((r["clients"], r["rejected_access"]), (3, 7))
        self.assertEqual(r["max_jobs"], self.max_jobs)

    def test_health_sin_red_informa_cero(self):
        r = handle_request(self.mgr, {"cmd": "health"})
        self.assertEqual((r["clients"], r["rejected_access"]), (0, 0))

    def test_health_no_trae_la_clave_error(self):
        self.assertNotIn("error", handle_request(self.mgr, {"cmd": "health"}))

    def test_output_responde_los_cuatro_campos(self):
        job = self.correr("echo", "hola")
        r = handle_request(self.mgr, {"cmd": "output", "id": job["id"]})
        self.assertEqual(set(r), {"id", "stream", "data", "truncated"})
        self.assertEqual(r["data"], "hola\n")

    def test_output_acepta_stream_y_max_bytes(self):
        job = self.python("import sys; print('abcdefghij', file=sys.stderr)")
        r = handle_request(self.mgr, {"cmd": "output", "id": job["id"], "stream": "stderr", "max_bytes": 4})
        self.assertEqual((r["stream"], r["data"], r["truncated"]), ("stderr", "hij\n", True))

    def test_output_sin_id(self):
        self.assertEqual(handle_request(self.mgr, {"cmd": "output"}), {"error": "falta id"})

    def test_output_de_id_inexistente_sin_comillas(self):
        r = handle_request(self.mgr, {"cmd": "output", "id": "nada"})
        self.assertEqual(r, {"error": "No existe el trabajo nada"})

    def test_output_con_stream_o_max_bytes_invalidos_es_un_error_del_usuario(self):
        job = self.correr("true")
        for extra in ({"stream": "x"}, {"max_bytes": 0}, {"max_bytes": "5"}, {"max_bytes": None}):
            with self.subTest(extra=extra):
                r = handle_request(self.mgr, {"cmd": "output", "id": job["id"], **extra})
                self.assertEqual(list(r), ["error"])
                self.assertNotIn("interno", r["error"])

    # DEF-006 y DEF-007 (RNF-21, RNF-23)
    def test_cancelar_un_id_inexistente_no_pone_comillas_en_el_mensaje(self):
        r = handle_request(self.mgr, {"cmd": "cancel", "id": "nada"})
        self.assertEqual(r, {"error": "No existe el trabajo nada"})

    def test_list_con_estado_desconocido_no_es_un_error_interno(self):
        r = handle_request(self.mgr, {"cmd": "list", "state": "HECHO"})
        self.assertEqual(r, {"error": "Estado desconocido: HECHO"})

    def test_list_con_estado_que_no_es_texto(self):
        r = handle_request(self.mgr, {"cmd": "list", "state": 5})
        self.assertEqual(list(r), ["error"])
        self.assertIn("state", r["error"])

    def test_list_con_estado_valido_sigue_funcionando(self):
        self.correr("true")
        self.assertEqual(len(handle_request(self.mgr, {"cmd": "list", "state": "succeeded"})["jobs"]), 1)


if __name__ == "__main__":
    unittest.main()
