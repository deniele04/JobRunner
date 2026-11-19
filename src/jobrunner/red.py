"""Capa de red del servidor (ADR-0008, ADR-0009).

Atiende varias conexiones a la vez en un solo hilo con `selectors`: un bufer por
conexion, mensajes JSON delimitados por salto de linea, varias solicitudes por
conexion respondidas en orden, tamano maximo por mensaje y cierre por
inactividad. Sirve igual a los clientes del socket Unix y a los de TCP.

Cada solicitud completa se procesa de una vez con el callback `procesar`, que
llama al gestor de trabajos; los estados siguen cambiando en un solo hilo y en un
solo lugar, asi que no hacen falta candados (ADR-0007).

Solo biblioteca estandar (ADR-0001).
"""
import json
import selectors
import socket
import time

from . import bitacora

MAX_MENSAJE = 64 * 1024   # bytes por mensaje (ADR-0009, regla 4)
INACTIVIDAD = 30.0        # segundos sin datos antes de cerrar la conexion (regla 5)
_LECTURA = 65536


def parsear_direccion(texto):
    """Convierte 'HOST:PUERTO' o '[IPv6]:PUERTO' en (host, puerto). ValueError si es invalida."""
    if not texto:
        raise ValueError("falta la direccion; usa HOST:PUERTO")
    if texto.startswith("["):
        fin = texto.find("]")
        if fin == -1 or texto[fin + 1:fin + 2] != ":":
            raise ValueError("direccion invalida: " + texto + " (usa [IPv6]:PUERTO)")
        host, puerto = texto[1:fin], texto[fin + 2:]
    else:
        host, separador, puerto = texto.rpartition(":")
        if not separador or not host:
            raise ValueError("direccion invalida: " + texto + " (usa HOST:PUERTO)")
    try:
        numero = int(puerto)
    except ValueError:
        raise ValueError("puerto invalido: " + puerto)
    if not 0 <= numero <= 65535:
        raise ValueError("puerto fuera de rango: " + puerto)
    return host, numero


def abrir_tcp(host, puerto):
    """Abre un socket TCP de escucha en host:puerto."""
    familia = socket.AF_INET6 if ":" in host else socket.AF_INET
    sock = socket.socket(familia, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, puerto))
        sock.listen(128)
    except OSError:
        sock.close()
        raise
    return sock


class _Conexion:
    def __init__(self, sock, origen):
        self.sock = sock
        self.origen = origen
        self.entrada = bytearray()
        self.salida = bytearray()
        self.ultima = time.monotonic()
        self.eventos = selectors.EVENT_READ
        self.abierta = True


class Red:
    """Multiplexor de conexiones. `procesar(linea: bytes)` devuelve el dict de respuesta."""

    def __init__(self, procesar, inactividad=INACTIVIDAD, max_mensaje=MAX_MENSAJE):
        self._procesar = procesar
        self._inactividad = inactividad
        self._max = max_mensaje
        self._sel = selectors.DefaultSelector()
        self._conexiones = set()
        self._escuchas = []

    # -- uso desde el servidor -------------------------------------------
    def escuchar(self, sock):
        """Registra un socket de escucha (Unix o TCP) ya enlazado."""
        sock.setblocking(False)
        self._escuchas.append(sock)
        self._sel.register(sock, selectors.EVENT_READ, None)

    def atender(self, espera):
        """Un paso del ciclo: espera hasta `espera` s y atiende lo que haya."""
        for clave, mascara in self._sel.select(espera):
            con = clave.data
            if con is None:
                self._aceptar(clave.fileobj)
                continue
            if not con.abierta:
                continue
            if mascara & selectors.EVENT_READ:
                self._leer(con)
            if con.abierta and mascara & selectors.EVENT_WRITE:
                self._escribir(con)
        self._cerrar_inactivas()

    def cerrar(self):
        """Cierra todas las conexiones y los sockets de escucha."""
        for con in list(self._conexiones):
            self._cerrar(con)
        for sock in self._escuchas:
            try:
                self._sel.unregister(sock)
            except (KeyError, ValueError):
                pass
            sock.close()
        self._escuchas = []
        self._sel.close()

    # -- internos ----------------------------------------------------------
    def _aceptar(self, escucha):
        while True:
            try:
                sock, direccion = escucha.accept()
            except (BlockingIOError, InterruptedError):
                return
            except OSError as e:
                bitacora.error("error_interno", motivo="accept: " + str(e))
                return
            sock.setblocking(False)
            origen = direccion[0] if isinstance(direccion, tuple) else "unix"
            con = _Conexion(sock, origen)
            self._conexiones.add(con)
            self._sel.register(sock, selectors.EVENT_READ, con)

    def _leer(self, con):
        try:
            datos = con.sock.recv(_LECTURA)
        except (BlockingIOError, InterruptedError):
            return
        except OSError:
            self._cerrar(con)
            return
        if not datos:
            if con.entrada.strip():
                # Solicitud sin salto de linea al cerrarse la conexion: no tiene efecto (ADR-0007).
                bitacora.error("solicitud_invalida", motivo="solicitud incompleta")
            self._cerrar(con)
            return
        con.ultima = time.monotonic()
        con.entrada += datos
        while con.abierta:
            fin = con.entrada.find(b"\n")
            if fin == -1:
                break
            linea = bytes(con.entrada[:fin])
            del con.entrada[:fin + 1]
            if len(linea) > self._max:
                self._rechazar_grande(con)
                return
            if not linea.strip():
                continue
            self._responder(con, self._procesar(linea))
        if con.abierta and len(con.entrada) > self._max:
            self._rechazar_grande(con)

    def _responder(self, con, respuesta):
        con.salida += (json.dumps(respuesta) + "\n").encode("utf-8")
        self._escribir(con)

    def _escribir(self, con):
        while con.salida:
            try:
                enviados = con.sock.send(con.salida)
            except (BlockingIOError, InterruptedError):
                break
            except OSError:
                bitacora.error("cliente_desconectado",
                               motivo="el cliente cerro antes de recibir la respuesta")
                self._cerrar(con)
                return
            del con.salida[:enviados]
            con.ultima = time.monotonic()
        eventos = selectors.EVENT_READ | (selectors.EVENT_WRITE if con.salida else 0)
        if eventos != con.eventos:
            con.eventos = eventos
            self._sel.modify(con.sock, eventos, con)

    def _rechazar_grande(self, con):
        bitacora.error("solicitud_invalida", motivo="mensaje demasiado grande",
                       maximo=self._max, origen=con.origen)
        aviso = {"error": "mensaje demasiado grande (maximo " + str(self._max) + " bytes)"}
        try:
            con.sock.send((json.dumps(aviso) + "\n").encode("utf-8"))
        except OSError:
            pass
        self._cerrar(con)

    def _cerrar_inactivas(self):
        limite = time.monotonic() - self._inactividad
        for con in list(self._conexiones):
            if con.ultima < limite:
                bitacora.evento("conexion_inactiva", motivo="sin datos", origen=con.origen)
                self._cerrar(con)

    def _cerrar(self, con):
        if not con.abierta:
            return
        con.abierta = False
        self._conexiones.discard(con)
        try:
            self._sel.unregister(con.sock)
        except (KeyError, ValueError):
            pass
        con.sock.close()
