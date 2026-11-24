"""DEF-008 (RF-15, RNF-08): un solo servicio por carpeta de datos.

Un segundo servidor sobre la misma carpeta se niega a arrancar sin tocar el socket, la base ni
los trabajos del primero. El candado se libera al cerrar o al morir de golpe el primero.
"""
import signal
import subprocess
import sys
import time
import unittest

from helpers import RAIZ, ServidorDePrueba, entorno


def segundo_servidor(socket, *opciones):
    """Intenta arrancar otro servidor y devuelve el proceso terminado."""
    return subprocess.run(
        [sys.executable, "-m", "jobrunner.server", socket, *opciones],
        capture_output=True, text=True, env=entorno(), cwd=str(RAIZ), timeout=15,
    )


class TestDef008ServicioUnico(unittest.TestCase):
    def setUp(self):
        self.servidor = ServidorDePrueba()
        self.addCleanup(self.servidor.limpiar)
        self.servidor.iniciar()

    def enviar_largo(self):
        codigo, trabajo = self.servidor.cli_json("submit", "--", "sleep", "300")
        self.assertEqual(codigo, 0)
        return trabajo["id"]

    def test_un_segundo_servidor_sobre_la_misma_carpeta_no_arranca(self):
        r = segundo_servidor(self.servidor.socket)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ya hay un servicio JobRunner", r.stderr)

    def test_el_primero_sigue_atendiendo_y_conserva_su_trabajo(self):
        id_trabajo = self.enviar_largo()
        segundo_servidor(self.servidor.socket)
        codigo, estado = self.servidor.cli_json("status", id_trabajo)
        self.assertEqual(codigo, 0)
        self.assertEqual(estado["state"], "RUNNING")   # no se marco FAILED ni se mato
        self.assertIsNone(estado["error"])

    def test_el_segundo_no_borra_el_socket_del_primero(self):
        segundo_servidor(self.servidor.socket)
        self.assertEqual(self.servidor.cli_json("list")[0], 0)

    def test_otro_nombre_de_socket_en_la_misma_carpeta_tambien_se_rechaza(self):
        otro = str(self.servidor.directorio / "otro.sock")
        r = segundo_servidor(otro)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ya hay un servicio JobRunner", r.stderr)
        self.assertFalse((self.servidor.directorio / "otro.sock").exists())

    def test_una_carpeta_distinta_si_puede_tener_su_propio_servicio(self):
        otro = ServidorDePrueba()
        self.addCleanup(otro.limpiar)
        otro.iniciar()
        self.assertEqual(otro.cli_json("list")[0], 0)
        self.assertEqual(self.servidor.cli_json("list")[0], 0)

    def test_un_servidor_con_tcp_tampoco_puede_arrancar_sobre_la_misma_carpeta(self):
        r = segundo_servidor(self.servidor.socket, "--listen", "127.0.0.1:0")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ya hay un servicio JobRunner", r.stderr)

    def test_tras_un_cierre_ordenado_se_puede_volver_a_iniciar(self):
        self.servidor.detener(senal=signal.SIGINT)
        self.servidor.iniciar()
        self.assertEqual(self.servidor.cli_json("list")[0], 0)

    def test_tras_morir_de_golpe_el_candado_no_queda_tomado(self):
        id_trabajo = self.enviar_largo()
        self.servidor.matar()   # SIGKILL: sin cierre ordenado
        self.servidor.iniciar()   # no debe rechazarse por un candado viejo
        codigo, estado = self.servidor.cli_json("status", id_trabajo)
        self.assertEqual(codigo, 0)
        self.assertEqual(estado["state"], "FAILED")   # la recuperacion de siempre (ADR-0005)
        self.assertEqual(estado["error"], "interrumpido por reinicio")

    def test_el_trabajo_no_hereda_el_candado(self):
        """Si el servidor muere y su trabajo sigue vivo, otro servidor debe poder arrancar."""
        self.enviar_largo()
        self.servidor.matar()
        time.sleep(0.3)
        self.servidor.iniciar()   # el sleep huerfano seguiria vivo; el candado no debe seguir tomado
        self.assertEqual(self.servidor.cli_json("list")[0], 0)


if __name__ == "__main__":
    unittest.main()
