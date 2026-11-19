"""Servidor con TCP (J2, ADR-0008 y ADR-0009): el servidor real con --listen, en localhost."""
import json
import socket
import subprocess
import sys
import time
import unittest

from helpers import RAIZ, ServidorDePrueba, entorno

NL = bytes([10])


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto


def pedir_tcp(puerto, pedido, limite=5.0):
    with socket.create_connection(("127.0.0.1", puerto), timeout=limite) as c:
        c.sendall(json.dumps(pedido).encode("utf-8") + NL)
        datos = b""
        while not datos.endswith(NL):
            trozo = c.recv(65536)
            if not trozo:
                break
            datos += trozo
    return json.loads(datos)


class ServidorTcpTest(unittest.TestCase):
    def setUp(self):
        self.servidor = ServidorDePrueba()
        self.addCleanup(self.servidor.limpiar)
        self.puerto = puerto_libre()
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto)])

    def test_por_tcp_se_envia_consulta_y_cancela_igual_que_por_unix(self):
        trabajo = pedir_tcp(self.puerto, {"cmd": "submit", "argv": ["sleep", "300"]})
        self.assertEqual(trabajo["state"], "RUNNING")
        self.assertEqual(pedir_tcp(self.puerto, {"cmd": "status", "id": trabajo["id"]})["id"], trabajo["id"])
        # el mismo trabajo se ve por el socket Unix (CLI)
        self.assertEqual(self.servidor.estado(trabajo["id"])["id"], trabajo["id"])
        listado = pedir_tcp(self.puerto, {"cmd": "list"})["jobs"]
        self.assertEqual([t["id"] for t in listado], [trabajo["id"]])
        pedir_tcp(self.puerto, {"cmd": "cancel", "id": trabajo["id"]})
        self.assertEqual(self.servidor.esperar_estado_final(trabajo["id"])["state"], "CANCELED")

    def test_dos_clientes_conectados_a_la_vez_reciben_respuesta_sin_esperarse(self):
        ocioso_tcp = socket.create_connection(("127.0.0.1", self.puerto), timeout=5)
        self.addCleanup(ocioso_tcp.close)
        ocioso_unix = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ocioso_unix.connect(self.servidor.socket)
        self.addCleanup(ocioso_unix.close)
        inicio = time.monotonic()
        codigo, respuesta = self.servidor.cli_json("list")
        self.assertEqual(codigo, 0)
        self.assertEqual(pedir_tcp(self.puerto, {"cmd": "list"}), respuesta)
        self.assertLess(time.monotonic() - inicio, 3.0)   # antes esperaba hasta 5 s por cliente

    def test_varias_solicitudes_en_una_conexion_tcp(self):
        with socket.create_connection(("127.0.0.1", self.puerto), timeout=5) as c:
            c.sendall(b'{"cmd": "list"}' + NL + b'{"cmd": "nada"}' + NL + b'{"cmd": "list"}' + NL)
            datos = b""
            while datos.count(NL) < 3:
                datos += c.recv(65536)
        r1, r2, r3 = [json.loads(x) for x in datos.strip().split(NL)]
        self.assertEqual(r1, {"jobs": []})
        self.assertIn("comando desconocido", r2["error"])
        self.assertEqual(r3, {"jobs": []})

    def test_mensaje_mayor_de_64_kib_recibe_error_y_el_servidor_sigue(self):
        with socket.create_connection(("127.0.0.1", self.puerto), timeout=5) as c:
            c.sendall(b"x" * (70 * 1024))
            c.settimeout(5)
            respuesta = json.loads(c.recv(4096))
        self.assertIn("demasiado grande", respuesta["error"])
        self.assertEqual(pedir_tcp(self.puerto, {"cmd": "list"}), {"jobs": []})
        self.assertIn("mensaje demasiado grande", self.servidor.directorio.joinpath("jobrunner.log").read_text())

    def test_el_bitacora_registra_el_puerto_tcp(self):
        texto = self.servidor.directorio.joinpath("jobrunner.log").read_text()
        self.assertIn("servicio_iniciado", texto)
        self.assertIn("tcp=127.0.0.1:" + str(self.puerto), texto)

    def test_ctrl_c_libera_el_puerto_tcp(self):
        self.servidor.detener()
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", self.puerto), timeout=2).close()
        s = socket.socket()
        s.bind(("127.0.0.1", self.puerto))   # el puerto quedo libre
        s.close()


class ServidorTcpOpcionesTest(unittest.TestCase):
    def arrancar(self, *opciones):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        return servidor, subprocess.run(
            [sys.executable, "-m", "jobrunner.server", servidor.socket, *opciones],
            capture_output=True, text=True, env=entorno(), cwd=str(RAIZ), timeout=15,
        )

    def test_direccion_invalida_no_arranca(self):
        servidor, r = self.arrancar("--listen", "7070")
        self.assertEqual(r.returncode, 2)
        self.assertIn("direccion invalida", r.stderr)

    def test_puerto_ocupado_no_arranca_y_no_deja_el_socket_unix(self):
        ocupado = socket.socket()
        ocupado.bind(("127.0.0.1", 0))
        ocupado.listen(1)
        self.addCleanup(ocupado.close)
        servidor, r = self.arrancar("--listen", "127.0.0.1:" + str(ocupado.getsockname()[1]))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no se pudo abrir el servicio", r.stderr)
        self.assertFalse(servidor.directorio.joinpath("jobrunner.sock").exists())

    def test_sin_listen_no_se_abre_ningun_puerto_tcp(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        servidor.iniciar()
        self.assertNotIn("tcp=", servidor.directorio.joinpath("jobrunner.log").read_text())


if __name__ == "__main__":
    unittest.main()
