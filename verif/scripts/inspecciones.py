"""Inspecciones documentales automatizadas: RNF-16, RNF-17, RNF-18 y RNF-34.

El PDF 05 asigna estos cuatro requisitos al método «Inspección» y no les da caso de
prueba. Cada inspección tiene su criterio escrito en `verif/inspecciones/INS-0NN.md` y
aquí se comprueba lo que se puede comprobar por máquina, para que el resultado salga de
`verify.sh` y deje evidencia, en lugar de ser una opinión.

Uso:
    python3 verif/scripts/inspecciones.py [--raiz RUTA] [--tsv ARCHIVO]

Escribe en la salida estándar el detalle de cada inspección. Con --tsv guarda además una
línea por inspección: ID<TAB>ESTADO<TAB>resumen.

Estados: PASS (cumple), FAIL (no cumple) y BLOCKED (falta un documento que debe aportar
otra persona del equipo; el detalle dice cuál). Código de salida: 1 si alguna falla;
BLOCKED no cuenta como fallo, igual que en verify.sh.

Solo biblioteca estándar (ADR-0001).
"""
import argparse
import re
import sys
from pathlib import Path

PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"

# RNF-17: ningún módulo pasa de este tamaño sin justificarlo, y el código no es un solo archivo.
LIMITE_LINEAS = 400
MINIMO_MODULOS = 5

# RNF-18: secciones que debe tener todo ADR (plantilla docs/decisions/template.md).
SECCIONES_ADR = ("## Contexto", "## Alternativas consideradas", "## Decisión", "## Consecuencias",
                 "## Requisitos afectados", "## Evidencia")
GUIAS = ("docs/technical-guide/arquitectura.md", "docs/technical-guide/modelo-estados.md",
         "docs/technical-guide/protocolo-y-persistencia.md", "docs/user-guide/guia-de-usuario.md")

# RNF-16: nada en el código ni en los scripts debe pedir más privilegios de los que da el usuario.
PRIVILEGIOS = re.compile(r"\bsudo\b|os\.set(?:e)?[ug]id|os\.chown|os\.setgroups|0o?777")

# RNF-34: el ADR 0001 es la elección de lenguaje; no decide seguridad, consistencia ni recuperación.
ADR_SIN_RIESGO = ("0001",)


def _leer(ruta):
    return Path(ruta).read_text(encoding="utf-8", errors="replace")


def _modulos(raiz):
    return sorted(p for p in (raiz / "src" / "jobrunner").glob("*.py") if p.name != "__init__.py")


