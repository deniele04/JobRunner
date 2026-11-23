#!/usr/bin/env python3
"""Revisa que una carpeta de evidencia entre dos equipos esté completa.

Uso: python3 verif/scripts/revisar_evidencia_remota.py <run-id>
     (revisa verif/results/<run-id>-remoto/)

Comprueba que existan los archivos que pide la sección 6 del plan de verificación
y que ninguno esté vacío. No juzga el contenido: solo avisa de lo que falta para
que se junte antes de la ejecución formal. Termina con 0 si está completa y 1 si no.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# (patrón del nombre, qué es)
REQUERIDOS = [
    ("equipo-servidor-bitacora*", "Bitácora del equipo que corre el servicio"),
    ("equipo-cliente-comandos*", "Salida de los comandos del equipo cliente (submit, status, list, output, cancel)"),
    ("health*", "Salida de `health` consultada desde el equipo cliente"),
    ("rechazo*", "Prueba de que un origen no permitido es rechazado (acceso_rechazado)"),
    ("red*", "Dirección y tipo de red usada (LAN privada o VPN), sin datos personales"),
    ("LEEME*", "Quién hizo la prueba, cuándo, con qué hash y qué pasó"),
]
PRIVADAS = re.compile(r"\b(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d+\.\d+|127\.\d+\.\d+\.\d+)\b")
IP = re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b")


def revisar(carpeta):
    problemas = []
    if not carpeta.is_dir():
        return [f"No existe la carpeta {carpeta}"]
    for patron, descripcion in REQUERIDOS:
        hallados = sorted(carpeta.glob(patron))
        if not hallados:
            problemas.append(f"Falta {patron}: {descripcion}")
            continue
        for f in hallados:
            if f.is_file() and f.stat().st_size == 0:
                problemas.append(f"{f.name} está vacío")
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
