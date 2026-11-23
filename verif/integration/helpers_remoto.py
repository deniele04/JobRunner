"""Utilidades para las pruebas del cliente remoto: puerto libre, CLI real y servidor con --listen.

Solo se escucha en 127.0.0.1: nunca se abre un puerto a la red (regla de la entrega final).
"""
import socket
import subprocess
import sys
import time
import unittest

from helpers import RAIZ, ServidorDePrueba, entorno

ROYITO = RAIZ / "scripts" / "royito"


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto


def esperar_puerto(puerto, limite=10.0):
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        try:
            socket.create_connection(("127.0.0.1", puerto), timeout=1).close()
            return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("el puerto %d no abrio en %.0f s" % (puerto, limite))


def royito(*args, env_extra=None, comando=None):
    """Ejecuta el CLI real. Devuelve (codigo, stdout, stderr)."""
    env = entorno()
    env.update(env_extra or {})
    orden = [sys.executable, "-m", "jobrunner.cli"] if comando is None else [str(comando)]
    r = subprocess.run(orden + list(args), capture_output=True, text=True, env=env,
                       cwd=str(RAIZ), timeout=30)
    return r.returncode, r.stdout, r.stderr


class ClienteRemotoBase(unittest.TestCase):
    opciones_extra = ()

    def setUp(self):
        self.servidor = ServidorDePrueba()
        self.addCleanup(self.servidor.limpiar)
        self.puerto = puerto_libre()
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto),
                                        *self.opciones_extra])
        esperar_puerto(self.puerto)

    def tcp(self, *args, **kwargs):
        return royito("--host", "127.0.0.1", "--port", str(self.puerto), *args, **kwargs)