def _adrs(raiz):
    return sorted(p for p in (raiz / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md"))


def _seccion(texto, titulo):
    """Texto de una sección «## titulo» hasta la siguiente «## »."""
    m = re.search(r"^## " + re.escape(titulo) + r"\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    return m.group(1) if m else ""


def rnf16(raiz):
    """Mínimo privilegio y modelo de amenazas básico: documento de seguridad y código sin privilegios."""
    detalle = []
    guias = sorted(raiz.glob("docs/**/seguridad.md"))
    if not guias:
        return BLOCKED, ["Falta docs/**/seguridad.md (modelo de amenazas y mínimo privilegio, "
                         "tarea J7 de Josué). Sin ese documento no se puede inspeccionar RNF-16."], \
            "falta seguridad.md"
    texto = _leer(guias[0]).lower()
    estado = PASS
    for tema in ("modelo de amenazas", "privilegio"):
        if tema in texto:
            detalle.append("OK  %s trata «%s»" % (guias[0].relative_to(raiz), tema))
        else:
            estado = FAIL
            detalle.append("FALLA  %s no trata «%s»" % (guias[0].relative_to(raiz), tema))
    archivos = [p for p in list((raiz / "src").rglob("*.py")) + list((raiz / "scripts").glob("*"))
                if p.is_file()]
    for ruta in archivos:
        for n, linea in enumerate(_leer(ruta).splitlines(), 1):
            if PRIVILEGIOS.search(linea) and not linea.lstrip().startswith("#"):
                estado = FAIL
                detalle.append("FALLA  %s:%d pide privilegios: %s" % (ruta.relative_to(raiz), n, linea.strip()))
    if estado == PASS:
        detalle.append("OK  %d archivos de src/ y scripts/ sin sudo, setuid, chown ni permisos 777" % len(archivos))
    return estado, detalle, "documento de seguridad y código sin privilegios" if estado == PASS else "no cumple"


def rnf17(raiz):
    """Código modular: varios módulos, ninguno monolítico."""
    modulos = _modulos(raiz)
    detalle, estado = [], PASS
    if len(modulos) < MINIMO_MODULOS:
        estado = FAIL
        detalle.append("FALLA  hay %d módulos en src/jobrunner (mínimo %d)" % (len(modulos), MINIMO_MODULOS))
    for ruta in modulos:
        lineas = len(_leer(ruta).splitlines())
        if lineas > LIMITE_LINEAS:
            estado = FAIL
            detalle.append("FALLA  %s tiene %d líneas (límite %d)" % (ruta.name, lineas, LIMITE_LINEAS))
        else:
            detalle.append("OK  %s: %d líneas" % (ruta.name, lineas))
    return estado, detalle, "%d módulos, ninguno de más de %d líneas" % (len(modulos), LIMITE_LINEAS) \
        if estado == PASS else "no cumple"


def rnf18(raiz):
    """Interfaces y decisiones documentadas: ADR completos, guías y cada comando del servidor en la guía del protocolo."""
    detalle, estado = [], PASS
    adrs = _adrs(raiz)
    if not adrs:
        return FAIL, ["FALLA  no hay ADR en docs/decisions/"], "sin ADR"
    for ruta in adrs:
        texto = _leer(ruta)
        faltan = [s for s in SECCIONES_ADR if s not in texto]
        if "**Estado:**" not in texto:
            faltan.append("**Estado:**")
        if faltan:
            estado = FAIL
            detalle.append("FALLA  %s sin: %s" % (ruta.name, ", ".join(faltan)))
    if estado == PASS:
        detalle.append("OK  %d ADR con todas sus secciones" % len(adrs))
    for guia in GUIAS:
        if (raiz / guia).is_file():
            detalle.append("OK  existe " + guia)
        else:
            estado = FAIL
            detalle.append("FALLA  no existe " + guia)
    servidor = raiz / "src" / "jobrunner" / "server.py"
    protocolo = raiz / "docs" / "technical-guide" / "protocolo-y-persistencia.md"
    if servidor.is_file() and protocolo.is_file():
        comandos = sorted(set(re.findall(r'cmd == "(\w+)"', _leer(servidor))))
        guia = _leer(protocolo)
        for comando in comandos:
            if re.search(r"(?<![\w])" + re.escape(comando) + r"(?![\w])", guia):
                detalle.append("OK  la guía del protocolo documenta el comando «%s»" % comando)
            else:
                estado = FAIL
                detalle.append("FALLA  el comando «%s» del servidor no aparece en protocolo-y-persistencia.md" % comando)
    return estado, detalle, "%d ADR y %d guías" % (len(adrs), len(GUIAS)) if estado == PASS else "no cumple"


def rnf34(raiz):
    """Cada ADR de seguridad, consistencia o recuperación declara sus riesgos, con mitigación y prueba."""
    detalle, estado = [], PASS
    matriz = raiz / "verif" / "verification-plan" / "matriz-trazabilidad.md"
    conocidos = set(re.findall(r"TC-\d{3}", _leer(matriz))) if matriz.is_file() else set()
    revisados = 0
    for ruta in _adrs(raiz):
        numero = ruta.name[:4]
        if numero in ADR_SIN_RIESGO:
            continue
        revisados += 1
        consecuencias = _seccion(_leer(ruta), "Consecuencias")
        m = re.search(r"\*\*Riesgos\*\*(.*)", consecuencias, re.S)
        riesgos = [l[2:].strip() for l in (m.group(1).splitlines() if m else []) if l.startswith("- ")]
        if not riesgos:
            estado = FAIL
            detalle.append("FALLA  ADR-%s no declara riesgos en «Consecuencias»" % numero)
            continue
        sin_prueba, sin_mitigacion, sin_ejecutar = [], [], []
        for riesgo in riesgos:
            if "Mitigación" not in riesgo:
                sin_mitigacion.append(riesgo[:60])
            prueba = re.search(r"Prueba:(.*)", riesgo)
            if not prueba:
                sin_prueba.append(riesgo[:60])
                continue
            for tc in re.findall(r"TC-\d{3}", prueba.group(1)):
                if tc not in conocidos:
                    sin_ejecutar.append(tc)
        if sin_mitigacion or sin_prueba or sin_ejecutar:
            estado = FAIL
            if sin_mitigacion:
                detalle.append("FALLA  ADR-%s: riesgos sin mitigación: %s" % (numero, "; ".join(sin_mitigacion)))
            if sin_prueba:
                detalle.append("FALLA  ADR-%s: riesgos sin «Prueba:»: %s" % (numero, "; ".join(sin_prueba)))
            if sin_ejecutar:
                detalle.append("FALLA  ADR-%s cita casos que no están en la matriz: %s"
                               % (numero, ", ".join(sorted(set(sin_ejecutar)))))
        else:
            aceptados = [r for r in riesgos if re.search(r"Prueba:\s*ninguna", r)]
            nota = " (%d con la prueba «ninguna» como riesgo aceptado y documentado)" % len(aceptados) \
                if aceptados else ""
            detalle.append("OK  ADR-%s: %d riesgo(s) con mitigación y prueba%s" % (numero, len(riesgos), nota))
    if not revisados:
        return FAIL, ["FALLA  no hay ADR que revisar"], "sin ADR"
    return estado, detalle, "%d ADR con riesgo, mitigación y prueba" % revisados if estado == PASS else "no cumple"


INSPECCIONES = (
    ("INS-016", "RNF-16 Mínimo privilegio y modelo de amenazas", rnf16),
    ("INS-017", "RNF-17 Código modular", rnf17),
    ("INS-018", "RNF-18 Interfaces y decisiones documentadas", rnf18),
    ("INS-034", "RNF-34 Riesgo y prueba en cada ADR", rnf34),
)


def inspeccionar(raiz):
    """Devuelve [(id, titulo, estado, detalle, resumen)] de las cuatro inspecciones."""
    resultados = []
    for ident, titulo, funcion in INSPECCIONES:
        estado, detalle, resumen = funcion(Path(raiz))
        resultados.append((ident, titulo, estado, detalle, resumen))
    return resultados


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspecciones documentales de RNF-16, RNF-17, RNF-18 y RNF-34.")
    parser.add_argument("--raiz", default=str(Path(__file__).resolve().parents[2]),
                        help="Raíz del repositorio (por defecto, la de este script)")
    parser.add_argument("--tsv", help="Archivo donde guardar ID, estado y resumen de cada inspección")
    args = parser.parse_args(argv)
    resultados = inspeccionar(args.raiz)
    for ident, titulo, estado, detalle, resumen in resultados:
        print("%s  %s: %s" % (ident, titulo, estado))
        for linea in detalle:
            print("    " + linea)
    if args.tsv:
        Path(args.tsv).write_text(
            "".join("%s\t%s\t%s\n" % (i, e, r) for i, _, e, _, r in resultados), encoding="utf-8")
    return 1 if any(e == FAIL for _, _, e, _, _ in resultados) else 0


if __name__ == "__main__":
    sys.exit(main())
