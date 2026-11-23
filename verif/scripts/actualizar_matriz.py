"""Actualiza la columna de resultado de la matriz de trazabilidad con una ejecución.

Uso: python3 verif/scripts/actualizar_matriz.py <run-id>

Lee verif/results/<run-id>/resumen.md (estado de cada TC y de cada inspección INS)
y reescribe, en verif/verification-plan/matriz-trazabilidad.md:
  - la columna Estado de la tabla de casos de prueba y de inspecciones;
  - la columna Resultado de cada RF y RNF, combinando los estados de sus casos
    (TC-NNN) e inspecciones (INS-NNN): FAIL si alguno falla, si no BLOCKED si
    alguno está bloqueado, si no Pendiente si alguno no se ejecutó en esa corrida,
    y PASS si todos pasan;
  - la línea «Última ejecución formal».
Un requisito sin caso ni inspección queda en «Sin TC».
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MATRIZ = RAIZ / "verif" / "verification-plan" / "matriz-trazabilidad.md"
# Un caso de prueba (TC-NNN) o una inspección (INS-NNN).
CASO = re.compile(r"(?:TC|INS)-\d{3}")


def leer_resumen(run_id):
    ruta = RAIZ / "verif" / "results" / run_id / "resumen.md"
    if not ruta.exists():
        sys.exit("No existe " + str(ruta))
    return estados_del_resumen(ruta.read_text(encoding="utf-8"))


def estados_del_resumen(texto):
    estados = {}
    for linea in texto.splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) >= 2 and CASO.fullmatch(celdas[0]):
            estados[celdas[0]] = celdas[1]
    return estados


def combinar(tcs, estados):
    if not tcs:
        return "Sin TC"
    valores = [estados.get(t, "Pendiente") for t in tcs]
    for malo in ("FAIL", "BLOCKED", "Pendiente"):
        if malo in valores:
            return malo
    return "PASS"


def actualizar_texto(texto, run_id, estados):
    """Devuelve el texto de la matriz con los estados de `estados` (caso -> estado)."""
    salida = []
    for linea in texto.splitlines():
        if linea.startswith("**Última ejecución formal:**"):
            linea = ("**Última ejecución formal:** `verif/results/%s/` "
                     "(ver [resumen](../results/%s/resumen.md))" % (run_id, run_id))
        elif linea.startswith("|"):
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            if celdas and re.fullmatch(r"(RF|RNF)-\d{2}", celdas[0]) and len(celdas) == 8:
                celdas[6] = combinar(CASO.findall(celdas[4]), estados)
                linea = "| " + " | ".join(celdas) + " |"
            elif celdas and CASO.fullmatch(re.sub(r"[\[\]]|\(.*\)", "", celdas[0])) and len(celdas) == 4:
                tc = re.sub(r"[\[\]]|\(.*\)", "", celdas[0])
                celdas[3] = estados.get(tc, "Pendiente")
                linea = "| " + " | ".join(celdas) + " |"
        salida.append(linea)
    return "\n".join(salida) + "\n"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run_id = sys.argv[1]
    estados = leer_resumen(run_id)
    MATRIZ.write_text(actualizar_texto(MATRIZ.read_text(encoding="utf-8"), run_id, estados), encoding="utf-8")
    print("Matriz actualizada con", run_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
