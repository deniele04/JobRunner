"""TC-009 con TCP (J5, ADR-0006 y ADR-0008): cierre controlado con el puerto de red abierto.

Con Ctrl+C o SIGTERM el servicio debe dejar de aceptar conexiones TCP, cerrar las que
estan abiertas, liberar el puerto y despues cancelar los trabajos como siempre; sin dejar
procesos, conexiones ni el puerto ocupado.
"""
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import unittest

from helpers import ServidorDePrueba
from test_tc009_cierre_controlado import IGNORA_SIGTERM, matar_grupos, procesos

NL = bytes([10])


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto


def puerto_en_escucha(puerto):
    """True/False segun `ss -ltn`; None si no hay `ss` en el sistema."""
    if shutil.which("ss") is None:
        return None
    salida = subprocess.run(["ss", "-ltn"], capture_output=True, text=True, timeout=10).stdout
    return any(linea.split()[3:4] and linea.split()[3].endswith(":" + str(puerto))
               for linea in salida.splitlines())


def pedir_tcp(puerto, pedido):
    import json
    with socket.create_connection(("127.0.0.1", puerto), timeout=5) as c:
        c.sendall(json.dumps(pedido).encode("utf-8") + NL)
        datos = b""
        while not datos.endswith(NL):
            trozo = c.recv(65536)
            if not trozo:
                break
            datos += trozo
    return json.loads(datos)


class PruebaDeCierreTcp(unittest.TestCase):
    def setUp(self):
        fd, self.base = tempfile.mkstemp(prefix="jobrunner-base-")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self.base) and os.remove(self.base))
        procesos("guardar", self.base)
        self.servidor = ServidorDePrueba()
        self.addCleanup(self.servidor.limpiar)
        self.puerto = puerto_libre()
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto)])

    def sin_huerfanos(self, patron):
        codigo, salida = procesos("revisar", "--base", self.base, "--patron", patron)
        self.addCleanup(matar_grupos, salida)
        self.assertEqual(codigo, 0, salida)

    def clientes_abiertos(self, cuantos=3):
        clientes = []
        for _ in range(cuantos):
            c = socket.create_connection(("127.0.0.1", self.puerto), timeout=5)
            self.addCleanup(c.close)
            clientes.append(c)
        return clientes

    def bitacora(self):
        return self.servidor.directorio.joinpath("jobrunner.log").read_text()


