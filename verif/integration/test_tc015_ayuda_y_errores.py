"""TC-015 (RF-17, RNF-21, RNF-23): ayuda y mensajes de error.

- `--help` de cada comando, y codigos de salida: 0 exito, 1 error del servicio o sin conexion,
  2 uso incorrecto.
- Cada error trae operacion, causa y accion, en una sola linea y sin traceback (RNF-21).
- La guia de usuario documenta cada comando y opcion, y los comandos de sus ejemplos son validos
  (apoyo a RNF-23; la demostracion con una persona que sigue la guia es manual, ver el TC).
"""
import json
import re
import shlex
import unittest
from pathlib import Path

from helpers import RAIZ
from helpers_remoto import ClienteRemotoBase, puerto_libre, royito

COMANDOS = ("submit", "status", "list", "cancel", "output", "health")
GUIAS = (RAIZ / "docs" / "user-guide" / "guia-de-usuario.md",
         RAIZ / "docs" / "user-guide" / "conexion-lan-vpn.md")
ERROR_CON_ACCION = re.compile(r"^Error al [^:\n]+: [^\n]+\. Que hacer: [^\n]+\.$")


class AyudaTest(unittest.TestCase):

    def test_la_ayuda_general_lista_los_comandos_y_las_opciones_de_red(self):
        codigo, salida, err = royito("--help")
        self.assertEqual(codigo, 0, err)
        self.assertIn("usage: royito", salida)
        for comando in COMANDOS:
            with self.subTest(comando=comando):
                self.assertIn(comando, salida)
        for opcion in ("--socket", "--host", "--port", "JOBRUNNER_HOST", "JOBRUNNER_PORT"):
            with self.subTest(opcion=opcion):
                self.assertIn(opcion, salida)

    def test_la_ayuda_general_explica_los_codigos_de_salida(self):
        _, salida, _ = royito("--help")
        flat = " ".join(salida.split())
        self.assertIn("0 operacion exitosa", flat)
        self.assertIn("1 error", flat)
        self.assertIn("2 uso incorrecto", flat)

    def test_cada_comando_tiene_ayuda_con_su_nombre_y_una_descripcion(self):
        for comando in COMANDOS:
            with self.subTest(comando=comando):
                codigo, salida, err = royito(comando, "--help")
                self.assertEqual(codigo, 0, err)
                self.assertIn("usage: royito " + comando, salida)
                lineas = [l for l in salida.splitlines() if l.strip()]
                self.assertGreater(len(lineas), 3)   # algo mas que la linea de uso

    def test_la_ayuda_de_cada_comando_documenta_sus_opciones(self):
        esperadas = {
            "submit": ("argv", "--request-id"),
            "status": ("id",),
            "list": ("--state", "QUEUED"),
            "cancel": ("id",),
            "output": ("--stderr", "--max-bytes", "--raw", "65536"),
            "health": ("salud", "--max-jobs", "--queue-size"),
        }
        for comando, textos in esperadas.items():
            _, salida, _ = royito(comando, "--help")
            for texto in textos:
                with self.subTest(comando=comando, texto=texto):
                    self.assertIn(texto, salida)

    def test_la_ayuda_no_necesita_el_servicio(self):
        # Sin servidor y con un host que no existe: la ayuda responde igual y sale con 0.
        codigo, _, _ = royito("--host", "no-existe.invalid", "output", "--help")
        self.assertEqual(codigo, 0)


