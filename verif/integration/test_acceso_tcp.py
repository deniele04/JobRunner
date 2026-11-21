"""Restriccion de acceso por red (J3, ADR-0008): --listen valida el destino y --allow filtra el origen.

Sin salir de la maquina: el servidor escucha en 127.0.0.1 y el cliente se conecta desde
127.0.0.1 (permitido) o desde 127.0.0.2 (otra direccion de loopback, no permitida por defecto).
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


def pedir_desde(origen, puerto, pedido, limite=5.0):
    """Envia una solicitud desde la direccion `origen`. Devuelve el dict, o None si el servidor cerro."""
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
    except (ConnectionResetError, BrokenPipeError):
        return None
    finally:
        c.close()
    return json.loads(datos) if datos else None


class AccesoPorDefectoTest(unittest.TestCase):
    def setUp(self):
        self.servidor = ServidorDePrueba()
        self.addCleanup(self.servidor.limpiar)
        self.puerto = puerto_libre()
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto)])

    def bitacora(self):
        return self.servidor.directorio.joinpath("jobrunner.log").read_text()

    def test_loopback_si_y_otro_origen_no(self):
        self.assertEqual(pedir_desde("127.0.0.1", self.puerto, {"cmd": "list"}), {"jobs": []})
        self.assertIsNone(pedir_desde("127.0.0.2", self.puerto, {"cmd": "list"}))

    def test_el_rechazo_se_registra_con_la_ip_y_no_se_crea_trabajo(self):
        pedir_desde("127.0.0.2", self.puerto, {"cmd": "submit", "argv": ["sleep", "300"]})
        time.sleep(0.3)
        self.assertIn("acceso_rechazado", self.bitacora())
        self.assertIn("ip=127.0.0.2", self.bitacora())
        self.assertEqual(pedir_desde("127.0.0.1", self.puerto, {"cmd": "list"}), {"jobs": []})

    def test_el_servidor_sigue_atendiendo_despues_de_muchos_rechazos(self):
        for _ in range(20):
            self.assertIsNone(pedir_desde("127.0.0.2", self.puerto, {"cmd": "list"}))
        codigo, respuesta = self.servidor.cli_json("list")
        self.assertEqual(codigo, 0)
        self.assertEqual(respuesta, {"jobs": []})

    def test_el_socket_unix_no_depende_de_allow(self):
        codigo, _ = self.servidor.cli_json("list")
        self.assertEqual(codigo, 0)

    def test_el_resumen_de_inicio_muestra_los_origenes_permitidos(self):
        self.assertIn("permitidas=127.0.0.1/32,::1/128", self.bitacora())


class AccesoConAllowTest(unittest.TestCase):
    def iniciar(self, *allow):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        puerto = puerto_libre()
        opciones = ["--listen", "127.0.0.1:" + str(puerto)]
        for red in allow:
            opciones += ["--allow", red]
        servidor.iniciar(opciones=opciones)
        return servidor, puerto

    def test_allow_con_una_ip_deja_pasar_solo_a_esa(self):
        _, puerto = self.iniciar("127.0.0.2")
        self.assertEqual(pedir_desde("127.0.0.2", puerto, {"cmd": "list"}), {"jobs": []})
        self.assertEqual(pedir_desde("127.0.0.1", puerto, {"cmd": "list"}), {"jobs": []})   # loopback siempre
        self.assertIsNone(pedir_desde("127.0.0.3", puerto, {"cmd": "list"}))

    def test_allow_con_cidr_cubre_todo_el_rango(self):
        _, puerto = self.iniciar("127.0.0.0/24")
        for origen in ("127.0.0.2", "127.0.0.77"):
            self.assertEqual(pedir_desde(origen, puerto, {"cmd": "list"}), {"jobs": []})
        self.assertIsNone(pedir_desde("127.0.1.1", puerto, {"cmd": "list"}))

    def test_allow_repetido_suma_redes(self):
        _, puerto = self.iniciar("127.0.0.2", "127.0.0.3")
        self.assertEqual(pedir_desde("127.0.0.2", puerto, {"cmd": "list"}), {"jobs": []})
        self.assertEqual(pedir_desde("127.0.0.3", puerto, {"cmd": "list"}), {"jobs": []})
        self.assertIsNone(pedir_desde("127.0.0.4", puerto, {"cmd": "list"}))

    def test_un_cliente_permitido_puede_enviar_y_cancelar(self):
        _, puerto = self.iniciar("127.0.0.2")
        trabajo = pedir_desde("127.0.0.2", puerto, {"cmd": "submit", "argv": ["sleep", "300"]})
        self.assertEqual(trabajo["state"], "RUNNING")
        cancelado = pedir_desde("127.0.0.2", puerto, {"cmd": "cancel", "id": trabajo["id"]})
        self.assertIn(cancelado["state"], ("CANCELED", "RUNNING"))


class ArranqueRechazadoTest(unittest.TestCase):
    def arrancar(self, *opciones):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        resultado = subprocess.run(
            [sys.executable, "-m", "jobrunner.server", servidor.socket, *opciones],
            capture_output=True, text=True, env=entorno(), cwd=str(RAIZ), timeout=15,
        )
        return servidor, resultado

    def comprobar_rechazo(self, opciones, fragmento):
        servidor, r = self.arrancar(*opciones)
        self.assertNotEqual(r.returncode, 0, "debio negarse a arrancar con " + " ".join(opciones))
        self.assertIn(fragmento, r.stderr)
        self.assertFalse(servidor.directorio.joinpath("jobrunner.sock").exists())

    def test_listen_en_todas_las_interfaces_no_arranca(self):
        for destino in ("0.0.0.0:7070", "[::]:7070"):
            with self.subTest(listen=destino):
                self.comprobar_rechazo(["--listen", destino], "abriria el servicio a cualquier red")

    def test_listen_en_una_direccion_publica_no_arranca(self):
        for destino in ("8.8.8.8:7070", "1.1.1.1:7070", "172.32.0.1:7070"):
            with self.subTest(listen=destino):
                self.comprobar_rechazo(["--listen", destino], "no es privada")

    def test_allow_publico_o_abierto_no_arranca(self):
        for red in ("0.0.0.0/0", "::/0", "0.0.0.0", "8.8.8.0/24", "192.168.0.0/15"):
            with self.subTest(allow=red):
                self.comprobar_rechazo(["--listen", "127.0.0.1:" + str(puerto_libre()), "--allow", red],
                                       "red no permitida")

    def test_allow_mal_escrito_no_arranca(self):
        self.comprobar_rechazo(["--listen", "127.0.0.1:" + str(puerto_libre()), "--allow", "basura"],
                               "red invalida")

    def test_allow_sin_listen_es_un_error_de_uso(self):
        servidor, r = self.arrancar("--allow", "192.168.1.0/24")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--allow solo tiene efecto con --listen", r.stderr)

    def test_un_allow_invalido_gana_aunque_el_listen_sea_valido(self):
        servidor, r = self.arrancar("--listen", "127.0.0.1:" + str(puerto_libre()),
                                    "--allow", "192.168.1.0/24", "--allow", "8.8.8.0/24")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
