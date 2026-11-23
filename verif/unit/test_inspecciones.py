"""Pruebas de verif/scripts/inspecciones.py (inspecciones de RNF-16, RNF-17, RNF-18 y RNF-34).

Cada prueba arma un repositorio mínimo en un directorio temporal, lo estropea de una sola
manera y comprueba que la inspección correspondiente lo detecta. Así se sabe que la
inspección puede fallar: una inspección que siempre da PASS no prueba nada.
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "verif" / "scripts"))
import inspecciones  # noqa: E402

ADR = """# ADR-0002: Algo

**Estado:** Aceptado

## Contexto
x

## Alternativas consideradas
x

## Decisión
x

## Consecuencias

**Positivas**
- algo

**Riesgos**
- Un riesgo — Mitigación: una medida — Prueba: TC-007.

## Decisiones abiertas
Ninguna

## Requisitos afectados
RNF-11

## Evidencia
x
"""

SERVIDOR = '''def handle_request(manager, request):
    cmd = request.get("cmd")
    if cmd == "submit":
        pass
    if cmd == "status":
        pass
'''

PROTOCOLO = "Comandos: `submit` y `status`.\n"
MATRIZ = "| TC-007 | Reinicio | PASS |\n"
SEGURIDAD = "# Seguridad\n\n## Modelo de amenazas\nx\n\n## Mínimo privilegio\nel servicio corre sin root\n"


def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def repo_correcto(raiz):
    for nombre in ("a", "b", "c", "d", "e"):
        escribir(raiz / "src" / "jobrunner" / (nombre + ".py"), "x = 1\n")
    escribir(raiz / "src" / "jobrunner" / "server.py", SERVIDOR)
    escribir(raiz / "docs" / "decisions" / "0002-algo.md", ADR)
    for guia in inspecciones.GUIAS:
        escribir(raiz / guia, "guía\n")
    escribir(raiz / "docs" / "technical-guide" / "protocolo-y-persistencia.md", PROTOCOLO)
    escribir(raiz / "verif" / "verification-plan" / "matriz-trazabilidad.md", MATRIZ)
    escribir(raiz / "docs" / "technical-guide" / "seguridad.md", SEGURIDAD)
    escribir(raiz / "scripts" / "run.sh", "#!/usr/bin/env bash\nexec python3 -m jobrunner.server\n")


class InspeccionesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.raiz = Path(self._tmp.name)
        repo_correcto(self.raiz)

    @staticmethod
    def main(argumentos):
        with contextlib.redirect_stdout(io.StringIO()):   # la salida no es parte de la prueba
            return inspecciones.main(argumentos)

    def estados(self):
        return {i: e for i, _, e, _, _ in inspecciones.inspeccionar(self.raiz)}

    def detalle(self, ident):
        return "\n".join(d for i, _, _, d, _ in inspecciones.inspeccionar(self.raiz) if i == ident for d in d)

    # -- el caso sano --------------------------------------------------------
    def test_un_repositorio_correcto_pasa_las_cuatro(self):
        self.assertEqual(self.estados(), {"INS-016": "PASS", "INS-017": "PASS", "INS-018": "PASS", "INS-034": "PASS"})

    # -- RNF-16 --------------------------------------------------------------
    def test_sin_documento_de_seguridad_queda_bloqueada_y_dice_cual_falta(self):
        (self.raiz / "docs" / "technical-guide" / "seguridad.md").unlink()
        self.assertEqual(self.estados()["INS-016"], "BLOCKED")
        self.assertIn("seguridad.md", self.detalle("INS-016"))

    def test_seguridad_sin_modelo_de_amenazas_falla(self):
        escribir(self.raiz / "docs" / "technical-guide" / "seguridad.md", "# Seguridad\nsolo el mínimo privilegio\n")
        self.assertEqual(self.estados()["INS-016"], "FAIL")
        self.assertIn("modelo de amenazas", self.detalle("INS-016"))

    def test_codigo_que_pide_sudo_falla(self):
        escribir(self.raiz / "scripts" / "setup.sh", "sudo apt install algo\n")
        self.assertEqual(self.estados()["INS-016"], "FAIL")
        self.assertIn("setup.sh:1", self.detalle("INS-016"))

    def test_codigo_con_setuid_o_permisos_777_falla(self):
        escribir(self.raiz / "src" / "jobrunner" / "a.py", "import os\nos.setuid(0)\n")
        self.assertEqual(self.estados()["INS-016"], "FAIL")
        escribir(self.raiz / "src" / "jobrunner" / "a.py", "x = 1\n")
        escribir(self.raiz / "src" / "jobrunner" / "b.py", "import os\nos.chmod('s', 0o777)\n")
        self.assertEqual(self.estados()["INS-016"], "FAIL")

    def test_un_comentario_que_menciona_sudo_no_cuenta(self):
        escribir(self.raiz / "scripts" / "run.sh", "# No uses sudo: el servicio no lo necesita\n")
        self.assertEqual(self.estados()["INS-016"], "PASS")

    # -- RNF-17 --------------------------------------------------------------
    def test_un_modulo_de_mas_de_400_lineas_falla(self):
        escribir(self.raiz / "src" / "jobrunner" / "a.py", "x = 1\n" * (inspecciones.LIMITE_LINEAS + 1))
        self.assertEqual(self.estados()["INS-017"], "FAIL")
        self.assertIn("a.py", self.detalle("INS-017"))

    def test_un_modulo_justo_en_el_limite_pasa(self):
        escribir(self.raiz / "src" / "jobrunner" / "a.py", "x = 1\n" * inspecciones.LIMITE_LINEAS)
        self.assertEqual(self.estados()["INS-017"], "PASS")

    def test_poco_codigo_repartido_en_menos_modulos_de_los_minimos_falla(self):
        for nombre in ("b", "c", "d", "e"):
            (self.raiz / "src" / "jobrunner" / (nombre + ".py")).unlink()
        self.assertEqual(self.estados()["INS-017"], "FAIL")

    # -- RNF-18 --------------------------------------------------------------
    def test_un_adr_sin_una_seccion_falla(self):
        escribir(self.raiz / "docs" / "decisions" / "0002-algo.md", ADR.replace("## Evidencia\nx\n", ""))
        self.assertEqual(self.estados()["INS-018"], "FAIL")
        self.assertIn("## Evidencia", self.detalle("INS-018"))

    def test_falta_una_guia_falla(self):
        (self.raiz / "docs" / "user-guide" / "guia-de-usuario.md").unlink()
        self.assertEqual(self.estados()["INS-018"], "FAIL")

    def test_un_comando_del_servidor_sin_documentar_falla(self):
        escribir(self.raiz / "src" / "jobrunner" / "server.py", SERVIDOR + '    if cmd == "health":\n        pass\n')
        self.assertEqual(self.estados()["INS-018"], "FAIL")
        self.assertIn("health", self.detalle("INS-018"))

    def test_el_comando_nuevo_documentado_pasa(self):
        escribir(self.raiz / "src" / "jobrunner" / "server.py", SERVIDOR + '    if cmd == "health":\n        pass\n')
        escribir(self.raiz / "docs" / "technical-guide" / "protocolo-y-persistencia.md", PROTOCOLO + "`health`\n")
        self.assertEqual(self.estados()["INS-018"], "PASS")

    # -- RNF-34 --------------------------------------------------------------
    def test_un_adr_sin_riesgos_falla(self):
        escribir(self.raiz / "docs" / "decisions" / "0002-algo.md",
                 ADR.replace("**Riesgos**\n- Un riesgo — Mitigación: una medida — Prueba: TC-007.\n", ""))
        self.assertEqual(self.estados()["INS-034"], "FAIL")

    def test_un_riesgo_sin_prueba_falla(self):
        escribir(self.raiz / "docs" / "decisions" / "0002-algo.md", ADR.replace(" — Prueba: TC-007.", ""))
        self.assertEqual(self.estados()["INS-034"], "FAIL")
        self.assertIn("sin «Prueba:»", self.detalle("INS-034"))

    def test_un_riesgo_sin_mitigacion_falla(self):
        escribir(self.raiz / "docs" / "decisions" / "0002-algo.md", ADR.replace(" — Mitigación: una medida", ""))
        self.assertEqual(self.estados()["INS-034"], "FAIL")

    def test_una_prueba_que_no_esta_en_la_matriz_falla(self):
        escribir(self.raiz / "docs" / "decisions" / "0002-algo.md", ADR.replace("TC-007", "TC-999"))
        self.assertEqual(self.estados()["INS-034"], "FAIL")
        self.assertIn("TC-999", self.detalle("INS-034"))

    def test_una_prueba_ninguna_se_acepta_pero_queda_anotada(self):
        escribir(self.raiz / "docs" / "decisions" / "0002-algo.md", ADR.replace("TC-007.", "ninguna en este hito."))
        self.assertEqual(self.estados()["INS-034"], "PASS")
        self.assertIn("riesgo aceptado", self.detalle("INS-034"))

    def test_el_adr_de_lenguaje_no_se_exige(self):
        escribir(self.raiz / "docs" / "decisions" / "0001-lenguaje.md", ADR.replace("**Riesgos**\n- Un riesgo — Mitigación: una medida — Prueba: TC-007.\n", ""))
        self.assertEqual(self.estados()["INS-034"], "PASS")

    # -- la línea de comandos ---------------------------------------------------
    def test_main_guarda_el_tsv_y_sale_con_0_si_nada_falla(self):
        tsv = self.raiz / "ins.tsv"
        codigo = self.main(["--raiz", str(self.raiz), "--tsv", str(tsv)])
        self.assertEqual(codigo, 0)
        filas = [l.split("\t") for l in tsv.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([f[:2] for f in filas],
                         [["INS-016", "PASS"], ["INS-017", "PASS"], ["INS-018", "PASS"], ["INS-034", "PASS"]])

    def test_main_sale_con_1_si_alguna_falla_pero_no_si_solo_hay_bloqueadas(self):
        (self.raiz / "docs" / "technical-guide" / "seguridad.md").unlink()
        self.assertEqual(self.main(["--raiz", str(self.raiz)]), 0)   # BLOCKED no es fallo
        escribir(self.raiz / "src" / "jobrunner" / "a.py", "x = 1\n" * 500)
        self.assertEqual(self.main(["--raiz", str(self.raiz)]), 1)

    # -- el repositorio real -----------------------------------------------------
    def test_el_repositorio_real_no_tiene_inspecciones_que_fallen(self):
        for ident, titulo, estado, detalle, _ in inspecciones.inspeccionar(RAIZ):
            self.assertNotEqual(estado, "FAIL", "%s %s:\n%s" % (ident, titulo, "\n".join(detalle)))


if __name__ == "__main__":
    unittest.main()
