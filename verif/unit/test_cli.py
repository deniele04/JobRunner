"""Piezas del CLI que no necesitan servidor: regla del codigo de salida, mensajes y destino (U1)."""
import os
import unittest
from unittest import mock

from jobrunner import cli


def analizar(*argv, entorno=None):
    """build_parser + resolver_destino con un entorno controlado."""
    with mock.patch.dict(os.environ, entorno or {}, clear=False):
        for variable in ("JOBRUNNER_HOST", "JOBRUNNER_PORT"):
            if not entorno or variable not in entorno:
                os.environ.pop(variable, None)
        parser = cli.build_parser()   # lee JOBRUNNER_HOST al construirse
        args = parser.parse_args(list(argv))
        cli.resolver_destino(parser, args)
    return args


class ReglaDelCodigoDeSalidaTest(unittest.TestCase):
    def test_error_del_servicio_con_v(self):
        self.assertTrue(cli.es_error_del_servicio({"v": 1, "error": "falta id"}))

    def test_error_del_servicio_sin_v(self):
        self.assertTrue(cli.es_error_del_servicio({"error": "falta id"}))

    def test_un_trabajo_no_es_error_aunque_traiga_error(self):
        for error in (None, "SIGTERM", "No se pudo ejecutar 'x'"):
            with self.subTest(error=error):
                self.assertFalse(cli.es_error_del_servicio(
                    {"v": 1, "id": "j", "state": "FAILED", "error": error}))

    def test_un_listado_no_es_error(self):
        self.assertFalse(cli.es_error_del_servicio({"v": 1, "jobs": []}))

    def test_las_respuestas_sin_error_no_lo_son(self):
        self.assertFalse(cli.es_error_del_servicio({"v": 1, "uptime_seconds": 1.0}))
        self.assertFalse(cli.es_error_del_servicio({"v": 1, "id": "j", "stream": "stdout", "data": ""}))

    def test_lo_que_no_es_un_objeto_no_es_error(self):
        self.assertFalse(cli.es_error_del_servicio([1, 2]))


class MensajeDeErrorTest(unittest.TestCase):
    def test_lleva_operacion_causa_y_accion(self):
        texto = cli.mensaje_de_error("status", {"v": 1, "error": "no existe el trabajo abc"})
        self.assertIn("Error al consultar el trabajo", texto)
        self.assertIn("no existe el trabajo abc", texto)
        self.assertIn("Que hacer: ", texto)
        self.assertIn("royito list", texto)

    def test_cada_error_conocido_tiene_su_accion(self):
        errores = {
            "cancel": ["El trabajo x ya termino en estado FAILED; no se puede cancelar"],
            "submit": ["cola llena (capacidad 3); intenta más tarde",
                       "argv debe ser una lista no vacia de strings",
                       "request_id debe ser texto de 1 a 64 caracteres (letras, numeros, - y _)",
                       "el servicio se esta cerrando; no acepta trabajos nuevos"],
            "list": ["Estado desconocido: X"],
            "status": ["version de protocolo no soportada: 2 (soportada: 1)",
                       "error interno: algo"],
        }
        for comando, mensajes in errores.items():
            for mensaje in mensajes:
                with self.subTest(error=mensaje):
                    self.assertIn("Que hacer: ", cli.mensaje_de_error(comando, {"error": mensaje}))

    def test_un_error_desconocido_conserva_operacion_y_causa(self):
        texto = cli.mensaje_de_error("cancel", {"error": "algo raro"})
        self.assertEqual(texto, "Error al cancelar el trabajo: algo raro.")

    def test_no_duplica_el_punto_final(self):
        self.assertNotIn("..", cli.mensaje_de_error("list", {"error": "algo raro."}))


class DestinoTest(unittest.TestCase):
    def test_sin_host_es_el_socket_unix(self):
        args = analizar("list")
        self.assertIsNone(args.host)

    def test_con_host_y_sin_puerto_usa_7070(self):
        args = analizar("--host", "127.0.0.1", "list")
        self.assertEqual((args.host, args.port), ("127.0.0.1", 7070))

    def test_las_variables_de_entorno_dan_el_destino(self):
        args = analizar("list", entorno={"JOBRUNNER_HOST": "10.0.0.5", "JOBRUNNER_PORT": "9000"})
        self.assertEqual((args.host, args.port), ("10.0.0.5", 9000))

    def test_la_opcion_gana_a_la_variable(self):
        args = analizar("--host", "192.168.1.2", "--port", "8000", "list",
                        entorno={"JOBRUNNER_HOST": "10.0.0.5", "JOBRUNNER_PORT": "9000"})
        self.assertEqual((args.host, args.port), ("192.168.1.2", 8000))

    def test_host_vacio_en_el_entorno_se_toma_como_sin_host(self):
        self.assertIsNone(analizar("list", entorno={"JOBRUNNER_HOST": ""}).host)

    def test_port_sin_host_termina_con_error_de_uso(self):
        with self.assertRaises(SystemExit) as r:
            analizar("--port", "7070", "list")
        self.assertEqual(r.exception.code, 2)

    def test_formato_de_destino_con_ipv6(self):
        self.assertEqual(cli._destino("::1", 7070), "[::1]:7070")
        self.assertEqual(cli._destino("127.0.0.1", 7070), "127.0.0.1:7070")


if __name__ == "__main__":
    unittest.main()
