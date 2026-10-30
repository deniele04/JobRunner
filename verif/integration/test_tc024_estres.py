"""TC-024: muchos trabajos sin dejar procesos ni fugas (RNF-33, RNF-25, RNF-30).

Con el servidor real: varias oleadas de trabajos cortos (con exito y con fallo) y
una saturacion con cancelacion masiva. Al final no debe haber zombis ni
huerfanos, el servidor no debe haber acumulado descriptores de archivo y debe
seguir respondiendo. Usa los limites por defecto (3 simultaneos y 10 en cola).
"""
import json
import time
import unittest

from helpers_procesos import ConLineaBase

OLEADAS = 5
POR_OLEADA = 10
MARGEN_DESCRIPTORES = 3


class TestTC024Estres(ConLineaBase):
    def enviar_rapido(self, argv, request_id=None):
        pedido = {"cmd": "submit", "argv": argv}
        if request_id:
            pedido["request_id"] = request_id
        return self.servidor.solicitud_cruda(json.dumps(pedido) + chr(10))

    def pedir(self, pedido):
        return self.servidor.solicitud_cruda(json.dumps(pedido) + chr(10))

    def esperar_sin_activos(self, limite=30.0):
        fin = time.monotonic() + limite
        while time.monotonic() < fin:
            activos = [t for t in self.servidor.listar() if t["state"] in ("QUEUED", "RUNNING")]
            if not activos:
                return
            time.sleep(0.2)
        self.fail("seguian %d trabajos activos tras %.0f s" % (len(activos), limite))

    def test_oleadas_de_trabajos_cortos_no_dejan_procesos_ni_fugas(self):
        descriptores_antes = self.descriptores_del_servidor()
        programas = [["true"], ["sh", "-c", "exit 3"], ["sleep", "0.2"]]
        esperados = {"SUCCEEDED": 0, "FAILED": 0}
        for oleada in range(OLEADAS):
            for i in range(POR_OLEADA):
                argv = programas[i % 3]
                respuesta = self.enviar_rapido(argv)
                self.assertNotEqual(list(respuesta), ["error"], respuesta)
                esperados["FAILED" if argv[0] == "sh" else "SUCCEEDED"] += 1
            self.esperar_sin_activos()

        trabajos = self.servidor.listar()
        self.assertEqual(len(trabajos), OLEADAS * POR_OLEADA)
        for estado, cantidad in esperados.items():
            self.assertEqual(len([t for t in trabajos if t["state"] == estado]), cantidad, estado)
        for t in trabajos:
            if t["argv"][0] == "sh":
                self.assertEqual(t["exit_code"], 3)
        self.assertSinZombisNiHuerfanos()
        self.assertLessEqual(self.descriptores_del_servidor(), descriptores_antes + MARGEN_DESCRIPTORES)

    def test_saturacion_y_cancelacion_masiva_no_dejan_procesos(self):
        descriptores_antes = self.descriptores_del_servidor()
        aceptados, rechazados = [], 0
        for _ in range(20):
            respuesta = self.enviar_rapido(["sleep", "300"])
            if list(respuesta) == ["error"]:
                self.assertIn("cola llena", respuesta["error"])
                rechazados += 1
            else:
                aceptados.append(respuesta["id"])
        self.assertEqual(len(aceptados), 13)   # 3 corriendo + 10 en cola
        self.assertEqual(rechazados, 7)
        self.assertEqual(len(self.servidor.listar()), 13)   # los rechazados no se crean

        # Primero los de la cola (no hay proceso que detener), despues los que corren.
        en_cola = [t["id"] for t in self.servidor.listar("QUEUED")]
        corriendo = [t["id"] for t in self.servidor.listar("RUNNING")]
        self.assertEqual((len(en_cola), len(corriendo)), (10, 3))
        for job_id in en_cola + corriendo:
            self.pedir({"cmd": "cancel", "id": job_id})
        self.esperar_sin_activos()

        estados = [t["state"] for t in self.servidor.listar()]
        self.assertEqual(estados.count("CANCELED"), 13, estados)
        self.assertSinZombisNiHuerfanos()
        self.assertLessEqual(self.descriptores_del_servidor(), descriptores_antes + MARGEN_DESCRIPTORES)
        self.assertIsNone(self.servidor.proceso.poll(), "el servidor termino")


if __name__ == "__main__":
    unittest.main()
