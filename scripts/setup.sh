#!/usr/bin/env bash
# Prepara el proyecto: verifica Python y compila el código para detectar errores de sintaxis.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || { echo "Error: se requiere Python 3.10 o superior." >&2; exit 1; }

python3 -m compileall -q src
chmod +x scripts/*.sh
echo "Construcción OK: Python $(python3 --version | cut -d' ' -f2), sin dependencias externas."
