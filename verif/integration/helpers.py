"""Base de las pruebas de integración de JobRunner.

Levanta el servidor real (`python3 -m jobrunner.server`) en un directorio
temporal propio, con su propio socket Unix, y ofrece una función para usar el
CLI real (`python3 -m jobrunner.cli`) como lo haría una persona. Cada prueba
tiene su servidor y su directorio de datos, así que no se afectan entre sí ni
tocan `data/` del repositorio.

Solo biblioteca estándar (ADR-0001).
"""
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SRC = RAIZ / "src"
PROCESOS_SH = RAIZ / "verif" / "scripts" / "procesos.sh"

ESTADOS_FINALES = ("SUCCEEDED", "FAILED", "CANCELED")


def entorno():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    # Evita que un JOBRUNNER_SOCKET del entorno apunte a otro servidor.
    env.pop("JOBRUNNER_SOCKET", None)
    return env


class ServidorDePrueba:
    """Servidor JobRunner real, aislado, con su socket y su directorio de datos."""

    def __init__(self):
        self.directorio = Path(tempfile.mkdtemp(prefix="jobrunner-integracion-"))
        self.socket = str(self.directorio / "jobrunner.sock")
        self.proceso = None
        self.opciones = []
        self.salida = self.directorio / "servidor.log"

    # -- ciclo de vida -----------------------------------------------------
    def iniciar(self, espera=10.0, opciones=None):
        """Arranca el servidor. `opciones` (p. ej. ["--max-jobs", "1"]) se recuerdan
        para `reiniciar()`."""
        if opciones is not None:
            self.opciones = list(opciones)
        with open(self.salida, "ab") as log:
            self.proceso = subprocess.Popen(
                [sys.executable, "-m", "jobrunner.server", self.socket, *self.opciones],
                stdout=log, stderr=subprocess.STDOUT, env=entorno(), cwd=str(RAIZ),
            )
        limite = time.monotonic() + espera
        while time.monotonic() < limite:
            if self.proceso.poll() is not None:
                raise RuntimeError("El servidor terminó al arrancar:\n" + self.log())
            if self._acepta_conexiones():
                return self
            time.sleep(0.05)
        self.matar()
        raise RuntimeError("El servidor no abrió el socket en %.0f s:\n%s" % (espera, self.log()))

    def _acepta_conexiones(self):
        if not os.path.exists(self.socket):
            return False
        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            probe.connect(self.socket)
            return True
        except OSError:
            return False
        finally:
            probe.close()

    def detener(self, espera=15.0, senal=signal.SIGINT):
        """Cierre ordenado con Ctrl+C (SIGINT) o SIGTERM, como lo haría el operador.

        Espera a que el servidor termine por sí solo; si no lo hace, lo mata.
        """
        if self.proceso is None or self.proceso.poll() is not None:
            return
        self.proceso.send_signal(senal)
        try:
            self.proceso.wait(timeout=espera)
        except subprocess.TimeoutExpired:
            self.matar()

    def reiniciar(self, **kwargs):
        """Vuelve a arrancar el servidor sobre el mismo directorio de datos."""
        self.detener()
        return self.iniciar(**kwargs)

    def matar(self):
        """Muerte abrupta (SIGKILL): simula una falla dura del servicio."""
        if self.proceso is not None and self.proceso.poll() is None:
            self.proceso.kill()
            self.proceso.wait()

    def limpiar(self):
        """Cancela trabajos vivos, detiene el servidor y borra el directorio."""
        try:
            if self.proceso is not None and self.proceso.poll() is None:
                for trabajo in self.listar():
                    if trabajo.get("state") in ("QUEUED", "RUNNING"):
                        self.cli("cancel", trabajo["id"])
        except Exception:
            pass
        self.detener()
        shutil.rmtree(self.directorio, ignore_errors=True)

    def log(self):
        try:
            return self.salida.read_text(errors="replace")
        except OSError:
            return ""

    # -- uso del CLI --------------------------------------------------------
    def cli(self, *args, timeout=20):
        """Ejecuta `python3 -m jobrunner.cli --socket <socket> <args>`.

        Devuelve (código de salida, stdout, stderr).
        """
        r = subprocess.run(
            [sys.executable, "-m", "jobrunner.cli", "--socket", self.socket, *args],
            capture_output=True, text=True, env=entorno(), cwd=str(RAIZ), timeout=timeout,
        )
        return r.returncode, r.stdout, r.stderr

    def cli_json(self, *args):
        """Como `cli`, pero interpreta stdout como JSON. Devuelve (código, objeto)."""
        codigo, salida, err = self.cli(*args)
        try:
            return codigo, json.loads(salida)
        except json.JSONDecodeError:
            raise AssertionError(
                "El CLI no devolvió JSON (código %s)\nstdout: %r\nstderr: %r"
                % (codigo, salida, err)
            )

    def enviar(self, *argv):
        """submit -- <argv>. Devuelve (código, trabajo)."""
        return self.cli_json("submit", *argv)

    def estado(self, job_id):
        return self.cli_json("status", job_id)[1]

    def listar(self, estado=None):
        args = ["list"] + (["--state", estado] if estado else [])
        return self.cli_json(*args)[1]["jobs"]

    def esperar_estado_final(self, job_id, limite=15.0):
        fin = time.monotonic() + limite
        while time.monotonic() < fin:
            trabajo = self.estado(job_id)
            if trabajo.get("state") in ESTADOS_FINALES:
                return trabajo
            time.sleep(0.1)
        raise AssertionError("El trabajo %s no terminó en %.0f s" % (job_id, limite))

    def solicitud_cruda(self, texto):
        """Envía bytes tal cual al socket (para solicitudes mal formadas)."""
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(10)
        try:
            s.connect(self.socket)
            s.sendall(texto.encode("utf-8"))
            datos = b""
            while not datos.endswith(b"\n"):
                trozo = s.recv(4096)
                if not trozo:
                    break
                datos += trozo
            return json.loads(datos.decode("utf-8"))
        finally:
            s.close()


class PruebaDeIntegracion(unittest.TestCase):
    """Clase base: un servidor nuevo por prueba, siempre limpiado al final."""

    def setUp(self):
        self.servidor = ServidorDePrueba()
        self.addCleanup(self.servidor.limpiar)
        self.servidor.iniciar()