class CodigosDeSalidaTest(ClienteRemotoBase):

    def test_0_cuando_la_operacion_se_hizo(self):
        for args in (("list",), ("health",), ("submit", "--", "true")):
            with self.subTest(args=args):
                self.assertEqual(self.servidor.cli(*args)[0], 0)
                self.assertEqual(self.tcp(*args)[0], 0)

    def test_0_aunque_el_trabajo_haya_fallado(self):
        _, trabajo = self.servidor.enviar("--", "sh", "-c", "exit 7")
        self.servidor.esperar_estado_final(trabajo["id"])
        for ejecutar in (self.servidor.cli, self.tcp):
            self.assertEqual(ejecutar("status", trabajo["id"])[0], 0)
            self.assertEqual(ejecutar("output", trabajo["id"])[0], 0)

    def test_1_cuando_el_servicio_rechaza_la_operacion(self):
        for args in (("status", "x"), ("cancel", "x"), ("output", "x"), ("list", "--state", "HECHO")):
            with self.subTest(args=args):
                self.assertEqual(self.servidor.cli(*args)[0], 1)
                self.assertEqual(self.tcp(*args)[0], 1)

    def test_2_cuando_el_comando_esta_mal_escrito(self):
        casos = (
            (),                                  # falta el comando
            ("hola",),                           # comando que no existe
            ("submit",),                         # falta el comando a ejecutar
            ("status",),                         # falta el id
            ("list", "--nada"),                  # opcion que no existe
            ("output", "x", "--max-bytes", "a"), # valor que no es numero
            ("--port", "7070", "list"),          # --port sin --host
        )
        for args in casos:
            with self.subTest(args=args):
                codigo, salida, err = royito(*args)
                self.assertEqual(codigo, 2, err)
                self.assertEqual(salida, "")
                self.assertTrue(err.strip(), "debe explicar el uso en stderr")

    def test_el_error_de_uso_nombra_los_comandos_validos(self):
        _, _, err = royito("hola")
        for comando in COMANDOS:
            self.assertIn(comando, err)


class ErroresConCausaYAccionTest(ClienteRemotoBase):
    opciones_extra = ("--max-jobs", "1", "--queue-size", "0")

    def assertErrorCompleto(self, ejecutar, args, operacion, causa, accion):
        codigo, salida, err = ejecutar(*args)
        self.assertEqual(codigo, 1)
        linea = err.strip()
        self.assertEqual(len(linea.splitlines()), 1, err)
        self.assertRegex(linea, ERROR_CON_ACCION)
        self.assertIn("Error al " + operacion, linea)
        self.assertIn(causa.lower(), linea.lower())
        self.assertIn(accion, linea)
        self.assertNotIn("Traceback", err)
        self.assertIn("error", json.loads(salida))   # el JSON de la respuesta sigue en stdout

    def test_cada_error_del_servicio_dice_operacion_causa_y_accion(self):
        self.servidor.enviar("--", "sleep", "30")      # ocupa el unico lugar
        casos = (
            (("status", "x"), "consultar el trabajo", "no existe el trabajo x", "royito list"),
            (("cancel", "x"), "cancelar el trabajo", "no existe el trabajo x", "royito list"),
            (("output", "x"), "leer la salida del trabajo", "no existe el trabajo x", "royito list"),
            (("list", "--state", "HECHO"), "listar los trabajos", "estado desconocido: HECHO", "CANCELED"),
            (("submit", "--", "sleep", "1"), "enviar el trabajo", "cola llena", "--queue-size"),
        )
        for ejecutar in (self.servidor.cli, self.tcp):
            for args, operacion, causa, accion in casos:
                with self.subTest(args=args):
                    self.assertErrorCompleto(ejecutar, args, operacion, causa, accion)

    def test_cancelar_un_trabajo_terminado(self):
        _, trabajo = self.servidor.enviar("--", "true")
        self.servidor.esperar_estado_final(trabajo["id"])
        for ejecutar in (self.servidor.cli, self.tcp):
            self.assertErrorCompleto(ejecutar, ("cancel", trabajo["id"]), "cancelar el trabajo",
                                     "ya termino en estado SUCCEEDED", "no hay nada que hacer")

    def test_output_fuera_de_rango(self):
        _, trabajo = self.servidor.enviar("--", "true")
        self.servidor.esperar_estado_final(trabajo["id"])
        self.assertErrorCompleto(self.tcp, ("output", trabajo["id"], "--max-bytes", "0"),
                                 "leer la salida del trabajo", "max_bytes", "1 a 65536")

    def test_request_id_invalido(self):
        self.assertErrorCompleto(self.tcp, ("submit", "--request-id", "no valido!", "--", "true"),
                                 "enviar el trabajo", "request_id", "1 a 64 caracteres")


