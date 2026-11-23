"""TC-012 (J6, ADR-0009): mensajes fragmentados y desconexiones en red (RF-21, RF-22, RNF-14, RNF-24).

Servidor real, por TCP en 127.0.0.1 (y por el socket Unix cuando conviene): un mensaje en
pedazos, varias solicitudes en una conexion, un mensaje de mas de 64 KiB y un cliente que se
va a la mitad o sin leer la respuesta.
"""
import json
import socket
import threading
import time
import unittest

from helpers import ServidorDePrueba

NL = bytes([10])
MAXIMO = 64 * 1024


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto


def leer_lineas(sock, cuantas, limite=8.0):
    sock.settimeout(limite)
    datos = b""
    while datos.count(NL) < cuantas:
        trozo = sock.recv(65536)
        if not trozo:
            break
        datos += trozo
    return [json.loads(x) for x in datos.split(NL) if x]


class PruebaDeRed(unittest.TestCase):
    def setUp(self):
        self.servidor = ServidorDePrueba()
        self.addCleanup(self.servidor.limpiar)
        self.puerto = puerto_libre()
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto)])

    def tcp(self):
        c = socket.create_connection(("127.0.0.1", self.puerto), timeout=5)
        self.addCleanup(c.close)
        return c

    def unix(self):
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(5)
        c.connect(self.servidor.socket)
        self.addCleanup(c.close)
        return c

    def conexiones(self):
        return (("tcp", self.tcp), ("unix", self.unix))

    def bitacora(self):
        return self.servidor.directorio.joinpath("jobrunner.log").read_text()