class TestTC009CierreTcp(PruebaDeCierreTcp):

    def test_ctrl_c_libera_el_puerto_y_no_quedan_conexiones_en_escucha(self):
        self.assertIn(puerto_en_escucha(self.puerto), (True, None))
        self.servidor.detener()
        self.assertEqual(self.servidor.proceso.returncode, 0)
        self.assertIn(puerto_en_escucha(self.puerto), (False, None), "ss -ltn aun muestra el puerto")
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", self.puerto), timeout=2).close()
        libre = socket.socket()
        libre.bind(("127.0.0.1", self.puerto))   # se puede volver a usar el puerto
        libre.close()

    def test_sigterm_tambien_libera_el_puerto(self):
        self.servidor.detener(senal=signal.SIGTERM)
        self.assertEqual(self.servidor.proceso.returncode, 0)
        self.assertIn(puerto_en_escucha(self.puerto), (False, None))
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", self.puerto), timeout=2).close()

    def test_las_conexiones_abiertas_se_cierran_al_cerrar(self):
        clientes = self.clientes_abiertos(3)
        clientes[0].sendall(b'{"cmd": "list"}' + NL)   # una ya hizo una solicitud
        clientes[0].recv(4096)
        unix = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        unix.connect(self.servidor.socket)
        self.addCleanup(unix.close)
        self.servidor.detener()
        for c in clientes + [unix]:
            c.settimeout(3)
            self.assertEqual(c.recv(10), b"", "una conexion quedo abierta tras el cierre")

    def test_el_cierre_de_la_red_no_espera_a_que_mueran_los_trabajos(self):
        # Un trabajo que ignora SIGTERM alarga el cierre unos 5 s; la red debe cerrarse al inicio.
        self.servidor.enviar("--", "sh", "-c", IGNORA_SIGTERM)
        clientes = self.clientes_abiertos(2)
        time.sleep(0.3)
        self.servidor.proceso.send_signal(signal.SIGINT)
        inicio = time.monotonic()
        for c in clientes:
            c.settimeout(3)
            self.assertEqual(c.recv(10), b"")
        self.assertLess(time.monotonic() - inicio, 2.0, "las conexiones tardaron en cerrarse")
        self.assertIsNone(self.servidor.proceso.poll(), "el servidor debia seguir cancelando el trabajo")
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", self.puerto), timeout=2).close()
        self.assertIn(puerto_en_escucha(self.puerto), (False, None))
        self.servidor.proceso.wait(timeout=12)
        self.sin_huerfanos("sleep 1|while")

    def test_trabajos_enviados_por_tcp_se_cancelan_sin_huerfanos(self):
        trabajo = pedir_tcp(self.puerto, {"cmd": "submit", "argv": ["sleep", "310"]})
        self.assertEqual(trabajo["state"], "RUNNING")
        self.servidor.detener()
        self.sin_huerfanos("sleep 310")
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto)])
        self.assertEqual(self.servidor.estado(trabajo["id"])["state"], "CANCELED")

    def test_se_conserva_la_cola_de_los_trabajos_enviados_por_tcp(self):
        self.servidor.detener()
        self.servidor.iniciar(opciones=["--max-jobs", "1", "--listen", "127.0.0.1:" + str(self.puerto)])
        primero = pedir_tcp(self.puerto, {"cmd": "submit", "argv": ["sleep", "311"]})
        segundo = pedir_tcp(self.puerto, {"cmd": "submit", "argv": ["sh", "-c", "exit 0"]})
        self.assertEqual(segundo["state"], "QUEUED")
        self.servidor.detener()
        self.sin_huerfanos("sleep 311")
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto)])
        self.assertEqual(self.servidor.estado(primero["id"])["state"], "CANCELED")
        self.assertEqual(self.servidor.esperar_estado_final(segundo["id"])["state"], "SUCCEEDED")

    def test_se_puede_reiniciar_en_el_mismo_puerto_de_inmediato_con_clientes_conectados(self):
        self.clientes_abiertos(3)
        self.servidor.detener()
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto)])
        self.assertEqual(pedir_tcp(self.puerto, {"cmd": "list"})["jobs"], [])

    def test_una_solicitud_a_medias_no_crea_trabajos(self):
        c = self.clientes_abiertos(1)[0]
        c.sendall(b'{"cmd": "submit", "argv": ["sleep", "312"')   # sin cerrar ni enviar el salto de linea
        time.sleep(0.2)
        self.servidor.detener()
        self.sin_huerfanos("sleep 312")
        self.servidor.iniciar(opciones=["--listen", "127.0.0.1:" + str(self.puerto)])
        self.assertEqual(self.servidor.listar(), [])

    def test_el_segundo_ctrl_c_fuerza_el_cierre_con_tcp_abierto(self):
        self.servidor.enviar("--", "sh", "-c", IGNORA_SIGTERM)
        self.clientes_abiertos(2)
        time.sleep(0.3)
        inicio = time.monotonic()
        self.servidor.proceso.send_signal(signal.SIGINT)
        time.sleep(1.0)
        self.servidor.proceso.send_signal(signal.SIGINT)
        self.servidor.proceso.wait(timeout=8)
        self.assertLess(time.monotonic() - inicio, 4.0)
        self.assertIn(puerto_en_escucha(self.puerto), (False, None))
        self.sin_huerfanos("sleep 1|while")

    def test_la_bitacora_registra_el_cierre_de_la_red(self):
        self.clientes_abiertos(2)
        time.sleep(0.2)
        self.servidor.detener()
        texto = self.bitacora()
        self.assertIn("red_cerrada", texto)
        self.assertIn("conexiones=2", texto)
        self.assertIn("tcp=127.0.0.1:" + str(self.puerto), texto)
        self.assertLess(texto.index("red_cerrada"), texto.index("servicio_detenido"))


class TestTC009SinTcp(unittest.TestCase):
    """Sin --listen el cierre sigue igual y no aparece ningun puerto."""

    def test_sin_listen_no_se_registra_puerto_tcp(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        servidor.iniciar()
        time.sleep(0.5)   # que el servidor termine de atender la conexion de comprobacion del arranque
        servidor.detener()
        texto = servidor.directorio.joinpath("jobrunner.log").read_text()
        self.assertIn("red_cerrada", texto)
        self.assertIn("conexiones=0", texto)
        self.assertIn("tcp=-", texto)


if __name__ == "__main__":
    unittest.main()
