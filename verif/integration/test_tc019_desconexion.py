"""TC-019: desconexion del cliente (INC-001, RNF-08, decision 8 de la minuta del 20/10/2026).

Con el servidor real, un cliente se desconecta de varias formas: sin enviar nada,
despues de enviar una solicitud completa sin leer la respuesta y a mitad de una
solicitud. El servidor debe seguir atendiendo, aplicar una solicitud completa
una sola vez y no dejar procesos ni descriptores abiertos.
"""
import json
import socket
import time
import unittest

from helpers_procesos import ConLineaBase

SALTO = bytes([10])


def conectar(ruta):
    # Con la cola de conexiones del servidor llena (listen(5)) un connect con
    # timeout falla con EAGAIN; el cliente real bloquea. Se reintenta igual.
    fin = time.monotonic() + 10
    while True:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(10)
        try:
            s.connect(ruta)
            return s
        except BlockingIOError:
            s.close()
            if time.monotonic() > fin:
                raise
            time.sleep(0.05)


def linea(objeto):
    return json.dumps(objeto).encode("utf-8") + SALTO


class TestTC019Desconexion(ConLineaBase):
    def trabajos(self):
        self.assertIsNone(self.servidor.proceso.poll(), "el servidor termino")
        codigo, respuesta = self.servidor.cli_json("list")
        self.assertEqual(codigo, 0)
        return respuesta["jobs"]

    def esperar_trabajos(self, cantidad, limite=5.0):
        fin = time.monotonic() + limite
        while time.monotonic() < fin:
            lista = self.trabajos()
            if len(lista) >= cantidad:
                return lista
            time.sleep(0.1)
        self.fail("no aparecieron %d trabajo(s) en %.0f s" % (cantidad, limite))

    def test_cierra_la_conexion_sin_enviar_nada(self):
        for _ in range(10):
            conectar(self.servidor.socket).close()
        self.assertEqual(self.trabajos(), [])

    def test_cierra_sin_leer_la_respuesta_y_la_solicitud_se_aplica_una_vez(self):
        pedido = {"cmd": "submit", "argv": ["sleep", "300"], "request_id": "tc019-a"}
        cliente = conectar(self.servidor.socket)
        cliente.sendall(linea(pedido))
        cliente.close()
        lista = self.esperar_trabajos(1)
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]["state"], "RUNNING")

        # Reenviar el mismo request_id devuelve el mismo trabajo, no crea otro.
        repetido = self.servidor.solicitud_cruda(json.dumps(pedido) + chr(10))
        self.assertEqual(repetido["id"], lista[0]["id"])
        self.assertEqual(len(self.trabajos()), 1)

        # Cancelarlo y comprobar que no quedan procesos.
        self.servidor.cli("cancel", lista[0]["id"])
        self.servidor.esperar_estado_final(lista[0]["id"])
        self.assertSinZombisNiHuerfanos()

    def test_cierra_a_mitad_de_una_solicitud(self):
        cliente = conectar(self.servidor.socket)
        cliente.sendall(b'{"cmd": "submit", "argv": ["sleep"')   # sin cerrar ni salto de linea
        cliente.close()
        time.sleep(0.5)
        self.assertEqual(self.trabajos(), [])
        self.assertIn("solicitud_invalida", self.bitacora())

    def test_rafaga_de_desconexiones_no_agota_los_descriptores_del_servidor(self):
        antes = self.descriptores_del_servidor()
        for i in range(30):
            cliente = conectar(self.servidor.socket)
            if i % 3 == 0:
                cliente.sendall(linea({"cmd": "list"}))
            elif i % 3 == 1:
                cliente.sendall(bytes([0xFF, 0xFE]) + SALTO)
            cliente.close()
        self.assertEqual(self.trabajos(), [])
        self.assertLessEqual(self.descriptores_del_servidor(), antes + 2)


if __name__ == "__main__":
    unittest.main()
