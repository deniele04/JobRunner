#!/usr/bin/env python3
"""Revisa que una carpeta de evidencia entre dos equipos esté completa.

Uso: python3 verif/scripts/revisar_evidencia_remota.py <run-id>
     (revisa verif/results/<run-id>-remoto/)

Comprueba que existan los archivos que pide la sección 6 del plan de verificación,
que ninguno esté vacío, que la bitácora tenga el rechazo de un origen no permitido y
que no aparezca una IP pública (RNF-26). No juzga lo demás: solo avisa de lo que falta. Termina con 0 si está completa y 1 si no.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# Cada requisito acepta varios nombres de archivo (el de la ejecución real del equipo de Josué y
# el de la guía). (patrones, qué es)
REQUERIDOS = [
    (("jobrunner.log", "*bitacora*"), "Bitácora del servicio durante la prueba"),
    (("prueba-vpn-servidor*", "equipo-servidor*"), "Grabación o salida del equipo que corre el servicio"),
    (("prueba-vpn-cliente*", "equipo-cliente*"), "Salida de los comandos del equipo cliente (submit, status, list, output, cancel)"),
    (("health*",), "Salida de `health` consultada desde el equipo cliente"),
    (("configuracion*", "red*"), "Opciones con las que se inició el servicio y red usada (LAN privada o VPN)"),
    (("resumen.md", "LEEME*"), "Quién hizo la prueba, cuándo, con qué commit y qué pasó"),
]
# El rechazo de un origen no permitido debe verse en la bitácora.
EVENTO_RECHAZO = "acceso_rechazado"
PRIVADAS = re.compile(r"(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d+\.\d+|127\.\d+\.\d+\.\d+)")
# Una IP es un grupo de cuatro números que no forma parte de otro texto (por ejemplo «6.6.87.2-microsoft»).
IP = re.compile(r"(?<![\w.-])\d{1,3}(\.\d{1,3}){3}(?![\w-]|\.\d)")


def revisar(carpeta):
    problemas = []
    if not carpeta.is_dir():
        return [f"No existe la carpeta {carpeta}"]
    for patrones, descripcion in REQUERIDOS:
        hallados = sorted({f for pat in patrones for f in carpeta.glob(pat) if f.is_file()})
        if not hallados:
            problemas.append(f"Falta {' o '.join(patrones)}: {descripcion}")
            continue
        for f in hallados:
            if f.stat().st_size == 0:
                problemas.append(f"{f.name} está vacío")
    registros = [f for pat in REQUERIDOS[0][0] for f in carpeta.glob(pat) if f.is_file()]
    if registros and not any(EVENTO_RECHAZO in f.read_text(encoding="utf-8", errors="replace") for f in registros):
        problemas.append(f"La bitácora no tiene ningún «{EVENTO_RECHAZO}»: falta la prueba de un origen no permitido")
    # La red debe ser privada: avisa si en la evidencia aparece una IP pública.
    for f in carpeta.glob("*"):
        if not f.is_file():
            continue
        try:
            texto = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in IP.finditer(texto):
            ip = m.group(0)
            if all(int(p) <= 255 for p in ip.split(".")) and not PRIVADAS.fullmatch(ip) and ip != "0.0.0.0":
                problemas.append(f"{f.name} menciona {ip}, que no es una red privada ni VPN (RNF-26)")
                break
    return problemas


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    carpeta = RAIZ / "verif" / "results" / f"{argv[1]}-remoto"
    problemas = revisar(carpeta)
    if problemas:
        print(f"Evidencia remota INCOMPLETA en {carpeta.relative_to(RAIZ)}:")
        for p in problemas:
            print(f"  - {p}")
        return 1
    print(f"Evidencia remota completa en {carpeta.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
