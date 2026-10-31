#!/usr/bin/env bash
# Script de verificación (Avances 1 y 2).
#
# Ejecuta las pruebas unitarias y de integración (servidor y CLI reales) y la
# verificación desde un clon limpio (TC-014),
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

# Línea base de procesos para comprobar al final que las pruebas no dejaron
# zombis ni huérfanos (verif/scripts/procesos.sh).
BASE_PROCESOS="$(mktemp)"
verif/scripts/procesos.sh guardar "$BASE_PROCESOS" > /dev/null

# 1. Pruebas unitarias y de integración: una línea por prueba en unit-resultados.tsv.
python3 verif/scripts/ejecutar_pruebas.py "$OUT/unit-resultados.tsv" > "$OUT/unittest.log" 2>&1
unit_rc=$?

# Estado de un TC a partir de los nombres de sus pruebas unitarias:
# FAIL si alguna falla, BLOCKED si alguna no se encontró, PASS si todas pasan.
estado_pruebas() {
  local nombre r resultado="PASS"
  # Sin pruebas todavía: el caso no se puede ejecutar.
  [ $# -eq 0 ] && { echo "BLOCKED"; return; }
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
  test_trabajo_cancelado_no_cambia_de_estado_en_poll \
  test_cancelar_en_cola_pasa_a_canceled_y_nunca_arranca)"
tc008="$(estado_pruebas \
  test_comando_inexistente_falla_sin_tumbar_el_gestor \
  test_argv_vacio_se_rechaza_y_no_registra_trabajo \
  test_solicitud_mal_formada_no_tumba_al_servicio \
  test_bytes_que_no_son_texto_valido \
  test_cliente_que_se_desconecta_antes_de_la_respuesta)"
ids="$(estado_pruebas test_ids_unicos_en_2000_trabajos)"

# TC-001 y TC-004 son de extremo a extremo: servidor y CLI reales (verif/integration).
tc001="$(estado_pruebas \
  test_submit_devuelve_un_id \
  test_submit_exitoso_termina_con_codigo_0 \
  test_dos_submit_devuelven_ids_distintos \
  test_status_reconoce_el_id_devuelto \
  test_submit_sin_comando_se_rechaza \
  test_solicitud_mal_formada_no_tumba_al_servicio \
  test_la_ayuda_lleva_el_nombre_royito \
  test_royito_envia_y_consulta_desde_cualquier_carpeta \
  test_respeta_la_variable_jobrunner_socket \
  test_funciona_a_traves_de_un_enlace_simbolico)"
tc004="$(estado_pruebas \
  test_status_inmediato_es_running \
  test_list_incluye_el_trabajo_con_su_estado \
  test_al_terminar_status_es_succeeded_con_codigo_0 \
  test_trabajo_con_error_termina_failed_con_su_codigo \
  test_list_filtra_por_estado \
  test_status_de_id_inexistente_da_error_y_codigo_distinto_de_cero \
  test_status_y_list_exitosos_terminan_con_codigo_0 \
  test_consulta_responde_en_menos_de_1_segundo_con_100_trabajos)"

# Casos del Avance 2. Para añadir una prueba a un caso basta agregar su nombre aquí.
tc002="$(estado_pruebas \
  test_respeta_max_jobs_y_encola_el_resto \
  test_trabajo_en_cola_no_tiene_started_at \
  test_tres_simultaneos_con_los_valores_por_defecto)"
tc007="$(estado_pruebas \
  test_reinicio_conserva_historial_y_recupera_interrumpidos \
  test_reinicio_conserva_el_historial_de_trabajos_terminados \
  test_recuperacion_marca_running_como_failed_y_termina_su_proceso \
  test_recuperar_dos_veces_da_el_mismo_resultado \
  test_recuperacion_reanuda_los_trabajos_en_cola \
  test_los_datos_sobreviven_a_cerrar_y_reabrir)"
tc009="$(estado_pruebas \
  test_ctrl_c_cancela_los_trabajos_en_ejecucion_sin_huerfanos \
  test_sigterm_tambien_cierra_de_forma_controlada \
  test_el_trabajo_cancelado_queda_canceled_tras_reiniciar \
  test_se_elimina_el_socket \
  test_se_conserva_la_cola_para_el_siguiente_arranque \
  test_no_arranca_trabajos_de_la_cola_durante_el_cierre \
  test_trabajo_que_ignora_sigterm_se_mata_a_los_5_segundos \
  test_no_acepta_solicitudes_mientras_cierra \
  test_segundo_ctrl_c_fuerza_el_cierre_inmediato \
  test_cierre_ordenado_no_deja_huerfanos \
  test_cierra_los_running_sin_dejar_procesos \
  test_los_queued_se_conservan_y_no_arrancan \
  test_la_cola_conservada_se_reanuda_en_el_siguiente_arranque \
  test_no_acepta_trabajos_nuevos_durante_el_cierre \
  test_el_estado_final_de_un_trabajo_ya_terminado_no_se_reescribe \
  test_escala_a_sigkill_si_el_trabajo_ignora_sigterm \
  test_forzar_envia_sigkill_de_inmediato \
  test_el_resultado_del_cierre_queda_guardado)"
tc016="$(estado_pruebas \
  test_cola_llena_rechaza_y_no_registra_el_trabajo \
  test_el_rechazo_no_afecta_a_los_trabajos_aceptados \
  test_submit_con_cola_llena_responde_error_y_no_crea_trabajo)"
tc017="$(estado_pruebas \
  test_la_segunda_cancelacion_devuelve_el_estado_sin_cambiar_nada \
  test_la_segunda_cancelacion_no_falla_aunque_el_proceso_ya_murio \
  test_dos_cancelaciones_seguidas_dejan_un_solo_estado_final \
  test_cancelar_un_trabajo_ya_cancelado_devuelve_su_estado_sin_cambiarlo \
  test_cancelar_un_trabajo_que_termino_solo_sigue_dando_error \
  test_cancelar_un_id_inexistente_no_afecta_a_los_demas)"
tc018="$(estado_pruebas \
  test_servidor_request_id_repetido_devuelve_el_mismo_trabajo \
  test_reenvio_tras_desconexion_del_cliente \
  test_servidor_request_id_repetido_despues_de_reiniciar \
  test_request_id_invalido_se_rechaza \
  test_request_id_repetido_devuelve_el_mismo_trabajo \
  test_request_id_repetido_despues_de_reiniciar \
  test_request_id_invalido_es_rechazado \
  test_sin_request_id_cada_envio_es_un_trabajo_nuevo \
  test_request_id_repetido_es_rechazado_y_no_cambia_nada \
  test_trabajos_sin_request_id_no_chocan)"
tc019="$(estado_pruebas \
  test_cierra_la_conexion_sin_enviar_nada \
  test_cierra_sin_leer_la_respuesta_y_la_solicitud_se_aplica_una_vez \
  test_cierra_a_mitad_de_una_solicitud \
  test_rafaga_de_desconexiones_no_agota_los_descriptores_del_servidor)"
tc020="$(estado_pruebas \
  test_kill_9_al_trabajo_lo_deja_failed_con_diagnostico \
  test_kill_15_externo_lo_deja_failed_con_sigterm \
  test_los_demas_trabajos_siguen_en_ejecucion \
  test_el_lugar_liberado_lo_ocupa_el_siguiente_de_la_cola \
  test_trabajo_que_termina_sin_que_nadie_lo_consulte_no_queda_zombi)"
tc024="$(estado_pruebas \
  test_oleadas_de_trabajos_cortos_no_dejan_procesos_ni_fugas \
  test_saturacion_y_cancelacion_masiva_no_dejan_procesos)"
tc021="$(estado_pruebas \
  test_trabajo_que_ignora_sigterm_termina_con_sigkill \
  test_el_escalamiento_no_bloquea_a_los_demas_trabajos)"
tc022="$(estado_pruebas \
  test_escritura_no_confirmada_no_deja_rastro \
  test_escritura_confirmada_sobrevive_a_la_muerte_del_proceso)"
tc025="$(estado_pruebas \
  test_cada_evento_tiene_fecha_nivel_tipo_e_id \
  test_eventos_de_un_trabajo_se_correlacionan_por_su_id \
  test_cancelar_registra_el_evento_con_su_codigo \
  test_comando_inexistente_registra_un_error \
  test_no_registra_los_argumentos_del_trabajo)"

# 4. Las pruebas no deben dejar zombis ni huérfanos (RNF-30, RNF-33).
sleep 1
verif/scripts/procesos.sh revisar --base "$BASE_PROCESOS" --patron 'sleep|jobrunner' > "$OUT/procesos.log" 2>&1
procesos_rc=$?
rm -f "$BASE_PROCESOS"
if [ "$procesos_rc" -eq 0 ]; then limpieza="PASS"; else limpieza="FAIL"; fi
conocidos="$(awk -F'\t' '$1 == "XFAIL" { n++ } END { print n + 0 }' "$OUT/unit-resultados.tsv")"

{
  echo "# Resumen de la ejecución $RUN_ID"
  echo
  echo "| TC | Estado | Evidencia |"
  echo "|---|---|---|"
  echo "| TC-001 | $tc001 | unittest.log, unit-resultados.tsv. Unicidad de 2000 IDs (unitaria): $ids |"
  echo "| TC-002 | $tc002 | unittest.log, unit-resultados.tsv |"
  echo "| TC-003 | $tc003 | unittest.log, unit-resultados.tsv |"
  echo "| TC-004 | $tc004 | unittest.log, unit-resultados.tsv |"
  echo "| TC-005 | $tc005 | unittest.log, unit-resultados.tsv |"
  echo "| TC-006 | $tc006 | unittest.log, unit-resultados.tsv |"
  echo "| TC-007 | $tc007 | unittest.log, unit-resultados.tsv |"
  echo "| TC-008 | $tc008 | unittest.log, unit-resultados.tsv |"
  echo "| TC-009 | $tc009 | unittest.log, unit-resultados.tsv, procesos.log |"
  echo "| TC-014 | $tc014 | tc-014-clon-limpio.log |"
  echo "| TC-016 | $tc016 | unittest.log, unit-resultados.tsv |"
  echo "| TC-017 | $tc017 | unittest.log, unit-resultados.tsv |"
  echo "| TC-018 | $tc018 | unittest.log, unit-resultados.tsv |"
  echo "| TC-019 | $tc019 | unittest.log, unit-resultados.tsv |"
  echo "| TC-020 | $tc020 | unittest.log, unit-resultados.tsv |"
  echo "| TC-021 | $tc021 | unittest.log, unit-resultados.tsv |"
  echo "| TC-022 | $tc022 | unittest.log, unit-resultados.tsv |"
  echo "| TC-024 | $tc024 | unittest.log, unit-resultados.tsv |"
  echo "| TC-025 | $tc025 | unittest.log, unit-resultados.tsv |"
  echo "| Sin zombis ni huérfanos tras las pruebas | $limpieza | procesos.log |"
  echo
  echo "Fallos esperados y conocidos (expectedFailure): $conocidos. Ver las pruebas con estado XFAIL en unit-resultados.tsv y la matriz de trazabilidad."
} > "$OUT/resumen.md"
cat "$OUT/resumen.md"

# La evidencia no debe llevar la ruta personal de quien ejecuta: se sustituye la
# ruta del repositorio por <repo> en los registros (no cambia ningún resultado).
sed -i "s|$ROOT|<repo>|g" "$OUT"/*.log "$OUT"/*.tsv "$OUT"/*.md 2>/dev/null

status=0
[ "$unit_rc" -ne 0 ] && status=1
[ "$tc014" = "FAIL" ] && status=1
[ "$limpieza" = "FAIL" ] && status=1
exit "$status"
