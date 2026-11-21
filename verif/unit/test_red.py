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
    permitidas = None   # None: las de por defecto (127.0.0.1 y ::1)

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

        self.red = red.Red(procesar, inactividad=self.inactividad, max_mensaje=self.max_mensaje,
                            permitidas=self.permitidas)
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


class RedAccesoRechazadoTest(RedBase):
    permitidas = [red.parsear_red("10.0.0.0/8")]   # sin loopback

    def test_origen_no_permitido_se_cierra_sin_leer_y_se_cuenta(self):
        c = self.cliente_tcp()   # llega desde 127.0.0.1, que aqui no esta permitido
        try:
            c.sendall(b"hola" + NL)
        except OSError:
            pass
        c.settimeout(3)
        try:
            self.assertEqual(c.recv(100), b"")
        except ConnectionResetError:
            pass   # tambien vale: el servidor cerro de golpe
        time.sleep(0.2)
        self.assertEqual(self.recibidas, [])
        self.assertEqual(self.red.rechazadas, 1)

    def test_el_socket_unix_no_pasa_por_la_lista_de_origenes(self):
        c = self.cliente_unix()
        c.sendall(b"hola" + NL)
        self.assertEqual(json.loads(leer_linea(c))["eco"], "hola")
        self.assertEqual(self.red.rechazadas, 0)

    def test_un_rechazo_no_afecta_al_servicio(self):
        for _ in range(5):
            try:
                self.cliente_tcp().sendall(b"x" + NL)
            except OSError:
                pass
        time.sleep(0.3)
        c = self.cliente_unix()
        c.sendall(b"sigo" + NL)
        self.assertEqual(json.loads(leer_linea(c))["eco"], "sigo")
        self.assertEqual(self.red.rechazadas, 5)


class RedAccesoPermitidoTest(RedBase):
    permitidas = [red.parsear_red("127.0.0.0/8")]

    def test_origen_dentro_de_la_red_permitida_es_atendido(self):
        c = self.cliente_tcp()
        c.sendall(b"hola" + NL)
        self.assertEqual(json.loads(leer_linea(c))["eco"], "hola")
        self.assertEqual(self.red.rechazadas, 0)


class RedesPermitidasTest(unittest.TestCase):
    def test_por_defecto_solo_127_0_0_1_y_loopback_ipv6(self):
        redes = red.redes_permitidas([])
        self.assertTrue(red.es_permitida("127.0.0.1", redes))
        self.assertTrue(red.es_permitida("::1", redes))
        self.assertFalse(red.es_permitida("127.0.0.2", redes))
        self.assertFalse(red.es_permitida("192.168.1.10", redes))
        self.assertFalse(red.es_permitida("8.8.8.8", redes))

    def test_allow_agrega_redes_y_conserva_el_loopback(self):
        redes = red.redes_permitidas(["192.168.1.0/24", "100.64.0.0/10"])
        self.assertTrue(red.es_permitida("127.0.0.1", redes))
        self.assertTrue(red.es_permitida("192.168.1.77", redes))
        self.assertTrue(red.es_permitida("100.101.102.103", redes))
        self.assertFalse(red.es_permitida("192.168.2.1", redes))
        self.assertFalse(red.es_permitida("100.128.0.1", redes))   # fuera de 100.64.0.0/10

    def test_una_ip_suelta_cuenta_como_red_de_un_solo_equipo(self):
        redes = red.redes_permitidas(["10.1.2.3"])
        self.assertTrue(red.es_permitida("10.1.2.3", redes))
        self.assertFalse(red.es_permitida("10.1.2.4", redes))

    def test_ipv4_mapeada_en_ipv6_y_ambito_se_normalizan(self):
        redes = red.redes_permitidas(["192.168.1.0/24"])
        self.assertTrue(red.es_permitida("::ffff:192.168.1.5", redes))
        self.assertTrue(red.es_permitida("::1%lo", redes))
        self.assertFalse(red.es_permitida("::ffff:8.8.8.8", redes))

    def test_direccion_que_no_es_ip_no_se_permite(self):
        self.assertFalse(red.es_permitida("no-es-ip", red.redes_permitidas([])))

    def test_redes_aceptables(self):
        for texto in ("10.0.0.0/8", "10.5.0.0/16", "172.16.0.0/12", "172.31.1.0/24", "192.168.0.0/16",
                      "100.64.0.0/10", "100.100.0.0/16", "127.0.0.1", "::1"):
            with self.subTest(red=texto):
                red.parsear_red(texto)

    def test_redes_rechazadas(self):
        for texto in ("0.0.0.0/0", "0.0.0.0", "::/0", "::", "8.8.8.0/24", "1.2.3.4", "172.32.0.0/16",
                      "100.128.0.0/10", "192.168.0.0/15", "10.0.0.0/7", "2001:db8::/32", "basura", "10.0.0.0/33", ""):
            with self.subTest(red=texto):
                with self.assertRaises(ValueError):
                    red.parsear_red(texto)

    def test_una_red_invalida_en_la_lista_impide_construirla(self):
        with self.assertRaises(ValueError):
            red.redes_permitidas(["192.168.1.0/24", "8.8.8.0/24"])


class ValidarEscuchaTest(unittest.TestCase):
    def test_direcciones_privadas_son_validas(self):
        for host in ("127.0.0.1", "localhost", "::1", "10.1.2.3", "172.16.5.5", "192.168.0.20", "100.101.102.103"):
            with self.subTest(host=host):
                red.validar_escucha(host)

    def test_todas_las_interfaces_y_las_publicas_se_rechazan(self):
        for host in ("0.0.0.0", "::", "8.8.8.8", "1.1.1.1", "172.32.0.1", "100.128.0.1", "2001:db8::1", ""):
            with self.subTest(host=host):
                with self.assertRaises(ValueError):
                    red.validar_escucha(host)

    def test_nombre_que_no_se_resuelve_se_rechaza(self):
        with self.assertRaises(ValueError):
            red.validar_escucha("este-nombre-no-existe.invalid")


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
