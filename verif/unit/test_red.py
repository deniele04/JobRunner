"""Capa de red del servidor (J2, ADR-0009): Red con selectors, probada en el mismo proceso.

Levanta la clase `Red` con un `procesar` de juguete en un hilo y le habla por un
socket Unix y por TCP en localhost. No usa el gestor de trabajos.
"""
import json
import os
import socket
import tempfile
import threading
import time
import unittest

from jobrunner import red

NL = bytes([10])
GRANDE = 12 * 1024 * 1024   # mayor que los buffers del kernel en loopback


def linea(obj):
    return json.dumps(obj).encode("utf-8") + NL


def leer_linea(sock, limite=5.0):
    sock.settimeout(limite)
    datos = b""
    while not datos.endswith(NL):
        trozo = sock.recv(65536)
        if not trozo:
            break
        datos += trozo
    return datos


class RedBase(unittest.TestCase):
    max_mensaje = red.MAX_MENSAJE
    inactividad = red.INACTIVIDAD

    def setUp(self):
        self.recibidas = []
        self._tmp = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self._tmp.name, "r.sock")

        def procesar(datos):
            self.recibidas.append(datos)
            texto = datos.decode("utf-8", "replace")
            if texto == "grande":
                return {"datos": "x" * (GRANDE)}
            return {"eco": texto}

        self.red = red.Red(procesar, inactividad=self.inactividad, max_mensaje=self.max_mensaje)
        self.unix = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.unix.bind(self.ruta)
        self.unix.listen(16)
        self.red.escuchar(self.unix)
        self.tcp = red.abrir_tcp("127.0.0.1", 0)
        self.puerto = self.tcp.getsockname()[1]
        self.red.escuchar(self.tcp)

        self.activo = True
        self.hilo = threading.Thread(target=self._ciclo, daemon=True)
        self.hilo.start()
        self.addCleanup(self._detener)

    def _ciclo(self):
        while self.activo:
            self.red.atender(0.05)

    def _detener(self):
        self.activo = False
        self.hilo.join(timeout=5)
        self.red.cerrar()
        self._tmp.cleanup()

    def cliente_unix(self):
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.connect(self.ruta)
        self.addCleanup(c.close)
        return c

    def cliente_tcp(self):
        c = socket.create_connection(("127.0.0.1", self.puerto), timeout=5)
        self.addCleanup(c.close)
        return c


class RedTest(RedBase):
    def test_responde_por_unix_y_por_tcp(self):
        for cliente in (self.cliente_unix(), self.cliente_tcp()):
            cliente.sendall(b"hola" + NL)
            self.assertEqual(json.loads(leer_linea(cliente)), {"eco": "hola"})

    def test_dos_solicitudes_en_una_conexion_se_responden_en_orden(self):
        c = self.cliente_tcp()
        c.sendall(b"uno" + NL + b"dos" + NL + b"tres" + NL)
        respuestas = []
        buffer = b""
        c.settimeout(5)
        while len(respuestas) < 3:
            buffer += c.recv(4096)
            while NL in buffer:
                una, buffer = buffer.split(NL, 1)
                respuestas.append(json.loads(una)["eco"])
        self.assertEqual(respuestas, ["uno", "dos", "tres"])

    def test_mensaje_fragmentado_se_reensambla(self):
        c = self.cliente_unix()
        for pedazo in (b'{"cmd":', b' "li', b'st"}', NL):
            c.sendall(pedazo)
            time.sleep(0.1)
        self.assertEqual(json.loads(leer_linea(c)), {"eco": '{"cmd": "list"}'})
        self.assertEqual(self.recibidas, [b'{"cmd": "list"}'])

    def test_cliente_conectado_sin_enviar_no_retrasa_a_los_demas(self):
        lento = self.cliente_tcp()   # conecta y no envia nada
        inicio = time.monotonic()
        rapido = self.cliente_unix()
        rapido.sendall(b"rapido" + NL)
        self.assertEqual(json.loads(leer_linea(rapido, 2))["eco"], "rapido")
        self.assertLess(time.monotonic() - inicio, 1.0)
        lento.sendall(b"tarde" + NL)   # el lento sigue siendo atendido cuando envia
        self.assertEqual(json.loads(leer_linea(lento))["eco"], "tarde")

    def test_lineas_en_blanco_se_ignoran(self):
        c = self.cliente_unix()
        c.sendall(NL + b"   " + NL + b"x" + NL)
        self.assertEqual(json.loads(leer_linea(c))["eco"], "x")
        self.assertEqual(self.recibidas, [b"x"])

    def test_solicitud_incompleta_al_cerrar_no_se_procesa(self):
        c = self.cliente_unix()
        c.sendall(b'{"cmd": "submit"')
        c.close()
        time.sleep(0.5)
        self.assertEqual(self.recibidas, [])

    def test_respuesta_enorme_a_un_cliente_que_no_lee_no_bloquea_a_los_demas(self):
        sordo = self.cliente_tcp()
        sordo.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        sordo.sendall(b"grande" + NL)   # la respuesta (3 MiB) no cabe en los bufers
        time.sleep(0.3)
        otro = self.cliente_unix()
        otro.sendall(b"vivo" + NL)
        self.assertEqual(json.loads(leer_linea(otro, 2))["eco"], "vivo")
        # al empezar a leer, el sordo recibe la respuesta completa
        total = b""
        sordo.settimeout(10)
        while not total.endswith(NL):
            total += sordo.recv(65536)
        self.assertEqual(len(json.loads(total)["datos"]), GRANDE)

    def test_cliente_que_se_va_sin_leer_la_respuesta_no_tumba_la_red(self):
        c = self.cliente_tcp()
        c.sendall(b"grande" + NL)
        c.close()
        time.sleep(0.5)
        otro = self.cliente_unix()
        otro.sendall(b"sigo" + NL)
        self.assertEqual(json.loads(leer_linea(otro))["eco"], "sigo")


