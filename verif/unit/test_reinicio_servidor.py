"""TC-007 y TC-018 con un servidor real: reinicio sin perder trabajos y duplicados.

Levanta el servidor como proceso aparte, lo mata con SIGKILL (caida inesperada)
y lo vuelve a arrancar sobre los mismos datos. Comprueba que el historial se
conserva, que el trabajo interrumpido pasa a FAILED y su proceso se termina, y
que un request_id repetido devuelve el mismo trabajo, incluso tras reiniciar o
tras una desconexion del cliente (ADR-0002, ADR-0005, decision 8 de la minuta).
"""
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest

NL = bytes([10])
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pedir(ruta, pedido):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as c:
        c.settimeout(5)
        c.connect(ruta)
        c.sendall(json.dumps(pedido).encode("utf-8") + NL)
        resp = b""
        while not resp.endswith(NL):
            trozo = c.recv(4096)
            if not trozo:
                break
            resp += trozo
    return json.loads(resp.decode("utf-8"))


def grupo_vivo(pid):
    """True si el grupo de procesos existe y no es un zombi."""
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return False
    try:
        with open("/proc/" + str(pid) + "/stat") as f:
            estado = f.read().rsplit(")", 1)[1].split()[0]
        return estado != "Z"
    except OSError:
        return False


class ReinicioServidorTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self._tmp.name, "jobrunner.sock")
        self.proc = None
        self.pids = []
        self.arrancar()

    def tearDown(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=5)
        for pid in self.pids:
            try:
                os.killpg(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        self._tmp.cleanup()

    def arrancar(self):
        entorno = dict(os.environ, PYTHONPATH=os.path.join(RAIZ, "src"))
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "jobrunner.server", self.ruta],
            env=entorno, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        limite = time.monotonic() + 10
        while time.monotonic() < limite:
            if self.proc.poll() is not None:
                self.fail("el servidor termino al arrancar")
            try:
                pedir(self.ruta, {"cmd": "list"})
                return
            except (FileNotFoundError, ConnectionRefusedError, OSError):
                time.sleep(0.1)
        self.fail("el servidor no respondio a tiempo")

    def matar_servidor(self):
        self.proc.kill()
        self.proc.wait(timeout=5)

    def reiniciar(self):
        self.matar_servidor()
        self.arrancar()

    def test_reinicio_conserva_historial_y_recupera_interrumpidos(self):
        largo = pedir(self.ruta, {"cmd": "submit", "argv": ["sleep", "120"]})
        self.pids.append(largo["pid"])
        corto = pedir(self.ruta, {"cmd": "submit", "argv": ["true"]})
        time.sleep(0.5)
        self.assertEqual(pedir(self.ruta, {"cmd": "status", "id": corto["id"]})["state"], "SUCCEEDED")

        self.matar_servidor()
        self.assertTrue(grupo_vivo(largo["pid"]), "el trabajo deberia seguir vivo tras la caida")
        self.arrancar()

        lista = {j["id"]: j for j in pedir(self.ruta, {"cmd": "list"})["jobs"]}
        self.assertEqual(len(lista), 2)
        self.assertEqual(lista[corto["id"]]["state"], "SUCCEEDED")
        self.assertEqual(lista[corto["id"]]["exit_code"], 0)
        self.assertEqual(lista[largo["id"]]["state"], "FAILED")
        self.assertEqual(lista[largo["id"]]["error"], "interrumpido por reinicio")

        limite = time.monotonic() + 8
        while grupo_vivo(largo["pid"]) and time.monotonic() < limite:
            time.sleep(0.1)
        self.assertFalse(grupo_vivo(largo["pid"]), "el proceso interrumpido debio terminarse")

        with open(os.path.join(self._tmp.name, "jobrunner.log"), encoding="utf-8") as f:
            self.assertIn("recuperado job=" + largo["id"], f.read())

    def test_servidor_request_id_repetido_devuelve_el_mismo_trabajo(self):
        pedido = {"cmd": "submit", "argv": ["sleep", "120"], "request_id": "req-1"}
        primero = pedir(self.ruta, pedido)
        self.pids.append(primero["pid"])
        segundo = pedir(self.ruta, pedido)
        self.assertEqual(segundo["id"], primero["id"])
        self.assertEqual(len(pedir(self.ruta, {"cmd": "list"})["jobs"]), 1)

    def test_reenvio_tras_desconexion_del_cliente(self):
        pedido = {"cmd": "submit", "argv": ["sleep", "120"], "request_id": "req-desc"}
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as c:
            c.connect(self.ruta)
            c.sendall(json.dumps(pedido).encode("utf-8") + NL)
        time.sleep(0.3)
        reenvio = pedir(self.ruta, pedido)
        self.pids.append(reenvio["pid"])
        self.assertEqual(len(pedir(self.ruta, {"cmd": "list"})["jobs"]), 1)

    def test_servidor_request_id_repetido_despues_de_reiniciar(self):
        pedido = {"cmd": "submit", "argv": ["sleep", "120"], "request_id": "req-reinicio"}
        primero = pedir(self.ruta, pedido)
        self.pids.append(primero["pid"])
        self.reiniciar()
        repetido = pedir(self.ruta, pedido)
        self.assertEqual(repetido["id"], primero["id"])
        self.assertEqual(len(pedir(self.ruta, {"cmd": "list"})["jobs"]), 1)

    def test_request_id_invalido_se_rechaza(self):
        for invalido in ("", 5):
            respuesta = pedir(self.ruta, {"cmd": "submit", "argv": ["true"], "request_id": invalido})
            self.assertEqual(list(respuesta), ["error"])
        self.assertEqual(pedir(self.ruta, {"cmd": "list"})["jobs"], [])


if __name__ == "__main__":
    unittest.main()
