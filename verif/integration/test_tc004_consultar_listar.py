"""TC-004 — Consultar estado y listar trabajos (RF-08, RF-09, RNF-05).

Automatiza verif/test-cases/TC-004.md: servidor y CLI reales, por socket Unix.
El caso manual usa `sleep 10`; aquí se usa `sleep 2` para que la prueba dure
segundos. El comportamiento comprobado es el mismo.
"""
import time
import unittest

from helpers import PruebaDeIntegracion


class TestTC004ConsultarListar(PruebaDeIntegracion):

    def test_status_inmediato_es_running(self):
        _, trabajo = self.servidor.enviar("--", "sleep", "2")
        self.assertEqual(self.servidor.estado(trabajo["id"])["state"], "RUNNING")

    def test_list_incluye_el_trabajo_con_su_estado(self):
        _, trabajo = self.servidor.enviar("--", "sleep", "2")
        lista = {t["id"]: t["state"] for t in self.servidor.listar()}
        self.assertIn(trabajo["id"], lista)
        self.assertEqual(lista[trabajo["id"]], "RUNNING")

    def test_al_terminar_status_es_succeeded_con_codigo_0(self):
        _, trabajo = self.servidor.enviar("--", "sleep", "2")
        final = self.servidor.esperar_estado_final(trabajo["id"])
        self.assertEqual(final["state"], "SUCCEEDED")
        self.assertEqual(final["exit_code"], 0)
        self.assertIsNotNone(final["finished_at"])

    def test_trabajo_con_error_termina_failed_con_su_codigo(self):
        _, trabajo = self.servidor.enviar("--", "sh", "-c", "exit 3")
        final = self.servidor.esperar_estado_final(trabajo["id"])
        self.assertEqual(final["state"], "FAILED")
        self.assertEqual(final["exit_code"], 3)

    def test_list_filtra_por_estado(self):
        _, largo = self.servidor.enviar("--", "sleep", "30")
        _, corto = self.servidor.enviar("--", "true")
        self.servidor.esperar_estado_final(corto["id"])
        en_ejecucion = {t["id"] for t in self.servidor.listar("RUNNING")}
        terminados = {t["id"] for t in self.servidor.listar("SUCCEEDED")}
        self.assertIn(largo["id"], en_ejecucion)
        self.assertNotIn(corto["id"], en_ejecucion)
        self.assertIn(corto["id"], terminados)

    def test_status_de_id_inexistente_da_error_y_codigo_distinto_de_cero(self):
        codigo, respuesta = self.servidor.cli_json("status", "no-existe")
        self.assertIn("error", respuesta)
        self.assertNotEqual(codigo, 0)

    def test_status_y_list_exitosos_terminan_con_codigo_0(self):
        # RF-17: códigos de salida adecuados para éxito.
        _, trabajo = self.servidor.enviar("--", "sleep", "2")
        c_status, _ = self.servidor.cli_json("status", trabajo["id"])
        c_list, _ = self.servidor.cli_json("list")
        self.assertEqual((c_status, c_list), (0, 0))

    def test_consulta_responde_en_menos_de_1_segundo_con_100_trabajos(self):
        # RNF-05: máximo 1 s con 100 trabajos almacenados.
        ids = [self.servidor.enviar("--", "true")[1]["id"] for _ in range(100)]
        self.servidor.esperar_estado_final(ids[-1])
        inicio = time.monotonic()
        self.servidor.cli_json("status", ids[0])
        duracion = time.monotonic() - inicio
        self.assertLess(duracion, 1.0, "status tardó %.2f s con 100 trabajos" % duracion)


if __name__ == "__main__":
    unittest.main()
