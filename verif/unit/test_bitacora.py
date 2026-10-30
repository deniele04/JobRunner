"""Pruebas unitarias de la bitácora de eventos (TC-025: RF-14, RNF-22, RNF-15).

Comprueban que cada evento queda en una línea con fecha y hora, nivel, tipo e ID
del trabajo; que los eventos de un mismo trabajo se pueden correlacionar por su
ID, y que la bitácora no guarda los argumentos de los trabajos.

Ejecutar con ./scripts/test.sh (usa unittest de la biblioteca estándar).
"""
import re
import tempfile
import time
import unittest

from jobrunner import bitacora
from jobrunner.executor import JobManager
from jobrunner.jobs import FINAL_STATES, RUNNING

FORMATO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z (INFO|ERROR) \S+ job=\S+")


class BitacoraTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ruta = bitacora.configurar(self._tmp.name)
        self.mgr = JobManager(data_dir=self._tmp.name)

    def tearDown(self):
        for job in self.mgr.list(state=RUNNING):
            try:
                self.mgr.cancel(job["id"])
            except (KeyError, ValueError):
                pass
        bitacora.cerrar()
        self._tmp.cleanup()

    def lineas(self):
        return self.ruta.read_text(encoding="utf-8").splitlines()

    def esperar_estado_final(self, job_id, timeout=5.0):
        limite = time.monotonic() + timeout
        while time.monotonic() < limite:
            self.mgr.poll()
            if self.mgr.get(job_id)["state"] in FINAL_STATES:
                return
            time.sleep(0.05)
        self.fail(f"El trabajo {job_id} no llegó a un estado final en {timeout} s")

    def test_cada_evento_tiene_fecha_nivel_tipo_e_id(self):
        bitacora.evento("iniciado", "abc123", pid=42)
        bitacora.error("solicitud_invalida", motivo="JSON invalido")

        info, err = self.lineas()
        self.assertRegex(info, FORMATO)
        self.assertTrue(info.endswith("INFO iniciado job=abc123 pid=42"))
        self.assertRegex(err, FORMATO)
        self.assertTrue(err.endswith('ERROR solicitud_invalida job=- motivo="JSON invalido"'))

    def test_eventos_de_un_trabajo_se_correlacionan_por_su_id(self):
        job = self.mgr.submit(["sh", "-c", "exit 3"])
        self.esperar_estado_final(job["id"])

        del_trabajo = [linea for linea in self.lineas() if "job=" + job["id"] in linea]
        tipos = [linea.split()[2] for linea in del_trabajo]
        self.assertEqual(tipos, ["recibido", "iniciado", "terminado"])
        self.assertIn("estado=FAILED codigo=3", del_trabajo[-1])

    def test_cancelar_registra_el_evento_con_su_codigo(self):
        job = self.mgr.submit(["sleep", "30"])
        self.mgr.cancel(job["id"])
        self.esperar_estado_final(job["id"])

        self.assertTrue(any(
            "cancelado job=" + job["id"] + " codigo=-15" in linea for linea in self.lineas()
        ))

    def test_comando_inexistente_registra_un_error(self):
        job = self.mgr.submit(["comando_que_no_existe_xyz"])

        errores = [linea for linea in self.lineas() if " ERROR " in linea]
        self.assertEqual(len(errores), 1)
        self.assertIn("no_se_pudo_iniciar job=" + job["id"], errores[0])

    def test_no_registra_los_argumentos_del_trabajo(self):
        job = self.mgr.submit(["sh", "-c", "echo clave-secreta-123"])
        self.esperar_estado_final(job["id"])

        contenido = self.ruta.read_text(encoding="utf-8")
        self.assertIn("programa=sh", contenido)
        self.assertNotIn("clave-secreta-123", contenido)


if __name__ == "__main__":
    unittest.main()
