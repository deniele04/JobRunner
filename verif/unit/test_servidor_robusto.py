"""Robustez del servidor y del CLI ante entradas y clientes problematicos.

Cubre los pendientes del Avance 1: bytes que no son texto valido, cliente que
se desconecta antes de recibir la respuesta y codigo de salida del CLI.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO

from jobrunner import cli

NL = bytes([10])
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def json_linea(obj):
    return json.dumps(obj).encode("utf-8") + NL


def pedir(ruta, datos):
    """Envia bytes crudos al servidor y devuelve la respuesta decodificada."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as c:
        c.settimeout(5)
        c.connect(ruta)
        c.sendall(datos)
        resp = b""
        while not resp.endswith(NL):
            trozo = c.recv(4096)
            if not trozo:
                break
            resp += trozo
    return json.loads(resp.decode("utf-8"))


class ServidorRobustoTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self._tmp.name, "jobrunner.sock")
        entorno = dict(os.environ, PYTHONPATH=os.path.join(RAIZ, "src"))
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "jobrunner.server", self.ruta],
            env=entorno, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        limite = time.monotonic() + 5
        while not os.path.exists(self.ruta):
            if time.monotonic() > limite or self.proc.poll() is not None:
                self.fail("el servidor no arranco")
            time.sleep(0.05)

    def tearDown(self):
        self.proc.terminate()
        self.proc.wait(timeout=5)
        self._tmp.cleanup()

    def assertServidorVivo(self):
        self.assertIsNone(self.proc.poll(), "el servidor termino")
        self.assertIn("jobs", pedir(self.ruta, json_linea({"cmd": "list"})))

    def test_bytes_que_no_son_texto_valido(self):
        respuesta = pedir(self.ruta, bytes([0xFF, 0xFE]) + NL)
        self.assertIn("error", respuesta)
        self.assertServidorVivo()

    def test_cliente_que_se_desconecta_antes_de_la_respuesta(self):
        for _ in range(5):
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as c:
                c.connect(self.ruta)
                c.sendall(json_linea({"cmd": "list"}))
        time.sleep(0.3)
        self.assertServidorVivo()


class CodigoDeSalidaCliTest(unittest.TestCase):
    def codigo(self, respuesta):
        with redirect_stdout(StringIO()):
            try:
                cli.print_response(respuesta)
            except SystemExit as e:
                return e.code
        return 0

    def test_trabajo_con_error_nulo_no_es_error(self):
        trabajo = {"id": "x", "state": "QUEUED", "error": None}
        self.assertEqual(self.codigo(trabajo), 0)

    def test_trabajo_fallido_sigue_siendo_una_operacion_exitosa(self):
        trabajo = {"id": "x", "state": "FAILED", "error": "SIGTERM"}
        self.assertEqual(self.codigo(trabajo), 0)

    def test_listado_no_es_error(self):
        self.assertEqual(self.codigo({"jobs": []}), 0)

    def test_error_de_operacion_sale_con_1(self):
        self.assertEqual(self.codigo({"error": "falta id"}), 1)


if __name__ == "__main__":
    unittest.main()