class ErroresDeConexionTest(unittest.TestCase):

    def test_sin_servicio_local_dice_que_iniciar(self):
        codigo, _, err = royito("--socket", "/tmp/tc015-no-existe.sock", "list")
        self.assertEqual(codigo, 1)
        self.assertIn("no se pudo conectar al servidor en /tmp/tc015-no-existe.sock", err)
        self.assertIn("./scripts/run.sh", err)   # la accion
        self.assertNotIn("Traceback", err)

    def test_sin_servicio_remoto_dice_a_donde_y_que_revisar(self):
        puerto = puerto_libre()
        codigo, _, err = royito("--host", "127.0.0.1", "--port", str(puerto), "health")
        self.assertEqual(codigo, 1)
        self.assertIn("no se pudo conectar a 127.0.0.1:%d" % puerto, err)
        for pista in ("--listen", "--allow"):
            self.assertIn(pista, err)
        self.assertNotIn("Traceback", err)


class GuiaDeUsuarioTest(unittest.TestCase):
    """RNF-23: la guia explica todo lo que el usuario necesita para operar sin ayuda."""

    def setUp(self):
        self.guia = GUIAS[0].read_text(encoding="utf-8")

    def test_la_guia_explica_cada_comando(self):
        for comando in COMANDOS:
            with self.subTest(comando=comando):
                self.assertIn("royito " + comando, self.guia)

    def test_la_guia_explica_cada_opcion_del_cliente_y_del_servicio(self):
        for opcion in ("--host", "--port", "JOBRUNNER_HOST", "JOBRUNNER_PORT", "--stderr", "--max-bytes",
                       "--raw", "--state", "--request-id", "--max-jobs", "--queue-size", "--listen",
                       "--allow", "--help"):
            with self.subTest(opcion=opcion):
                self.assertIn(opcion, self.guia)

    def test_la_guia_explica_los_codigos_de_salida_y_los_errores(self):
        for texto in ("código **0**", "**1**", "**2**", "Que hacer",
                      "no se pudo conectar a HOST:PUERTO", "cola llena", "Estado desconocido"):
            with self.subTest(texto=texto):
                self.assertIn(texto, self.guia)

    def test_la_guia_explica_la_salud_campo_por_campo(self):
        for campo in ("version", "uptime_seconds", "jobs_by_state", "running", "max_jobs", "queued",
                      "queue_size", "database", "clients", "rejected_access"):
            with self.subTest(campo=campo):
                self.assertIn("`" + campo + "`", self.guia)

    def test_los_comandos_royito_de_los_ejemplos_son_validos(self):
        """Cada linea `royito ...` de un bloque de codigo se acepta tal cual por el CLI."""
        from jobrunner import cli
        revisados = 0
        for guia in GUIAS:
            texto = guia.read_text(encoding="utf-8")
            for bloque in re.findall(r"```(?:bash)?\n(.*?)```", texto, flags=re.S):
                for linea in bloque.splitlines():
                    linea = linea.strip()
                    if not linea.startswith("royito "):
                        continue
                    args = shlex.split(linea, comments=True)[1:]
                    args = ["id-de-ejemplo" if a.startswith("<") else a for a in args]
                    parser = cli.build_parser()
                    with self.subTest(guia=guia.name, comando=linea):
                        try:
                            parser.parse_args(args)
                        except SystemExit as e:
                            self.fail("la guia usa un comando que el CLI rechaza (codigo %s): %s" % (e.code, linea))
                    revisados += 1
        self.assertGreaterEqual(revisados, 8)


if __name__ == "__main__":
    unittest.main()
