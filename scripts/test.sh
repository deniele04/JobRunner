#!/usr/bin/env bash
# Ejecuta las pruebas unitarias y el script de verificación.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src

python3 -m compileall -q src

# Se ejecutan ambos pasos aunque el primero falle, para que verify.sh deje
# siempre su evidencia en verif/results/. El código de salida es 1 si falla alguno.
estado=0

if [ -d verif/unit ]; then
  python3 -m unittest discover -s verif/unit -v || estado=1
else
  echo "Aviso: todavía no hay pruebas unitarias en verif/unit/."
fi

if [ -x verif/scripts/verify.sh ]; then
  verif/scripts/verify.sh || estado=1
else
  echo "Aviso: todavía no existe verif/scripts/verify.sh."
fi

exit "$estado"
