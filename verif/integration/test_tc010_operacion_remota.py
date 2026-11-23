"""TC-010 (RF-18, RF-19): operacion remota con la misma semantica que en local.

Con el servidor real escuchando en 127.0.0.1 y el CLI real, cada comando (submit, status, list,
output y cancel) por TCP da lo mismo que por el socket Unix: mismas respuestas, mismos errores y
mismos codigos de salida. Los campos que cambian en cada trabajo (id, fechas, pid y rutas de
salida) se descartan al comparar. La demostracion entre dos equipos reales es manual (TC-010,
pasos manuales); aqui todo ocurre en la misma maquina y sin abrir puertos a la red.
"""
import json
import sys
import unittest

from helpers_remoto import ClienteRemotoBase

VOLATILES = ("id", "created_at", "started_at", "finished_at", "pid", "stdout_path", "stderr_path")


def normalizar(respuesta):
    """La respuesta sin los campos que cambian en cada trabajo (tambien dentro de un listado)."""
    if isinstance(respuesta, dict):
        return {k: normalizar(v) for k, v in respuesta.items() if k not in VOLATILES}
    if isinstance(respuesta, list):
        return [normalizar(x) for x in respuesta]
    return respuesta


class MismaSemanticaBase(ClienteRemotoBase):
    """`ambos(...)` ejecuta el mismo comando por Unix y por TCP y devuelve las dos tuplas."""

    def unix(self, *args):
        return self.servidor.cli(*args)

    def ambos(self, *args):
        return self.unix(*args), self.tcp(*args)

    def esperar(self, job_id):
        return self.servidor.esperar_estado_final(job_id)


class ComandosPorTcpTest(MismaSemanticaBase):

    def test_submit_por_tcp_y_por_unix_dan_la_misma_respuesta(self):
        (cu, su, eu), (ct, st, et) = self.ambos("submit", "--", "sleep", "30")
        self.assertEqual((cu, ct), (0, 0), eu + et)
        unix, tcp = json.loads(su), json.loads(st)
        self.assertEqual(normalizar(unix), normalizar(tcp))
        self.assertEqual((tcp["v"], tcp["state"], tcp["argv"]), (1, "RUNNING", ["sleep", "30"]))
        self.assertNotEqual(unix["id"], tcp["id"])   # dos trabajos distintos

    def test_status_de_un_trabajo_da_lo_mismo_por_los_dos_transportes(self):
        _, trabajo = self.servidor.enviar("--", "sh", "-c", "echo listo; exit 3")
        final = self.esperar(trabajo["id"])
        self.assertEqual((final["state"], final["exit_code"]), ("FAILED", 3))
        (cu, su, _), (ct, st, _) = self.ambos("status", trabajo["id"])
        self.assertEqual((cu, ct), (0, 0))   # un trabajo FAILED es una operacion exitosa
        self.assertEqual(json.loads(su), json.loads(st))

    def test_list_es_identico_por_los_dos_transportes(self):
        for argv in (("true",), ("sh", "-c", "exit 1"), ("sleep", "30")):
            self.servidor.enviar("--", *argv)
        self.esperar(self.servidor.listar()[0]["id"])
        for filtro in ((), ("--state", "RUNNING"), ("--state", "failed")):
            with self.subTest(filtro=filtro):
                (cu, su, _), (ct, st, _) = self.ambos("list", *filtro)
                self.assertEqual((cu, ct), (0, 0))
                self.assertEqual(json.loads(su), json.loads(st))

    def test_output_es_identico_por_los_dos_transportes(self):
        _, trabajo = self.servidor.enviar(
            "--", sys.executable, "-c", "import sys; print('bien'); print('mal', file=sys.stderr)")
        self.esperar(trabajo["id"])
        for extra, esperado in (((), "bien\n"), (("--stderr",), "mal\n")):
            with self.subTest(extra=extra):
                (cu, su, _), (ct, st, _) = self.ambos("output", trabajo["id"], *extra)
                self.assertEqual((cu, ct), (0, 0))
                self.assertEqual(json.loads(su), json.loads(st))
                self.assertEqual(json.loads(st)["data"], esperado)

    def test_cancel_por_tcp_y_por_unix_dan_la_misma_respuesta_y_el_mismo_final(self):
        _, a = self.servidor.enviar("--", "sleep", "30")
        _, b = self.servidor.enviar("--", "sleep", "30")
        cu, su, _ = self.unix("cancel", a["id"])
        ct, st, _ = self.tcp("cancel", b["id"])
        self.assertEqual((cu, ct), (0, 0))
        # ADR-0006: se responde de inmediato, con el trabajo todavia en RUNNING.
        self.assertEqual(normalizar(json.loads(su)), normalizar(json.loads(st)))
        for job_id in (a["id"], b["id"]):
            final = self.esperar(job_id)
            self.assertEqual((final["state"], final["exit_code"]), ("CANCELED", -15))

    def test_cancelar_dos_veces_por_tcp_devuelve_el_estado_sin_error(self):
        _, trabajo = self.servidor.enviar("--", "sleep", "30")
        self.assertEqual(self.tcp("cancel", trabajo["id"])[0], 0)
        codigo, salida, _ = self.tcp("cancel", trabajo["id"])
        self.assertEqual(codigo, 0)
        self.assertEqual(json.loads(salida)["id"], trabajo["id"])

    def test_request_id_enviado_por_un_transporte_se_reconoce_en_el_otro(self):
        _, primero, _ = self.unix("submit", "--request-id", "tc010", "--", "sleep", "30")
        codigo, segundo, _ = self.tcp("submit", "--request-id", "tc010", "--", "sleep", "30")
        self.assertEqual(codigo, 0)
        self.assertEqual(json.loads(segundo)["id"], json.loads(primero)["id"])
        self.assertTrue(json.loads(segundo)["duplicado"])
        self.assertEqual(len(self.servidor.listar()), 1)

    def test_lo_que_se_hace_por_un_transporte_se_ve_por_el_otro(self):
        _, por_tcp, _ = self.tcp("submit", "--", "sleep", "30")
        _, por_unix = self.servidor.enviar("--", "sleep", "30")
        ids = {t["id"] for t in json.loads(self.tcp("list")[1])["jobs"]}
        self.assertEqual(ids, {json.loads(por_tcp)["id"], por_unix["id"]})
        self.assertEqual({t["id"] for t in self.servidor.listar()}, ids)


