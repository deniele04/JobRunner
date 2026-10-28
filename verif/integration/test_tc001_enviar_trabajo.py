"""TC-001 — Enviar un trabajo válido (RF-01, RF-02).

Automatiza verif/test-cases/TC-001.md: servidor y CLI reales, por socket Unix.
"""
import unittest

from helpers import PruebaDeIntegracion


class TestTC001EnviarTrabajo(PruebaDeIntegracion):

    def test_submit_devuelve_un_id(self):
        _, trabajo = self.servidor.enviar("--", "sleep", "10")
        self.assertIn("id", trabajo, "submit no devolvió un ID: %r" % trabajo)
        self.assertTrue(trabajo["id"], "el ID está vacío")
        self.assertEqual(trabajo["argv"], ["sleep", "10"])

    def test_submit_exitoso_termina_con_codigo_0(self):
        # RF-17: el cliente debe dar códigos de salida adecuados para éxito y error.
        codigo, _ = self.servidor.enviar("--", "sleep", "10")
        self.assertEqual(codigo, 0, "un submit exitoso debe terminar con código 0")

    def test_dos_submit_devuelven_ids_distintos(self):
        _, a = self.servidor.enviar("--", "sleep", "10")
        _, b = self.servidor.enviar("--", "sleep", "10")
        self.assertNotEqual(a["id"], b["id"])

    def test_status_reconoce_el_id_devuelto(self):
        _, trabajo = self.servidor.enviar("--", "sleep", "10")
        consultado = self.servidor.estado(trabajo["id"])
        self.assertEqual(consultado.get("id"), trabajo["id"])
        self.assertIn(consultado.get("state"), ("QUEUED", "RUNNING"))

    def test_submit_sin_comando_se_rechaza(self):
        # RF-02: rechazar entradas vacías con un mensaje útil.
        codigo, _, err = self.servidor.cli("submit")
        self.assertNotEqual(codigo, 0)
        self.assertIn("argv", err, "el mensaje de error no indica qué falta")

    def test_solicitud_mal_formada_no_tumba_al_servicio(self):
        # RF-02 / RNF-08: una solicitud inválida no termina el servicio.
        respuesta = self.servidor.solicitud_cruda("esto no es json\n")
        self.assertIn("error", respuesta)
        _, trabajo = self.servidor.enviar("--", "true")
        self.assertIn("id", trabajo, "el servidor dejó de responder tras una solicitud inválida")
        self.assertIsNone(self.servidor.proceso.poll(), "el servidor terminó")


if __name__ == "__main__":
    unittest.main()
