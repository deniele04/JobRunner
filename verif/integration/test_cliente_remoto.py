"""Cliente remoto (U1): `royito --host HOST --port PUERTO` y las variables JOBRUNNER_HOST y JOBRUNNER_PORT.

Levanta el servidor real con --listen en 127.0.0.1 (solo loopback, nunca un puerto abierto a
la red) y usa el CLI real. Cubre RF-18 y RF-19 (misma operacion por TCP que por socket Unix),
el codigo de salida con `v` en las respuestas y el mensaje cuando no hay conexion (RNF-21).
"""
import json
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


class OperacionesPorTcpTest(ClienteRemotoBase):

    def test_submit_status_list_y_cancel_funcionan_con_host_y_puerto(self):
        codigo, salida, err = self.tcp("submit", "--", "sleep", "30")
        self.assertEqual(codigo, 0, err)
        trabajo = json.loads(salida)
        self.assertEqual(trabajo["state"], "RUNNING")

        codigo, salida, err = self.tcp("status", trabajo["id"])
        self.assertEqual(codigo, 0, err)
        self.assertEqual(json.loads(salida)["id"], trabajo["id"])

        codigo, salida, err = self.tcp("list")
        self.assertEqual(codigo, 0, err)
        self.assertEqual([t["id"] for t in json.loads(salida)["jobs"]], [trabajo["id"]])

        codigo, salida, err = self.tcp("cancel", trabajo["id"])
        self.assertEqual(codigo, 0, err)
        self.servidor.esperar_estado_final(trabajo["id"])

    def test_los_mismos_comandos_funcionan_por_el_socket_unix(self):
        codigo, trabajo = self.servidor.enviar("--", "sleep", "30")
        self.assertEqual(codigo, 0)
        # Lo enviado por el socket Unix se ve por TCP y al reves: es el mismo servicio.
        codigo, salida, err = self.tcp("status", trabajo["id"])
        self.assertEqual(codigo, 0, err)
        self.assertEqual(json.loads(salida)["id"], trabajo["id"])

    def test_la_respuesta_por_tcp_lleva_v_1(self):
        _, salida, _ = self.tcp("list")
        self.assertEqual(json.loads(salida), {"v": 1, "jobs": []})

    def test_request_id_por_tcp_devuelve_el_mismo_trabajo(self):
        _, primero, _ = self.tcp("submit", "--request-id", "remoto-1", "--", "sleep", "30")
        _, segundo, _ = self.tcp("submit", "--request-id", "remoto-1", "--", "sleep", "30")
        self.assertEqual(json.loads(primero)["id"], json.loads(segundo)["id"])
        self.assertTrue(json.loads(segundo)["duplicado"])


class VariablesDeEntornoTest(ClienteRemotoBase):

    def test_jobrunner_host_y_jobrunner_port(self):
        codigo, salida, err = royito("list", env_extra={
            "JOBRUNNER_HOST": "127.0.0.1", "JOBRUNNER_PORT": str(self.puerto)})
        self.assertEqual(codigo, 0, err)
        self.assertEqual(json.loads(salida)["jobs"], [])

    def test_las_opciones_tienen_prioridad_sobre_las_variables(self):
        libre = puerto_libre()   # nadie escucha ahi
        codigo, salida, err = royito(
            "--port", str(self.puerto), "list",
            env_extra={"JOBRUNNER_HOST": "127.0.0.1", "JOBRUNNER_PORT": str(libre)})
        self.assertEqual(codigo, 0, err)

    def test_sin_host_se_usa_el_socket_unix_aunque_haya_un_puerto_en_el_entorno(self):
        codigo, salida, err = royito("--socket", self.servidor.socket, "list",
                                     env_extra={"JOBRUNNER_PORT": str(puerto_libre())})
        self.assertEqual(codigo, 0, err)

    def test_el_lanzador_royito_respeta_las_variables(self):
        codigo, salida, err = royito("list", comando=ROYITO, env_extra={
            "JOBRUNNER_HOST": "127.0.0.1", "JOBRUNNER_PORT": str(self.puerto)})
        self.assertEqual(codigo, 0, err)
        self.assertEqual(json.loads(salida)["jobs"], [])

    def test_el_lanzador_royito_acepta_host_y_puerto(self):
        codigo, salida, err = royito("--host", "127.0.0.1", "--port", str(self.puerto), "list",
                                     comando=ROYITO)
        self.assertEqual(codigo, 0, err)


