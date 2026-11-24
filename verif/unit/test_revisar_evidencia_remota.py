"""Pruebas de revisar_evidencia_remota.py (D6: evidencia entre dos equipos)."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "scripts" / "revisar_evidencia_remota.py"
spec = importlib.util.spec_from_file_location("revisar_evidencia_remota", RUTA)
rev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rev)

ARCHIVOS = ["jobrunner.log", "prueba-vpn-servidor.txt", "prueba-vpn-cliente-daniel.txt",
            "health-daniel.json", "configuracion.txt", "resumen.md"]


def crear(carpeta, contenido="ok", omitir=()):
    for nombre in ARCHIVOS:
        if nombre not in omitir:
            texto = contenido + ("\nacceso_rechazado ip=100.64.0.9" if nombre == "jobrunner.log" else "")
            (carpeta / nombre).write_text(texto, encoding="utf-8")


class RevisarEvidenciaRemota(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_carpeta_completa_no_tiene_problemas(self):
        crear(self.dir, "servidor 192.168.1.20 escuchando")
        self.assertEqual(rev.revisar(self.dir), [])

    def test_carpeta_inexistente(self):
        self.assertEqual(len(rev.revisar(self.dir / "nada")), 1)

    def test_avisa_de_cada_archivo_que_falta(self):
        crear(self.dir, omitir=("health-daniel.json", "configuracion.txt"))
        problemas = rev.revisar(self.dir)
        self.assertEqual(len(problemas), 2)
        self.assertTrue(any("health" in p for p in problemas))
        self.assertTrue(any("configuracion" in p for p in problemas))

    def test_un_archivo_vacio_es_un_problema(self):
        crear(self.dir)
        (self.dir / "resumen.md").write_text("", encoding="utf-8")
        self.assertEqual(rev.revisar(self.dir), ["resumen.md está vacío"])

    def test_una_ip_publica_es_un_problema(self):
        crear(self.dir)
        (self.dir / "configuracion.txt").write_text("conectado a 8.8.8.8", encoding="utf-8")
        self.assertTrue(any("8.8.8.8" in p for p in rev.revisar(self.dir)))

    def test_vpn_y_lan_privada_se_aceptan(self):
        crear(self.dir)
        (self.dir / "configuracion.txt").write_text("100.101.2.3 10.0.0.5 172.20.1.1 192.168.0.9", encoding="utf-8")
        self.assertEqual(rev.revisar(self.dir), [])

    def test_sin_acceso_rechazado_en_la_bitacora_es_un_problema(self):
        crear(self.dir)
        (self.dir / "jobrunner.log").write_text("servicio_iniciado", encoding="utf-8")
        self.assertTrue(any("acceso_rechazado" in p for p in rev.revisar(self.dir)))

    def test_la_version_del_kernel_no_se_confunde_con_una_ip(self):
        crear(self.dir)
        (self.dir / "configuracion.txt").write_text("Sistema: Linux 6.6.87.2-microsoft-standard-WSL2", encoding="utf-8")
        self.assertEqual(rev.revisar(self.dir), [])

    def test_los_nombres_de_la_guia_tambien_se_aceptan(self):
        for nombre in ("equipo-servidor-bitacora.log", "equipo-servidor-grabacion.txt", "equipo-cliente-comandos.txt",
                       "health.json", "red.txt", "LEEME.md"):
            (self.dir / nombre).write_text("acceso_rechazado", encoding="utf-8")
        self.assertEqual(rev.revisar(self.dir), [])

    def test_la_evidencia_real_del_repositorio_esta_completa(self):
        carpeta = Path(__file__).resolve().parents[2] / "verif" / "results" / "20261123-remoto"
        if not carpeta.is_dir():
            self.skipTest("todavía no existe la evidencia remota")
        self.assertEqual(rev.revisar(carpeta), [])


if __name__ == "__main__":
    unittest.main()
