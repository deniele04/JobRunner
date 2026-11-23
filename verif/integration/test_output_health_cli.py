"""royito output y royito health con el servidor real, por el socket Unix y por TCP (U2).

Cubre RF-18 (output remoto), RF-19 (misma semantica que en local) y RF-24 (health).
"""
import json
import sys
import time
import unittest

from helpers import ServidorDePrueba
from helpers_remoto import ClienteRemotoBase, esperar_puerto, puerto_libre, royito


class OutputPorCliTest(ClienteRemotoBase):

    def enviar_y_esperar(self, *argv):
        _, trabajo = self.servidor.enviar("--", *argv)
        return self.servidor.esperar_estado_final(trabajo["id"])

    def por_unix(self, *args):
        return self.servidor.cli(*args)

    def test_output_devuelve_la_salida_por_unix_y_por_tcp(self):
        job = self.enviar_y_esperar("echo", "hola remoto")
        _, unix, _ = self.por_unix("output", job["id"])
        codigo, tcp, err = self.tcp("output", job["id"])
        self.assertEqual(codigo, 0, err)
        self.assertEqual(json.loads(tcp), json.loads(unix))
        self.assertEqual(json.loads(tcp), {"v": 1, "id": job["id"], "stream": "stdout",
                                           "data": "hola remoto\n", "truncated": False})

    def test_stderr_con_la_opcion_stderr(self):
        job = self.enviar_y_esperar(sys.executable, "-c",
                                    "import sys; print('bien'); print('mal', file=sys.stderr)")
        for ejecutar in (self.por_unix, self.tcp):
            salida = json.loads(ejecutar("output", job["id"], "--stderr")[1])
            self.assertEqual((salida["stream"], salida["data"]), ("stderr", "mal\n"))

    def test_raw_imprime_solo_el_texto(self):
        job = self.enviar_y_esperar("printf", "a\nb\n")
        codigo, salida, err = self.tcp("output", job["id"], "--raw")
        self.assertEqual((codigo, salida), (0, "a\nb\n"), err)

    def test_salida_larga_se_trunca_a_64_kib_y_lo_avisa(self):
        job = self.enviar_y_esperar(sys.executable, "-c", "import sys; sys.stdout.write('x' * 200000)")
        codigo, salida, err = self.tcp("output", job["id"])
        datos = json.loads(salida)
        self.assertEqual(codigo, 0, err)
        self.assertTrue(datos["truncated"])
        self.assertEqual(len(datos["data"]), 65536)
        _, crudo, aviso = self.tcp("output", job["id"], "--raw")
        self.assertEqual(len(crudo), 65536)
        self.assertIn("solo se muestra el final", aviso)

    def test_max_bytes(self):
        job = self.enviar_y_esperar("echo", "0123456789")
        datos = json.loads(self.tcp("output", job["id"], "--max-bytes", "4")[1])
        self.assertEqual((datos["data"], datos["truncated"]), ("789\n", True))

    def test_max_bytes_fuera_de_rango_da_error_con_que_hacer(self):
        job = self.enviar_y_esperar("true")
        codigo, salida, err = self.tcp("output", job["id"], "--max-bytes", "0")
        self.assertEqual(codigo, 1)
        self.assertIn("max_bytes", json.loads(salida)["error"])
        self.assertIn("Que hacer", err)

    def test_id_inexistente_sale_con_1(self):
        for ejecutar in (self.por_unix, self.tcp):
            codigo, salida, err = ejecutar("output", "no-existe")
            self.assertEqual(codigo, 1)
            self.assertEqual(json.loads(salida)["error"], "No existe el trabajo no-existe")
            self.assertIn("Error al leer la salida del trabajo", err)

    def test_output_de_un_trabajo_en_ejecucion_por_tcp_devuelve_lo_que_lleva(self):
        _, trabajo = self.servidor.enviar(
            "--", sys.executable, "-u", "-c", "print('avance'); import time; time.sleep(30)")
        fin = time.monotonic() + 10
        datos = {"data": ""}
        while time.monotonic() < fin and not datos["data"]:
            datos = json.loads(self.tcp("output", trabajo["id"])[1])
            time.sleep(0.1)
        self.assertEqual(datos["data"], "avance\n")


class HealthPorCliTest(ClienteRemotoBase):
    opciones_extra = ("--max-jobs", "2", "--queue-size", "1")

    def test_health_por_unix_y_por_tcp(self):
        for ejecutar in (self.servidor.cli, self.tcp):
            codigo, salida, err = ejecutar("health")
            self.assertEqual(codigo, 0, err)
            salud = json.loads(salida)
            self.assertEqual(salud["v"], 1)
            self.assertEqual((salud["max_jobs"], salud["queue_size"]), (2, 1))
            self.assertEqual(salud["database"], "ok")
            self.assertEqual(salud["running"], 0)
            self.assertNotIn("error", salud)

    def test_health_cuenta_los_clientes_conectados(self):
        salud = json.loads(self.tcp("health")[1])
        self.assertGreaterEqual(salud["clients"], 1)   # incluye al cliente que pregunta

    def test_health_refleja_los_trabajos_por_tcp(self):
        for _ in range(3):   # 2 corren, 1 espera: cola llena
            self.tcp("submit", "--", "sleep", "30")
        salud = json.loads(self.tcp("health")[1])
        self.assertEqual((salud["running"], salud["queued"]), (2, 1))
        self.assertEqual(salud["jobs_by_state"]["RUNNING"], 2)


class HealthAccesosRechazadosTest(unittest.TestCase):

    def test_los_accesos_rechazados_se_cuentan(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        puerto = puerto_libre()
        servidor.iniciar(opciones=["--listen", "127.0.0.1:%d" % puerto, "--allow", "10.0.0.0/8"])
        esperar_puerto(puerto)   # la conexion se acepta y se cierra: ya cuenta como rechazada
        time.sleep(0.2)
        antes = json.loads(servidor.cli("health")[1])["rejected_access"]
        for _ in range(3):
            royito("--host", "127.0.0.1", "--port", str(puerto), "list")
        time.sleep(0.3)
        despues = json.loads(servidor.cli("health")[1])["rejected_access"]
        self.assertEqual(despues - antes, 3)


if __name__ == "__main__":
    unittest.main()