class ErroresDeConexionTest(unittest.TestCase):

    def test_sin_servicio_el_mensaje_dice_a_donde_no_pudo_conectar(self):
        puerto = puerto_libre()
        codigo, salida, err = royito("--host", "127.0.0.1", "--port", str(puerto), "list")
        self.assertEqual(codigo, 1)
        self.assertEqual(salida, "")
        self.assertIn("no se pudo conectar a 127.0.0.1:%d" % puerto, err)
        self.assertIn("--listen", err)    # la accion que sugiere
        self.assertNotIn("Traceback", err)

    def test_host_que_no_se_resuelve_da_un_mensaje_y_no_un_traceback(self):
        codigo, _, err = royito("--host", "no-existe.invalid", "--port", "7070", "list")
        self.assertEqual(codigo, 1)
        self.assertIn("no se pudo conectar a no-existe.invalid:7070", err)
        self.assertNotIn("Traceback", err)

    def test_origen_no_permitido_da_un_mensaje_que_menciona_allow(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        puerto = puerto_libre()
        # Solo se permite 10.0.0.0/8: la conexion desde 127.0.0.1 se cierra sin responder.
        servidor.iniciar(opciones=["--listen", "127.0.0.1:%d" % puerto, "--allow", "10.0.0.0/8"])
        esperar_puerto(puerto)
        codigo, salida, err = royito("--host", "127.0.0.1", "--port", str(puerto), "list")
        self.assertEqual(codigo, 1)
        self.assertEqual(salida, "")
        self.assertIn("cerro la conexion sin responder", err)
        self.assertIn("--allow", err)
        self.assertNotIn("Traceback", err)

    def test_el_socket_unix_conserva_su_mensaje(self):
        codigo, _, err = royito("--socket", "/tmp/no-existe-jobrunner.sock", "list")
        self.assertEqual(codigo, 1)
        self.assertIn("no se pudo conectar al servidor en /tmp/no-existe-jobrunner.sock", err)


class UsoIncorrectoTest(unittest.TestCase):

    def test_port_sin_host_es_un_error_de_uso(self):
        codigo, _, err = royito("--port", "7070", "list")
        self.assertEqual(codigo, 2)
        self.assertIn("--port requiere --host", err)

    def test_puerto_no_numerico_es_un_error_de_uso(self):
        codigo, _, err = royito("--host", "127.0.0.1", "--port", "abc", "list")
        self.assertEqual(codigo, 2)
        self.assertIn("puerto invalido", err)

    def test_puerto_fuera_de_rango_es_un_error_de_uso(self):
        for valor in ("0", "65536", "-1"):
            with self.subTest(puerto=valor):
                codigo, _, err = royito("--host", "127.0.0.1", "--port", valor, "list")
                self.assertEqual(codigo, 2)
                self.assertIn("puerto fuera de rango", err)

    def test_jobrunner_port_invalido_es_un_error_de_uso(self):
        codigo, _, err = royito("list", env_extra={"JOBRUNNER_HOST": "127.0.0.1", "JOBRUNNER_PORT": "xx"})
        self.assertEqual(codigo, 2)
        self.assertIn("JOBRUNNER_PORT", err)


class CodigoDeSalidaPorTcpTest(ClienteRemotoBase):

    def test_error_del_servicio_por_tcp_sale_con_1_y_explica_que_hacer(self):
        codigo, salida, err = self.tcp("status", "no-existe")
        self.assertEqual(codigo, 1)
        self.assertIn("no existe el trabajo no-existe", json.loads(salida)["error"])
        self.assertIn("Error al consultar el trabajo", err)
        self.assertIn("Que hacer", err)

    def test_trabajo_fallido_por_tcp_sale_con_0(self):
        _, salida, _ = self.tcp("submit", "--", "sh", "-c", "exit 3")
        job_id = json.loads(salida)["id"]
        trabajo = self.servidor.esperar_estado_final(job_id)
        self.assertEqual(trabajo["state"], "FAILED")
        codigo, salida, err = self.tcp("status", job_id)
        self.assertEqual(codigo, 0, err)
        self.assertEqual(json.loads(salida)["exit_code"], 3)


if __name__ == "__main__":
    unittest.main()
