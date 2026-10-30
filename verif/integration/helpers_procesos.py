"""Utilidades compartidas por las pruebas TC-019, TC-020 y TC-024.

Comprobar que no quedan zombis ni huerfanos (con verif/scripts/procesos.sh) y
contar los descriptores de archivo abiertos del servidor.
"""
import os
import re
import signal
import subprocess
import tempfile

from helpers import PROCESOS_SH, PruebaDeIntegracion


def procesos(*args):
    r = subprocess.run([str(PROCESOS_SH), *args], capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout, r.stderr


def matar_grupos(salida):
    """Mata los grupos de procesos que el script marco como HUERFANO."""
    for pid in re.findall(r"^HUERFANO\t(\d+)", salida, re.M):
        try:
            os.killpg(int(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def descriptores_abiertos(pid):
    """Cantidad de descriptores de archivo abiertos por el proceso (Linux)."""
    return len(os.listdir("/proc/" + str(pid) + "/fd"))


class ConLineaBase(PruebaDeIntegracion):
    """Guarda la linea base de PID ANTES de levantar el servidor."""

    def setUp(self):
        fd, self.base = tempfile.mkstemp(prefix="jobrunner-base-")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self.base) and os.remove(self.base))
        codigo, _, _ = procesos("guardar", self.base)
        self.assertEqual(codigo, 0)
        super().setUp()

    def assertSinZombisNiHuerfanos(self, patron="sleep|jobrunner"):
        codigo, salida, _ = procesos("revisar", "--base", self.base, "--patron", patron)
        self.addCleanup(matar_grupos, salida)
        self.assertEqual(codigo, 0, salida)

    def descriptores_del_servidor(self):
        return descriptores_abiertos(self.servidor.proceso.pid)

    def bitacora(self):
        ruta = self.servidor.directorio / "jobrunner.log"
        return ruta.read_text(encoding="utf-8") if ruta.exists() else ""
