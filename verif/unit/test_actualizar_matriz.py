"""Pruebas de verif/scripts/actualizar_matriz.py: de resumen.md a la matriz de trazabilidad.

Sin una matriz que se actualiza sola mal, la trazabilidad no vale: aquí se comprueba cómo
se combinan PASS, FAIL, BLOCKED y Pendiente, que las inspecciones (INS) cuentan igual que los
casos de prueba (TC) y que un requisito sin caso ni inspección sigue marcado «Sin TC».
"""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "verif" / "scripts"))
import actualizar_matriz as am  # noqa: E402

RESUMEN = """# Resumen de la ejecución x

| TC | Estado | Evidencia |
|---|---|---|
| TC-001 | PASS | unittest.log |
| TC-002 | FAIL | unittest.log |
| TC-010 | BLOCKED | falta el cliente remoto |
| INS-017 | PASS | inspecciones.log |
| INS-016 | BLOCKED | inspecciones.log |
| Sin zombis ni huérfanos tras las pruebas | PASS | procesos.log |
"""

MATRIZ = """# Matriz

**Última ejecución formal:** `verif/results/viejo/` (ver [resumen](../results/viejo/resumen.md))

| TC | Título | Pruebas automatizadas | Estado |
|---|---|---|---|
| [TC-001](../test-cases/TC-001.md) | Enviar | `a.py` | Pendiente |
| TC-010 | Remoto | `b.py` | Pendiente |
| [INS-017](../inspecciones/INS-017.md) | Código modular | `inspecciones.py` | Pendiente |

| Req ID | Descripción breve | Prioridad | Método | Caso(s) | Evidencia | Resultado | Defecto/Excepción |
|---|---|---|---|---|---|---|---|
| RF-01 | Enviar | Alta | Prueba | [TC-001](../test-cases/TC-001.md) | x | Pendiente | — |
| RF-03 | Cola | Por definir | Prueba | [TC-001](../test-cases/TC-001.md), [TC-002](../test-cases/TC-002.md) | x | Pendiente | — |
| RF-18 | Remoto | Alta | Prueba/Demo | TC-010 | x | Pendiente | — |
| RF-99 | Sin ejecutar | Por definir | Prueba | TC-777 | x | PASS | — |
| RNF-17 | Modular | Por definir | Inspección | [INS-017](../inspecciones/INS-017.md) | x | Pendiente | — |
| RNF-16 | Amenazas | Por definir | Inspección | INS-016, [INS-017](../inspecciones/INS-017.md) | x | Pendiente | — |
| RNF-06 | Sin caso | Por definir | Prueba | sin TC | x | PASS | — |

| ID | Descripción | TC afectado | Estado |
|---|---|---|---|
| DEF-001 | Algo | [TC-001](../test-cases/TC-001.md) | Cerrado |
"""


def celdas(linea):
    return [c.strip() for c in linea.strip().strip("|").split("|")]


class ActualizarMatrizTest(unittest.TestCase):
    def setUp(self):
        self.estados = am.estados_del_resumen(RESUMEN)
        self.texto = am.actualizar_texto(MATRIZ, "20261201-final", self.estados)
        self.filas = {celdas(l)[0].split("]")[0].lstrip("["): celdas(l)
                      for l in self.texto.splitlines() if l.startswith("|")}

    def resultado(self, req):
        return self.filas[req][6]

    def test_lee_casos_e_inspecciones_del_resumen_y_nada_mas(self):
        self.assertEqual(self.estados, {"TC-001": "PASS", "TC-002": "FAIL", "TC-010": "BLOCKED",
                                        "INS-017": "PASS", "INS-016": "BLOCKED"})

    def test_la_tabla_de_casos_recibe_el_estado_de_cada_uno(self):
        self.assertEqual(self.filas["TC-001"][3], "PASS")
        self.assertEqual(self.filas["TC-010"][3], "BLOCKED")
        self.assertEqual(self.filas["INS-017"][3], "PASS")

    def test_un_requisito_con_un_caso_toma_su_estado(self):
        self.assertEqual(self.resultado("RF-01"), "PASS")
        self.assertEqual(self.resultado("RF-18"), "BLOCKED")

    def test_con_varios_casos_gana_el_peor(self):
        self.assertEqual(self.resultado("RF-03"), "FAIL")      # PASS + FAIL
        self.assertEqual(self.resultado("RNF-16"), "BLOCKED")  # BLOCKED + PASS

    def test_las_inspecciones_cuentan_como_casos(self):
        self.assertEqual(self.resultado("RNF-17"), "PASS")

    def test_un_caso_que_no_se_ejecuto_deja_el_requisito_pendiente(self):
        self.assertEqual(self.resultado("RF-99"), "Pendiente")

    def test_un_requisito_sin_caso_ni_inspeccion_dice_sin_tc(self):
        self.assertEqual(self.resultado("RNF-06"), "Sin TC")

    def test_actualiza_la_linea_de_la_ultima_ejecucion_formal(self):
        self.assertIn("`verif/results/20261201-final/` (ver [resumen](../results/20261201-final/resumen.md))", self.texto)
        self.assertNotIn("viejo", self.texto)

    def test_no_toca_la_tabla_de_defectos(self):
        self.assertIn("| DEF-001 | Algo | [TC-001](../test-cases/TC-001.md) | Cerrado |", self.texto)

    def test_la_matriz_real_solo_cita_casos_e_inspecciones_con_estado_conocido(self):
        """Cada caso o inspección que la matriz real cita debe poder salir de verify.sh."""
        texto = (RAIZ / "verif" / "verification-plan" / "matriz-trazabilidad.md").read_text(encoding="utf-8")
        verify = (RAIZ / "verif" / "scripts" / "verify.sh").read_text(encoding="utf-8")
        citados = set(am.CASO.findall(texto))
        for caso in sorted(citados):
            self.assertIn("| %s |" % caso, verify, caso + " está en la matriz pero verify.sh no lo informa")


if __name__ == "__main__":
    unittest.main()
