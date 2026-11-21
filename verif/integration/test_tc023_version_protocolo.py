"""TC-023 (J4, ADR-0009 regla 1): campo "v" de version del protocolo, con el servidor real y la CLI."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

from helpers import RAIZ, ServidorDePrueba, entorno

NL = bytes([10])


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto


def hablar(sock, texto_o_dict):
    """Envia una linea y devuelve la respuesta ya decodificada."""
    datos = texto_o_dict if isinstance(texto_o_dict, bytes) else json.dumps(texto_o_dict).encode("utf-8")
    sock.sendall(datos + NL)
    respuesta = b""
    while not respuesta.endswith(NL):
        trozo = sock.recv(65536)
        if not trozo:
            break
        respuesta += trozo
    return json.loads(respuesta)


class VersionDelProtocoloTest(unittest.TestCase):
    def setUp(self):
        self.servidor = ServidorDePrueba()
        self.addCleanup(self.servidor.limpiar)
        self.puerto = puerto_libre()
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto)])

    def unix(self):
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(5)
        c.connect(self.servidor.socket)
        self.addCleanup(c.close)
        return c

    def tcp(self):
        c = socket.create_connection(("127.0.0.1", self.puerto), timeout=5)
        self.addCleanup(c.close)
        return c

    def conexiones(self):
        return (("unix", self.unix), ("tcp", self.tcp))

    def bitacora(self):
        return self.servidor.directorio.joinpath("jobrunner.log").read_text()

    def test_toda_respuesta_lleva_v_1_y_va_primero(self):
        pedidos = [
            {"cmd": "list"},
            {"cmd": "status", "id": "no-existe"},
            {"cmd": "cancel", "id": "no-existe"},
            {"cmd": "nada"},
            {"cmd": "submit", "argv": []},
            {"cmd": "submit", "argv": ["true"]},
        ]
        for nombre, abrir in self.conexiones():
            c = abrir()
            for pedido in pedidos:
                with self.subTest(transporte=nombre, cmd=pedido["cmd"]):
                    respuesta = hablar(c, pedido)
                    self.assertEqual(respuesta["v"], 1)
                    self.assertEqual(list(respuesta)[0], "v")

    def test_el_json_invalido_tambien_lleva_v(self):
        for nombre, abrir in self.conexiones():
            with self.subTest(transporte=nombre):
                respuesta = hablar(abrir(), b"esto no es json")
                self.assertEqual(respuesta, {"v": 1, "error": "JSON invalido"})

    def test_solicitud_que_no_es_un_objeto_recibe_error_con_v(self):
        c = self.unix()
        for texto in (b"[1, 2]", b'"hola"', b"5", b"null"):
            with self.subTest(solicitud=texto):
                respuesta = hablar(c, texto)
                self.assertEqual(respuesta, {"v": 1, "error": "la solicitud debe ser un objeto JSON"})
        self.assertEqual(hablar(c, {"cmd": "list"}), {"v": 1, "jobs": []})   # la conexion sigue sirviendo

    def test_sin_v_se_toma_como_1(self):
        self.assertEqual(hablar(self.unix(), {"cmd": "list"}), {"v": 1, "jobs": []})

    def test_con_v_1_se_atiende_igual(self):
        for nombre, abrir in self.conexiones():
            with self.subTest(transporte=nombre):
                self.assertEqual(hablar(abrir(), {"v": 1, "cmd": "list"}), {"v": 1, "jobs": []})

    def test_version_desconocida_recibe_el_error_exacto_del_adr(self):
        casos = {"2": 2, "0": 0, "-1": -1, "99": 99, '"1"': "1", "1.0": 1.0, "true": True, "null": None, "[1]": [1]}
        for esperado, valor in casos.items():
            for nombre, abrir in self.conexiones():
                with self.subTest(v=esperado, transporte=nombre):
                    respuesta = hablar(abrir(), {"v": valor, "cmd": "list"})
                    self.assertEqual(respuesta, {
                        "v": 1,
                        "error": "version de protocolo no soportada: " + esperado + " (soportada: 1)",
                    })

    def test_la_version_se_revisa_antes_que_el_comando(self):
        respuesta = hablar(self.unix(), {"v": 2, "cmd": "comando-que-no-existe"})
        self.assertIn("version de protocolo no soportada: 2", respuesta["error"])

    def test_una_version_no_soportada_no_ejecuta_nada(self):
        respuesta = hablar(self.unix(), {"v": 2, "cmd": "submit", "argv": ["sleep", "300"]})
        self.assertIn("no soportada", respuesta["error"])
        self.assertEqual(hablar(self.unix(), {"cmd": "list"})["jobs"], [])

    def test_la_version_no_soportada_se_registra_y_la_conexion_sigue_viva(self):
        c = self.tcp()
        hablar(c, {"v": 3, "cmd": "list"})
        self.assertEqual(hablar(c, {"v": 1, "cmd": "list"}), {"v": 1, "jobs": []})
        self.assertIn("version de protocolo no soportada", self.bitacora())

    def test_el_trabajo_devuelto_conserva_sus_campos_y_agrega_v(self):
        trabajo = hablar(self.unix(), {"cmd": "submit", "argv": ["sleep", "300"]})
        self.assertEqual(trabajo["v"], 1)
        for campo in ("id", "state", "argv", "pid"):
            self.assertIn(campo, trabajo)
        self.assertEqual(hablar(self.unix(), {"cmd": "status", "id": trabajo["id"]})["id"], trabajo["id"])

    def test_el_mensaje_demasiado_grande_tambien_lleva_v(self):
        c = self.tcp()
        c.sendall(b"x" * (70 * 1024))
        respuesta = json.loads(c.recv(4096))
        self.assertEqual(respuesta["v"], 1)
        self.assertIn("demasiado grande", respuesta["error"])


class ClienteYVersionTest(unittest.TestCase):
    """La CLI envia "v": 1 y se niega a seguir si el servidor habla otra version."""

    def servidor_falso(self, respuesta):
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        ruta = os.path.join(directorio.name, "falso.sock")
        escucha = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        escucha.bind(ruta)
        escucha.listen(1)
        self.addCleanup(escucha.close)
        recibido = []

        def atender():
            conexion, _ = escucha.accept()
            with conexion:
                datos = b""
                while not datos.endswith(NL):
                    datos += conexion.recv(4096)
                recibido.append(json.loads(datos))
                conexion.sendall(json.dumps(respuesta).encode("utf-8") + NL)

        hilo = threading.Thread(target=atender, daemon=True)
        hilo.start()
        return ruta, recibido, hilo

    def royito(self, ruta, *argumentos):
        return subprocess.run(
            [sys.executable, "-m", "jobrunner.cli", "--socket", ruta, *argumentos],
            capture_output=True, text=True, env=entorno(), cwd=str(RAIZ), timeout=15,
        )

    def test_la_cli_envia_v_1(self):
        ruta, recibido, hilo = self.servidor_falso({"v": 1, "jobs": []})
        r = self.royito(ruta, "list")
        hilo.join(5)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(recibido[0]["v"], 1)
        self.assertEqual(recibido[0]["cmd"], "list")

    def test_la_cli_rechaza_un_servidor_con_otra_version(self):
        ruta, _, hilo = self.servidor_falso({"v": 2, "jobs": []})
        r = self.royito(ruta, "list")
        hilo.join(5)
        self.assertEqual(r.returncode, 1)
        self.assertIn("protocolo v2", r.stderr)

    def test_un_error_del_servicio_con_v_sale_con_codigo_1(self):
        ruta, _, hilo = self.servidor_falso({"v": 1, "error": "no existe el trabajo x"})
        r = self.royito(ruta, "status", "x")
        hilo.join(5)
        self.assertEqual(r.returncode, 1)

    def test_un_trabajo_fallido_con_v_sigue_siendo_una_operacion_exitosa(self):
        ruta, _, hilo = self.servidor_falso(
            {"v": 1, "id": "j1", "state": "FAILED", "exit_code": 1, "error": "salio con codigo 1"})
        r = self.royito(ruta, "status", "j1")
        hilo.join(5)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
