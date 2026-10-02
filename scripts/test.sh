#!/usr/bin/env bash
# Ejecuta las pruebas unitarias y el script de verificación.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src

python3 -m compileall -q src

if [ -d verif/unit ]; then
  python3 -m unittest discover -s verif/unit -v
else
  echo "Aviso: todavía no hay pruebas unitarias en verif/unit/."
fi

if [ -x verif/scripts/verify.sh ]; then
  verif/scripts/verify.sh
else
  echo "Aviso: todavía no existe verif/scripts/verify.sh."
fi
