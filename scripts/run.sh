#!/usr/bin/env bash
# Inicia el servicio JobRunner. Detener con Ctrl+C.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
exec python3 -m jobrunner.server "$@"