class RedLimiteDeTamanoTest(RedBase):
    max_mensaje = 1000

    def test_mensaje_sin_salto_de_linea_mayor_al_maximo_recibe_error_y_se_cierra(self):
        c = self.cliente_tcp()
        c.sendall(b"a" * 1500)
        respuesta = json.loads(leer_linea(c))
        self.assertIn("demasiado grande", respuesta["error"])
        self.assertEqual(c.recv(10), b"")   # el servidor cerro la conexion
        self.assertEqual(self.recibidas, [])

    def test_linea_completa_mayor_al_maximo_tambien_se_rechaza(self):
        c = self.cliente_unix()
        c.sendall(b"b" * 2000 + NL)
        self.assertIn("demasiado grande", json.loads(leer_linea(c))["error"])
        self.assertEqual(self.recibidas, [])

    def test_mensaje_justo_en_el_maximo_si_se_procesa(self):
        c = self.cliente_unix()
        c.sendall(b"c" * 1000 + NL)
        self.assertEqual(len(json.loads(leer_linea(c))["eco"]), 1000)


class RedInactividadTest(RedBase):
    inactividad = 0.4

    def test_conexion_inactiva_se_cierra(self):
        c = self.cliente_tcp()
        c.settimeout(5)
        inicio = time.monotonic()
        self.assertEqual(c.recv(10), b"")
        self.assertGreaterEqual(time.monotonic() - inicio, 0.3)

    def test_conexion_con_actividad_no_se_cierra(self):
        c = self.cliente_unix()
        for _ in range(4):
            time.sleep(0.2)
            c.sendall(b"ping" + NL)
            self.assertEqual(json.loads(leer_linea(c))["eco"], "ping")


class ParsearDireccionTest(unittest.TestCase):
    def test_direcciones_validas(self):
        self.assertEqual(red.parsear_direccion("127.0.0.1:7070"), ("127.0.0.1", 7070))
        self.assertEqual(red.parsear_direccion("localhost:80"), ("localhost", 80))
        self.assertEqual(red.parsear_direccion("[::1]:7070"), ("::1", 7070))
        self.assertEqual(red.parsear_direccion("100.64.0.5:0"), ("100.64.0.5", 0))

    def test_direcciones_invalidas(self):
        for texto in ("", "7070", ":7070", "host:", "host:abc", "host:70000", "[::1]7070", "[::1:7070"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    red.parsear_direccion(texto)


if __name__ == "__main__":
    unittest.main()
