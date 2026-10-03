#!/usr/bin/env bash
# Script de verificación del Avance 1.
#
# Ejecuta las pruebas unitarias y la verificación desde un clon limpio (TC-014),
# calcula el estado de cada caso de prueba y guarda la evidencia en
# verif/results/<run-id>/.
#
# Uso: verif/scripts/verify.sh [run-id]
#   Sin run-id se usa la fecha y hora (AAAAMMDD-HHMMSS).
#   El clon limpio se hace desde el último commit: confirma tus cambios antes
#   de una ejecución formal.
# Termina con código 1 si alguna prueba o TC falla; los TC BLOCKED no cuentan.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH=src

RUN_ID="${1:-$(date +%Y%m%d-%H%M%S)}"
OUT="verif/results/$RUN_ID"
mkdir -p "$OUT"

{
  echo "run-id: $RUN_ID"
  echo "fecha: $(date -Is)"
  echo "commit: $(git rev-parse HEAD 2>/dev/null || echo 'sin repositorio git')"
  echo "python: $(python3 --version 2>&1)"
  echo "sistema: $(uname -sr)"
} > "$OUT/entorno.txt"

# 1. Pruebas unitarias: una línea por prueba en unit-resultados.tsv.
python3 verif/scripts/ejecutar_pruebas.py "$OUT/unit-resultados.tsv" > "$OUT/unittest.log" 2>&1
unit_rc=$?

# Estado de un TC a partir de los nombres de sus pruebas unitarias:
# FAIL si alguna falla, BLOCKED si alguna no se encontró, PASS si todas pasan.
estado_pruebas() {
  local nombre r resultado="PASS"
  for nombre in "$@"; do
    r="$(awk -F'\t' -v n="$nombre" '$2 ~ ("\\." n "$") { print $1; exit }' "$OUT/unit-resultados.tsv" 2>/dev/null)"
    case "$r" in
      PASS) ;;
      FAIL) resultado="FAIL" ;;
      *) [ "$resultado" = "PASS" ] && resultado="BLOCKED" ;;
    esac
  done
  echo "$resultado"
}

# 2. TC-014: construcción desde un clon limpio, siguiendo el README.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
{
  echo '$ git clone <repositorio> JobRunner'
  git clone -q "$ROOT" "$TMP/JobRunner" &&
  echo '$ git log -1 --oneline' &&
  git -C "$TMP/JobRunner" log -1 --oneline &&
  echo '$ ./scripts/setup.sh' &&
  (cd "$TMP/JobRunner" && ./scripts/setup.sh)
} > "$OUT/tc-014-clon-limpio.log" 2>&1
if [ $? -eq 0 ] && grep -q "Construcción OK" "$OUT/tc-014-clon-limpio.log"; then
  tc014="PASS"
else
  tc014="FAIL"
fi

# 3. Estado de cada TC.
tc003="$(estado_pruebas \
  test_exito_termina_en_succeeded_con_codigo_0 \
  test_codigo_de_salida_distinto_de_cero_termina_en_failed \
  test_transiciones_validas \
  test_transiciones_invalidas_lanzan_error)"
tc006="$(estado_pruebas \
  test_trabajo_corre_en_proceso_separado \
  test_exito_termina_en_succeeded_con_codigo_0 \
  test_codigo_de_salida_distinto_de_cero_termina_en_failed \
  test_stderr_del_trabajo_se_guarda_en_archivo)"
tc005="$(estado_pruebas \
  test_cancelar_trabajo_en_ejecucion \
  test_cancelar_trabajo_inexistente \
  test_trabajo_cancelado_no_cambia_de_estado_en_poll)"
tc008="$(estado_pruebas \
  test_comando_inexistente_falla_sin_tumbar_el_gestor \
  test_argv_vacio_se_rechaza_y_no_registra_trabajo)"
ids="$(estado_pruebas test_ids_unicos_en_2000_trabajos)"

# TC-001 y TC-004 son de extremo a extremo y necesitan el CLI.
if [ -f src/jobrunner/cli.py ]; then
  motivo_cli="falta automatizar la prueba extremo a extremo con el CLI"
else
  motivo_cli="no existe src/jobrunner/cli.py"
fi

{
  echo "# Resumen de la ejecución $RUN_ID"
  echo
  echo "| TC | Estado | Evidencia |"
  echo "|---|---|---|"
  echo "| TC-001 | BLOCKED | $motivo_cli. Verificación parcial de ID único: $ids (unittest.log) |"
  echo "| TC-003 | $tc003 | unittest.log, unit-resultados.tsv |"
  echo "| TC-004 | BLOCKED | $motivo_cli |"
  echo "| TC-005 | $tc005 | unittest.log, unit-resultados.tsv |"
  echo "| TC-006 | $tc006 | unittest.log, unit-resultados.tsv |"
  echo "| TC-008 | $tc008 | unittest.log, unit-resultados.tsv |"
  echo "| TC-014 | $tc014 | tc-014-clon-limpio.log |"
} > "$OUT/resumen.md"
cat "$OUT/resumen.md"

status=0
[ "$unit_rc" -ne 0 ] && status=1
[ "$tc014" = "FAIL" ] && status=1
exit "$status"
