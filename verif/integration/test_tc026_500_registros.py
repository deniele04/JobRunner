"""TC-026: 500 trabajos registrados, servidor reiniciado, todos con sus metadatos (RNF-06).

Con el servidor real: se envían 500 trabajos (cada uno con su request_id), se espera a
que terminen, se guarda lo que informa `list`, se reinicia el servidor (Ctrl+C y nuevo
arranque sobre el mismo directorio de datos) y se comprueba, campo por campo, que los 500
siguen con sus metadatos y sus archivos de salida. Se envían por una sola conexión: el
protocolo admite varias solicitudes por conexión (ADR-0009) y así la prueba no tarda.
"""
import json
import socket
import time
import unittest

from helpers import PruebaDeIntegracion, ServidorDePrueba

TOTAL = 500
CADA_CUANTOS_FALLAN = 10   # 1 de cada 10 termina con `exit 3`
OPCIONES = ["--max-jobs", "250", "--queue-size", str(TOTAL)]   # la mitad corre y la mitad espera


def enviar_por_una_conexion(ruta_socket, solicitudes):
    """Envía todas las solicitudes por la misma conexión y devuelve sus respuestas, en orden."""
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(60)
    try:
        s.connect(ruta_socket)
        buffer, respuestas = b"", []
        for solicitud in solicitudes:
            s.sendall((json.dumps(solicitud) + chr(10)).encode("utf-8"))
            while chr(10).encode() not in buffer:
                trozo = s.recv(65536)
                if not trozo:
                    raise AssertionError("el servidor cerró la conexión")
                buffer += trozo
            linea, _, buffer = buffer.partition(chr(10).encode())
            respuestas.append(json.loads(linea.decode("utf-8")))
        return respuestas
    finally:
        s.close()


def por_id(trabajos):
    return {t["id"]: t for t in trabajos}


def cargar_500_trabajos(servidor):
    """Envía los 500 trabajos, espera a que terminen y devuelve lo que informa `list` (por id)."""
    solicitudes = [{"cmd": "submit", "argv": argv_del_trabajo(i), "request_id": "rnf06-%04d" % i}
                   for i in range(TOTAL)]
    respuestas = enviar_por_una_conexion(servidor.socket, solicitudes)
    errores = [r for r in respuestas if "error" in r and "id" not in r]
    assert not errores, "el servidor rechazó envíos: %r" % errores[:3]
    assert len(respuestas) == TOTAL
    fin = time.monotonic() + 60.0
    while time.monotonic() < fin:
        if not [t for t in servidor.listar() if t["state"] in ("QUEUED", "RUNNING")]:
            return por_id(servidor.listar())
        time.sleep(0.2)
    raise AssertionError("los 500 trabajos no terminaron en 60 s")


def argv_del_trabajo(i):
    if i % CADA_CUANTOS_FALLAN == 0:
        return ["sh", "-c", "exit 3"]
    return ["echo", "trabajo-%04d" % i]


class TestTC026QuinientosRegistros(unittest.TestCase):
    """Un solo servidor con los 500 trabajos para todas las pruebas: reiniciarlo no cambia los datos."""

    @classmethod
    def setUpClass(cls):
        cls.servidor = ServidorDePrueba()
        cls.addClassCleanup(cls.servidor.limpiar)
        cls.servidor.iniciar(opciones=OPCIONES)   # el límite de cola por defecto (10) no alcanza
        cls.antes = cargar_500_trabajos(cls.servidor)

    def test_los_500_trabajos_terminan_y_quedan_registrados(self):
        self.assertEqual(len(self.antes), TOTAL)
        estados = {t["state"] for t in self.antes.values()}
        self.assertEqual(estados, {"SUCCEEDED", "FAILED"})
        fallidos = [t for t in self.antes.values() if t["state"] == "FAILED"]
        self.assertEqual(len(fallidos), TOTAL // CADA_CUANTOS_FALLAN)
        self.assertTrue(all(t["exit_code"] == 3 for t in fallidos))

    def test_500_trabajos_sobreviven_al_reinicio_con_todos_sus_metadatos(self):
        self.servidor.reiniciar()
        despues = por_id(self.servidor.listar())
        self.assertEqual(len(despues), TOTAL)
        self.assertEqual(set(despues), set(self.antes), "cambió el conjunto de IDs")
        for job_id, antes in self.antes.items():
            self.assertEqual(despues[job_id], antes, "cambió un campo del trabajo " + job_id)

    def test_cada_metadato_obligatorio_sigue_presente_tras_el_reinicio(self):
        self.servidor.reiniciar()
        trabajos = self.servidor.listar()
        for t in trabajos:
            for campo in ("id", "argv", "state", "created_at", "started_at", "finished_at",
                          "exit_code", "request_id", "stdout_path", "stderr_path"):
                self.assertIsNotNone(t[campo], "falta %s en %s" % (campo, t["id"]))
        self.assertEqual(len({t["request_id"] for t in trabajos}), TOTAL)

    def test_los_archivos_de_salida_siguen_ahi_tras_el_reinicio(self):
        self.servidor.reiniciar()
        for t in self.servidor.listar():
            if t["argv"][0] == "echo":
                with open(t["stdout_path"], encoding="utf-8") as f:
                    self.assertEqual(f.read().strip(), t["argv"][1], t["id"])

    def test_un_segundo_reinicio_no_cambia_nada(self):
        self.servidor.reiniciar()
        self.servidor.reiniciar()
        self.assertEqual(por_id(self.servidor.listar()), self.antes)

    def test_status_por_id_responde_con_los_mismos_datos_tras_el_reinicio(self):
        self.servidor.reiniciar()
        for job_id in list(self.antes)[::25]:   # una muestra de 20 por el CLI real
            respuesta = {k: v for k, v in self.servidor.estado(job_id).items() if k != "v"}   # sin la versión
            self.assertEqual(respuesta, self.antes[job_id])


class TestTC026TrabajoNuevoTrasReiniciar(PruebaDeIntegracion):
    """Aparte, porque agrega un trabajo y los demás casos esperan exactamente 500."""

    def test_un_trabajo_nuevo_tras_el_reinicio_no_borra_los_anteriores(self):
        self.servidor.detener()
        self.servidor.iniciar(opciones=OPCIONES)
        antes = cargar_500_trabajos(self.servidor)
        self.servidor.reiniciar()
        codigo, nuevo = self.servidor.enviar("--", "true")
        self.assertEqual(codigo, 0, nuevo)
        self.servidor.esperar_estado_final(nuevo["id"])
        despues = por_id(self.servidor.listar())
        self.assertEqual(len(despues), TOTAL + 1)
        self.assertNotIn(nuevo["id"], antes)
        for job_id, trabajo in antes.items():
            self.assertEqual(despues[job_id], trabajo)


if __name__ == "__main__":
    unittest.main()
