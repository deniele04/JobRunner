"""El comando `royito` (scripts/royito) es el prefijo del cliente (RF-17).

Comprueba que el lanzador funciona sin PYTHONPATH, desde cualquier carpeta, por un
enlace simbólico y respetando JOBRUNNER_SOCKET, y que la ayuda lleva su nombre.
"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import RAIZ, PruebaDeIntegracion

ROYITO = RAIZ / "scripts" / "royito"


def entorno_limpio(**extra):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "JOBRUNNER_SOCKET")}
    env.update(extra)
    return env


def royito(*args, comando=ROYITO, cwd=None, **env):
    r = subprocess.run([str(comando), *args], capture_output=True, text=True,
                       cwd=cwd, env=entorno_limpio(**env), timeout=30)
    return r.returncode, r.stdout, r.stderr


class TestRoyito(PruebaDeIntegracion):

    def test_royito_es_ejecutable(self):
        self.assertTrue(os.access(ROYITO, os.X_OK), "scripts/royito no tiene permiso de ejecución")

    def test_la_ayuda_lleva_el_nombre_royito(self):
        codigo, salida, _ = royito("--help")
        self.assertEqual(codigo, 0)
        self.assertIn("royito", salida)
        self.assertNotIn("jobrunner submit", salida)

    def test_royito_envia_y_consulta_desde_cualquier_carpeta(self):
        with tempfile.TemporaryDirectory() as otra_carpeta:
            codigo, salida, err = royito("--socket", self.servidor.socket, "submit", "--", "sleep", "10",
                                         cwd=otra_carpeta)
            self.assertEqual(codigo, 0, err)
            job_id = json.loads(salida)["id"]
            codigo, salida, err = royito("--socket", self.servidor.socket, "status", job_id,
                                         cwd=otra_carpeta)
            self.assertEqual(codigo, 0, err)
            self.assertEqual(json.loads(salida)["state"], "RUNNING")

    def test_respeta_la_variable_jobrunner_socket(self):
        codigo, salida, err = royito("submit", "--", "sleep", "10", JOBRUNNER_SOCKET=self.servidor.socket)
        self.assertEqual(codigo, 0, err)
        self.assertIn("id", json.loads(salida))

    def test_funciona_a_traves_de_un_enlace_simbolico(self):
        with tempfile.TemporaryDirectory() as d:
            enlace = Path(d) / "royito"
            enlace.symlink_to(ROYITO)
            codigo, salida, err = royito("--socket", self.servidor.socket, "list", comando=enlace)
        self.assertEqual(codigo, 0, err)
        self.assertEqual(json.loads(salida), {"jobs": []})

    def test_sin_socket_indicado_apunta_al_socket_del_repositorio(self):
        # El valor por defecto es <repositorio>/data/jobrunner.sock, igual que ./scripts/run.sh.
        esperado = str(RAIZ / "data" / "jobrunner.sock")
        if os.path.exists(esperado):
            self.skipTest("hay un servicio de desarrollo corriendo en data/")
        codigo, _, err = royito("list")
        self.assertNotEqual(codigo, 0)
        self.assertIn(esperado, err)


if __name__ == "__main__":
    unittest.main()
