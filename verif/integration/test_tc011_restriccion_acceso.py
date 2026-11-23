"""TC-011 (J6, ADR-0008): restriccion de acceso por red (RF-20, RNF-12, RNF-13, RNF-26).

Servidor real. Para probarlo en una sola maquina: con --allow 10.0.0.0/8 (sin localhost) una
conexion desde 127.0.0.1 debe rechazarse; sin --allow solo entra 127.0.0.1 (127.0.0.2 es "otro
equipo" de la misma maquina).
"""
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


def pedir_desde(origen, puerto, pedido, limite=15.0):
    """Envia una solicitud desde `origen`. Devuelve el dict, o None si el servidor cerro sin responder."""
    c = socket.socket()
    c.settimeout(limite)
    try:
        c.bind((origen, 0))
        c.connect(("127.0.0.1", puerto))
        c.sendall(json.dumps(pedido).encode("utf-8") + NL)
        datos = b""
        while not datos.endswith(NL):
            trozo = c.recv(65536)
            if not trozo:
                break
            datos += trozo
    except ConnectionError:
        return None
    finally:
        c.close()
    return json.loads(datos) if datos else None


class TestTC011RestriccionAcceso(unittest.TestCase):
    def iniciar(self, *allow):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        puerto = puerto_libre()
        opciones = ["--listen", "127.0.0.1:" + str(puerto)]
        for red in allow:
            opciones += ["--allow", red]
        servidor.iniciar(opciones=opciones)
        return servidor, puerto

    def bitacora(self, servidor, esperar=None):
        """Texto de la bitacora; con `esperar`, reintenta hasta 3 s a que aparezca esa cadena."""
        limite = time.monotonic() + 3.0
        while True:
            texto = servidor.directorio.joinpath("jobrunner.log").read_text()
            if esperar is None or esperar in texto or time.monotonic() > limite:
                return texto
            time.sleep(0.05)

    def test_con_allow_10_0_0_0_8_la_conexion_desde_127_0_0_1_se_rechaza(self):
        servidor, puerto = self.iniciar("10.0.0.0/8")
        self.assertIsNone(pedir_desde("127.0.0.1", puerto, {"cmd": "list"}))
        texto = self.bitacora(servidor, esperar="ip=127.0.0.1")
        self.assertIn("acceso_rechazado", texto)
        self.assertIn("ip=127.0.0.1", texto)

    def test_sin_allow_entra_127_0_0_1_y_no_otro_origen(self):
        servidor, puerto = self.iniciar()
        self.assertEqual(pedir_desde("127.0.0.1", puerto, {"cmd": "list"})["jobs"], [])
        self.assertIsNone(pedir_desde("127.0.0.2", puerto, {"cmd": "list"}))
        self.assertIn("ip=127.0.0.2", self.bitacora(servidor, esperar="ip=127.0.0.2"))

    def test_con_allow_se_acepta_solo_lo_indicado(self):
        _, puerto = self.iniciar("127.0.0.2/32")
        self.assertEqual(pedir_desde("127.0.0.2", puerto, {"cmd": "list"})["jobs"], [])
        self.assertIsNone(pedir_desde("127.0.0.1", puerto, {"cmd": "list"}))
        self.assertIsNone(pedir_desde("127.0.0.3", puerto, {"cmd": "list"}))

    def test_un_origen_rechazado_no_puede_enviar_ni_cancelar_nada(self):
        servidor, puerto = self.iniciar("10.0.0.0/8")
        self.assertIsNone(pedir_desde("127.0.0.1", puerto, {"cmd": "submit", "argv": ["sleep", "300"]}))
        self.assertEqual(servidor.listar(), [])   # por el socket Unix: no se creo ningun trabajo

    def test_el_socket_unix_sigue_funcionando_aunque_se_rechace_todo_por_tcp(self):
        servidor, puerto = self.iniciar("10.0.0.0/8")
        for _ in range(30):
            self.assertIsNone(pedir_desde("127.0.0.1", puerto, {"cmd": "list"}))
        trabajo = servidor.enviar("--", "true")[1]
        self.assertEqual(servidor.esperar_estado_final(trabajo["id"])["state"], "SUCCEEDED")

    def test_rechazos_y_permitidos_intercalados_no_se_afectan(self):
        _, puerto = self.iniciar("127.0.0.2")
        for _ in range(10):
            self.assertIsNone(pedir_desde("127.0.0.1", puerto, {"cmd": "list"}))
            self.assertEqual(pedir_desde("127.0.0.2", puerto, {"cmd": "list"})["jobs"], [])


class TestTC011ArranqueRechazado(unittest.TestCase):
    def arrancar(self, *opciones):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        r = subprocess.run(
            [sys.executable, "-m", "jobrunner.server", servidor.socket, *opciones],
            capture_output=True, text=True, env=entorno(), cwd=str(RAIZ), timeout=15,
        )
        return servidor, r

    def test_listen_en_todas_las_interfaces_o_en_una_direccion_publica_no_arranca(self):
        for destino in ("0.0.0.0:7070", "[::]:7070", "8.8.8.8:7070"):
            with self.subTest(listen=destino):
                servidor, r = self.arrancar("--listen", destino)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("no se puede escuchar", r.stderr)
                self.assertFalse(servidor.directorio.joinpath("jobrunner.sock").exists())

    def test_allow_abierto_o_publico_no_arranca(self):
        for red in ("0.0.0.0/0", "::/0", "8.8.8.0/24"):
            with self.subTest(allow=red):
                servidor, r = self.arrancar("--listen", "127.0.0.1:" + str(puerto_libre()), "--allow", red)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("red no permitida", r.stderr)
                self.assertFalse(servidor.directorio.joinpath("jobrunner.sock").exists())

    def test_sin_listen_no_se_abre_ningun_puerto(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        servidor.iniciar()
        self.assertNotIn("tcp=", servidor.directorio.joinpath("jobrunner.log").read_text())


if __name__ == "__main__":
    unittest.main()