class ErroresIgualesPorTcpTest(MismaSemanticaBase):
    opciones_extra = ("--max-jobs", "1", "--queue-size", "0")

    def assertMismoError(self, *args):
        (cu, su, eu), (ct, st, et) = self.ambos(*args)
        self.assertEqual((cu, ct), (1, 1), "%s\n%s" % (eu, et))
        self.assertEqual(json.loads(su), json.loads(st))
        self.assertEqual(eu, et)   # tambien la linea de stderr: operacion, causa y accion
        self.assertEqual(list(json.loads(st)), ["v", "error"])
        return json.loads(st)["error"]

    def test_id_inexistente_en_status_cancel_y_output(self):
        for comando in ("status", "cancel", "output"):
            with self.subTest(comando=comando):
                self.assertIn("no existe el trabajo no-existe",
                              self.assertMismoError(comando, "no-existe").lower())

    def test_estado_desconocido_en_list(self):
        self.assertIn("Estado desconocido: HECHO", self.assertMismoError("list", "--state", "HECHO"))

    def test_cola_llena(self):
        self.servidor.enviar("--", "sleep", "30")   # ocupa el unico lugar para correr
        error = self.assertMismoError("submit", "--", "sleep", "30")
        self.assertIn("cola llena (capacidad 0)", error)
        self.assertEqual(len(self.servidor.listar()), 1)   # el rechazado no crea trabajo

    def test_cancelar_un_trabajo_ya_terminado(self):
        _, trabajo = self.servidor.enviar("--", "true")
        self.esperar(trabajo["id"])
        self.assertIn("ya termino en estado SUCCEEDED", self.assertMismoError("cancel", trabajo["id"]))

    def test_request_id_con_otro_comando(self):
        self.servidor.cli("submit", "--request-id", "mismo", "--", "sleep", "30")
        error = self.assertMismoError("submit", "--request-id", "mismo", "--", "sleep", "31")
        self.assertIn("request_id ya se uso para otro comando", error)


if __name__ == "__main__":
    unittest.main()