class TestTC012MensajesEnRed(PruebaDeRed):

    def test_un_mensaje_en_pedazos_se_reensambla_y_se_procesa_una_vez(self):
        for nombre, abrir in self.conexiones():
            with self.subTest(transporte=nombre):
                c = abrir()
                for pedazo in (b'{"cmd": "su', b'bmit", "argv"', b': ["true"]}', NL):
                    c.sendall(pedazo)
                    time.sleep(0.15)
                respuesta = leer_lineas(c, 1)[0]
                self.assertEqual(respuesta["v"], 1)
                self.assertIn("id", respuesta)
        self.assertEqual(len(self.servidor.listar()), 2)   # un trabajo por transporte, no mas

    def test_un_mensaje_enviado_byte_a_byte_se_procesa(self):
        c = self.tcp()
        for byte in b'{"cmd": "list"}' + NL:
            c.sendall(bytes([byte]))
        self.assertEqual(leer_lineas(c, 1)[0], {"v": 1, "jobs": []})

    def test_dos_solicitudes_en_una_conexion_se_responden_en_orden(self):
        for nombre, abrir in self.conexiones():
            with self.subTest(transporte=nombre):
                c = abrir()
                c.sendall(b'{"cmd": "submit", "argv": ["sleep", "300"]}' + NL)
                primera = leer_lineas(c, 1)[0]
                c.sendall(b'{"cmd": "list"}' + NL)
                segunda = leer_lineas(c, 1)[0]
                self.assertIn("id", primera)
                self.assertIn(primera["id"], [t["id"] for t in segunda["jobs"]])

    def test_varias_solicitudes_pegadas_en_un_solo_envio(self):
        c = self.tcp()
        c.sendall(b'{"cmd": "list"}' + NL + b'{"cmd": "nada"}' + NL + b'{"cmd": "list"}' + NL)
        r1, r2, r3 = leer_lineas(c, 3)
        self.assertEqual(r1["jobs"], [])
        self.assertIn("comando desconocido", r2["error"])
        self.assertEqual(r3["jobs"], [])

    def test_mensaje_de_mas_de_64_kib_sin_salto_de_linea_recibe_error_y_se_cierra(self):
        c = self.tcp()
        c.sendall(b"x" * (MAXIMO + 100))
        respuesta = leer_lineas(c, 1)[0]
        self.assertEqual(respuesta["v"], 1)
        self.assertIn("mensaje demasiado grande", respuesta["error"])
        c.settimeout(5)
        self.assertEqual(c.recv(10), b"")   # el servidor cerro la conexion
        self.assertIn("mensaje demasiado grande", self.bitacora())
        self.assertEqual(self.servidor.listar(), [])   # y el servicio sigue sirviendo
        self.assertEqual(self.servidor.cli_json("list")[0], 0)

    def test_linea_completa_de_mas_de_64_kib_tambien_se_rechaza(self):
        for nombre, abrir in self.conexiones():
            with self.subTest(transporte=nombre):
                c = abrir()
                c.sendall(b"y" * (MAXIMO + 1) + NL)
                self.assertIn("mensaje demasiado grande", leer_lineas(c, 1)[0]["error"])

    def test_un_mensaje_de_exactamente_64_kib_si_se_procesa(self):
        base = json.dumps({"cmd": "list", "relleno": ""})
        relleno = "z" * (MAXIMO - len(base))
        mensaje = json.dumps({"cmd": "list", "relleno": relleno}).encode("utf-8")
        self.assertEqual(len(mensaje), MAXIMO)
        c = self.tcp()
        c.sendall(mensaje + NL)
        self.assertEqual(leer_lineas(c, 1)[0]["jobs"], [])

    def test_cliente_que_se_va_a_la_mitad_no_crea_trabajos_y_el_servicio_sigue(self):
        for nombre, abrir in self.conexiones():
            with self.subTest(transporte=nombre):
                c = abrir()
                c.sendall(b'{"cmd": "submit", "argv": ["sleep", "300"')   # sin cerrar el JSON ni el salto
                time.sleep(0.2)
                c.close()
        time.sleep(0.5)
        self.assertEqual(self.servidor.listar(), [])
        self.assertIn("solicitud incompleta", self.bitacora())
        self.assertEqual(self.servidor.cli_json("list")[0], 0)

    def test_cliente_que_se_va_sin_leer_la_respuesta_la_solicitud_se_aplica_una_vez(self):
        pedido = {"cmd": "submit", "argv": ["sleep", "300"], "request_id": "red-1"}
        c = self.tcp()
        c.sendall(json.dumps(pedido).encode("utf-8") + NL)
        c.close()   # se va sin leer la respuesta
        time.sleep(0.5)
        c2 = self.tcp()
        c2.sendall(json.dumps(pedido).encode("utf-8") + NL)
        reenvio = leer_lineas(c2, 1)[0]
        self.assertTrue(reenvio["duplicado"])
        self.assertEqual(len(self.servidor.listar()), 1)

    def test_un_cliente_conectado_que_no_envia_nada_no_retrasa_a_los_demas(self):
        ocioso = self.tcp()
        inicio = time.monotonic()
        codigo, respuesta = self.servidor.cli_json("list")
        self.assertEqual(codigo, 0)
        self.assertLess(time.monotonic() - inicio, 3.0)
        ocioso.sendall(b'{"cmd": "list"}' + NL)   # y el ocioso sigue siendo atendido cuando habla
        self.assertEqual(leer_lineas(ocioso, 1)[0]["jobs"], [])

    def test_veinte_clientes_a_la_vez_reciben_cada_uno_su_respuesta(self):
        resultados = []

        def cliente(numero):
            with socket.create_connection(("127.0.0.1", self.puerto), timeout=10) as c:
                pedido = {"cmd": "submit", "argv": ["true"], "request_id": "multi-" + str(numero)}
                c.sendall(json.dumps(pedido).encode("utf-8") + NL)
                resultados.append(leer_lineas(c, 1)[0])

        hilos = [threading.Thread(target=cliente, args=(i,)) for i in range(20)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(timeout=20)
        self.assertEqual(len(resultados), 20)   # ninguno se quedo sin respuesta
        self.assertTrue(all(r["v"] == 1 for r in resultados))
        aceptados = [r for r in resultados if r.get("id")]
        rechazados = [r for r in resultados if r.get("error")]
        self.assertEqual(len(aceptados) + len(rechazados), 20)
        self.assertTrue(all("cola llena" in r["error"] for r in rechazados))   # la cola es de 10
        self.assertEqual(len({r["id"] for r in aceptados}), len(aceptados))   # trabajos distintos
        self.assertGreaterEqual(len(aceptados), 10)


if __name__ == "__main__":
    unittest.main()
