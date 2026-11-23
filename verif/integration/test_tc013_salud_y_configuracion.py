"""TC-013 (RF-16, RF-24): salud y configuracion.

`health` refleja los trabajos y los limites del servicio, y el servidor respeta --max-jobs,
--queue-size y --listen (y rechaza los valores invalidos con un mensaje). Servidor y CLI reales,
solo en 127.0.0.1.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest

from helpers import RAIZ, ServidorDePrueba, entorno
from helpers_remoto import ClienteRemotoBase, esperar_puerto, puerto_libre


def salud(ejecutar):
    codigo, salida, err = ejecutar("health")
    assert codigo == 0, err
    return json.loads(salida)


class SaludConLimitesTest(ClienteRemotoBase):
    opciones_extra = ("--max-jobs", "2", "--queue-size", "1")

    def test_health_informa_los_limites_configurados(self):
        for ejecutar in (self.servidor.cli, self.tcp):
            h = salud(ejecutar)
            self.assertEqual((h["max_jobs"], h["queue_size"]), (2, 1))

    def test_health_refleja_corriendo_en_cola_y_rechazados(self):
        self.servidor.enviar("--", "sleep", "30")
        self.servidor.enviar("--", "sleep", "30")
        _, tercero = self.servidor.enviar("--", "sleep", "30")        # a la cola
        self.assertEqual(tercero["state"], "QUEUED")
        codigo, rechazado = self.servidor.enviar("--", "sleep", "30")  # cola llena
        self.assertEqual(codigo, 1)
        self.assertIn("cola llena (capacidad 1)", rechazado["error"])
        for ejecutar in (self.servidor.cli, self.tcp):
            h = salud(ejecutar)
            self.assertEqual((h["running"], h["queued"]), (2, 1))
            self.assertEqual(h["jobs_by_state"]["RUNNING"], 2)
            self.assertEqual(h["jobs_by_state"]["QUEUED"], 1)
            self.assertEqual(sum(h["jobs_by_state"].values()), 3)   # el rechazado no cuenta

    def test_health_sigue_los_cambios_de_estado(self):
        _, a = self.servidor.enviar("--", "sleep", "30")
        _, corto = self.servidor.enviar("--", "true")
        self.servidor.esperar_estado_final(corto["id"])
        _, c = self.servidor.enviar("--", "sleep", "30")
        self.assertEqual(c["state"], "RUNNING")
        _, d = self.servidor.enviar("--", "sleep", "30")      # a la cola
        self.assertEqual(d["state"], "QUEUED")
        h = salud(self.tcp)
        self.assertEqual((h["jobs_by_state"]["SUCCEEDED"], h["running"], h["queued"]), (1, 2, 1))
        self.servidor.cli("cancel", d["id"])                  # sale de la cola
        h = salud(self.tcp)
        self.assertEqual((h["jobs_by_state"]["CANCELED"], h["queued"]), (1, 0))
        self.servidor.cli("cancel", a["id"])
        self.servidor.esperar_estado_final(a["id"])
        h = salud(self.tcp)
        self.assertEqual(h["jobs_by_state"]["CANCELED"], 2)
        self.assertEqual(h["running"], 1)

    def test_health_informa_version_tiempo_activo_y_base(self):
        h = salud(self.tcp)
        self.assertRegex(h["version"], r"^\d+\.\d+\.\d+")
        self.assertGreaterEqual(h["uptime_seconds"], 0)
        self.assertEqual(h["database"], "ok")
        self.assertGreaterEqual(h["clients"], 1)
        self.assertEqual(h["rejected_access"], 0)

    def test_el_estado_de_health_sobrevive_al_reinicio_del_servicio(self):
        _, trabajo = self.servidor.enviar("--", "echo", "hola")
        self.servidor.esperar_estado_final(trabajo["id"])
        antes = salud(self.tcp)
        self.servidor.reiniciar()
        esperar_puerto(self.puerto)
        despues = salud(self.tcp)
        self.assertEqual(despues["jobs_by_state"]["SUCCEEDED"], 1)
        self.assertEqual(despues["database"], "ok")
        self.assertEqual((despues["max_jobs"], despues["queue_size"]), (2, 1))
        self.assertLess(despues["uptime_seconds"], antes["uptime_seconds"] + 60)


class ConfiguracionPorDefectoTest(unittest.TestCase):

    def test_sin_opciones_los_limites_son_3_y_10(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        servidor.iniciar()
        h = salud(servidor.cli)
        self.assertEqual((h["max_jobs"], h["queue_size"]), (3, 10))


def sockets_en_escucha(pid):
    """Puertos TCP en LISTEN que tiene abiertos el proceso (Linux: /proc). None si no se puede ver."""
    try:
        inodos = set()
        for fd in os.listdir("/proc/%d/fd" % pid):
            destino = os.readlink("/proc/%d/fd/%s" % (pid, fd))
            if destino.startswith("socket:["):
                inodos.add(destino[8:-1])
        puertos, leidas = [], 0
        for tabla in ("/proc/net/tcp", "/proc/net/tcp6"):   # tcp6 no existe sin IPv6
            try:
                f = open(tabla)
            except FileNotFoundError:
                continue
            with f:
                leidas += 1
                next(f)
                for linea in f:
                    campos = linea.split()
                    if campos[3] == "0A" and campos[9] in inodos:
                        puertos.append(int(campos[1].split(":")[1], 16))
        return puertos if leidas else None
    except OSError:
        return None


class ListenTest(unittest.TestCase):

    def test_sin_listen_el_proceso_no_tiene_puertos_tcp_en_escucha(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        servidor.iniciar()
        puertos = sockets_en_escucha(servidor.proceso.pid)
        if puertos is None:
            self.skipTest("no se puede leer /proc en este sistema")
        self.assertEqual(puertos, [])
        self.assertNotIn("(TCP)", servidor.log())

    def test_con_listen_el_puerto_indicado_queda_abierto(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        puerto = puerto_libre()
        servidor.iniciar(opciones=["--listen", "127.0.0.1:%d" % puerto])
        esperar_puerto(puerto)
        self.assertIn("127.0.0.1:%d (TCP)" % puerto, servidor.log())
        abiertos = sockets_en_escucha(servidor.proceso.pid)
        if abiertos is not None:
            self.assertEqual(abiertos, [puerto])

    def test_listen_sin_valor_usa_el_puerto_por_defecto_7070(self):
        from jobrunner.server import parse_args
        self.assertEqual(parse_args(["--listen"]).listen, "127.0.0.1:7070")
        self.assertIsNone(parse_args([]).listen)

    def test_al_cerrar_el_servicio_el_puerto_queda_libre(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        puerto = puerto_libre()
        servidor.iniciar(opciones=["--listen", "127.0.0.1:%d" % puerto])
        esperar_puerto(puerto)
        servidor.detener()
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", puerto), timeout=2).close()


class OpcionesInvalidasTest(unittest.TestCase):
    """El servidor rechaza una configuracion invalida con un mensaje y el codigo de uso (2)."""

    def arrancar(self, *opciones):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run(
                [sys.executable, "-m", "jobrunner.server", os.path.join(d, "s.sock"), *opciones],
                capture_output=True, text=True, env=entorno(), cwd=str(RAIZ), timeout=20)
        return r.returncode, r.stderr

    def test_max_jobs_menor_que_1(self):
        for valor in ("0", "-2"):
            with self.subTest(valor=valor):
                codigo, err = self.arrancar("--max-jobs", valor)
                self.assertEqual(codigo, 2)
                self.assertIn("--max-jobs debe ser al menos 1", err)

    def test_queue_size_negativo(self):
        codigo, err = self.arrancar("--queue-size", "-1")
        self.assertEqual(codigo, 2)
        self.assertIn("--queue-size no puede ser negativo", err)

    def test_valores_que_no_son_numeros(self):
        for opcion in ("--max-jobs", "--queue-size"):
            with self.subTest(opcion=opcion):
                codigo, err = self.arrancar(opcion, "muchos")
                self.assertEqual(codigo, 2)
                self.assertIn("invalid int value", err)

    def test_listen_que_abriria_el_servicio_a_cualquier_red(self):
        codigo, err = self.arrancar("--listen", "0.0.0.0:7070")
        self.assertEqual(codigo, 2)
        self.assertIn("no se puede escuchar en 0.0.0.0", err)

    def test_allow_sin_listen(self):
        codigo, err = self.arrancar("--allow", "127.0.0.1")
        self.assertEqual(codigo, 2)
        self.assertIn("--allow solo tiene efecto con --listen", err)


class LimitesRespetadosTest(unittest.TestCase):

    def test_max_jobs_1_ejecuta_de_uno_en_uno(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        servidor.iniciar(opciones=["--max-jobs", "1", "--queue-size", "5"])
        estados = [servidor.enviar("--", "sleep", "30")[1]["state"] for _ in range(3)]
        self.assertEqual(estados, ["RUNNING", "QUEUED", "QUEUED"])
        h = salud(servidor.cli)
        self.assertEqual((h["running"], h["queued"], h["max_jobs"], h["queue_size"]), (1, 2, 1, 5))

    def test_queue_size_0_rechaza_en_cuanto_no_hay_lugar_para_correr(self):
        servidor = ServidorDePrueba()
        self.addCleanup(servidor.limpiar)
        servidor.iniciar(opciones=["--max-jobs", "1", "--queue-size", "0"])
        self.assertEqual(servidor.enviar("--", "sleep", "30")[0], 0)
        codigo, respuesta = servidor.enviar("--", "sleep", "30")
        self.assertEqual(codigo, 1)
        self.assertIn("cola llena (capacidad 0)", respuesta["error"])


if __name__ == "__main__":
    unittest.main()
