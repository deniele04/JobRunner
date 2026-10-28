#!/usr/bin/env bash
# Identifica procesos zombis y huérfanos que JobRunner pudo dejar atrás.
#
# Uso:
#   verif/scripts/procesos.sh guardar ARCHIVO
#       Guarda los PID que existen ahora (línea base). Hazlo ANTES de la prueba.
#   verif/scripts/procesos.sh revisar [--base ARCHIVO] [--patron REGEX] [--servidor REGEX]
#       Busca, DESPUÉS de la prueba:
#         ZOMBI     proceso en estado Z cuyo padre es el servidor
#                   (--servidor, por defecto 'jobrunner\.server'): el servidor
#                   no recogió a un hijo que ya terminó.
#         HUERFANO  proceso líder de sesión (los trabajos se lanzan con
#                   start_new_session) cuyo padre es PID 1, es decir, su padre
#                   murió. Sin --base solo se considera si coincide con --patron.
#       --base      ignora los PID del archivo guardado (lo que ya existía).
#       --patron    solo cuenta huérfanos cuya línea de comando coincide con la
#                   expresión regular (p. ej. 'sleep 300').
#       Se exige --base o --patron para huérfanos: sin ellos todos los
#       servicios del sistema (también líderes de sesión con padre 1) serían
#       falsos positivos.
#
# Código de salida: 0 = limpio, 1 = hay zombis u huérfanos, 2 = uso incorrecto.
# Solo lectura: no mata ni modifica ningún proceso. Requiere ps y awk (Linux).
set -uo pipefail

uso() { awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"; }

cmd="${1:-}"
case "$cmd" in
  guardar)
    [ $# -eq 2 ] || { uso >&2; exit 2; }
    ps -eo pid= | awk '{print $1}' > "$2" || exit 2
    echo "Línea base guardada en $2 ($(wc -l < "$2") procesos)"
    exit 0
    ;;
  revisar) shift ;;
  -h|--help) uso; exit 0 ;;
  *) uso >&2; exit 2 ;;
esac

base=""; patron=""; servidor='jobrunner\.server'
while [ $# -gt 0 ]; do
  case "$1" in
    --base)     [ $# -ge 2 ] || { uso >&2; exit 2; }; base="$2"; shift 2 ;;
    --patron)   [ $# -ge 2 ] || { uso >&2; exit 2; }; patron="$2"; shift 2 ;;
    --servidor) [ $# -ge 2 ] || { uso >&2; exit 2; }; servidor="$2"; shift 2 ;;
    *) uso >&2; exit 2 ;;
  esac
done

if [ -z "$base" ] && [ -z "$patron" ]; then
  echo "Error: indica --base ARCHIVO (guardado con 'guardar') o --patron REGEX para identificar huérfanos." >&2
  exit 2
fi
if [ -n "$base" ] && [ ! -r "$base" ]; then
  echo "Error: no se puede leer la línea base $base" >&2
  exit 2
fi

# pid ppid sid stat args  (una línea por proceso)
instantanea="$(ps -eo pid=,ppid=,sid=,stat=,args= 2>/dev/null)" || { echo "Error: ps falló" >&2; exit 2; }

hallazgos="$(
  printf '%s\n' "$instantanea" | awk -v servidor="$servidor" -v patron="$patron" -v base="$base" -v yo="$$" '
    function args_de(linea,   n, i, campos, salida) {
      n = split(linea, campos, " ")
      salida = ""
      for (i = 5; i <= n; i++) salida = salida (i > 5 ? " " : "") campos[i]
      return salida
    }
    BEGIN {
      if (base != "") while ((getline p < base) > 0) existia[p] = 1
    }
    { pid[NR] = $1; ppid[NR] = $2; sid[NR] = $3; stat[NR] = $4; linea[NR] = $0; arg[$1] = args_de($0); filas = NR }
    END {
      for (i = 1; i <= filas; i++) {
        if (pid[i] == yo || existia[pid[i]]) continue
        a = args_de(linea[i])
        # Zombi: estado Z y el padre es el servidor.
        if (stat[i] ~ /^Z/ && (ppid[i] in arg) && arg[ppid[i]] ~ servidor)
          printf "ZOMBI\t%s\tpadre=%s\t%s\n", pid[i], ppid[i], a
        # Huérfano: líder de sesión adoptado por PID 1.
        else if (ppid[i] == 1 && sid[i] == pid[i] && stat[i] !~ /^Z/ && (patron == "" || a ~ patron))
          printf "HUERFANO\t%s\tsid=%s\t%s\n", pid[i], sid[i], a
      }
    }'
)"

if [ -z "$hallazgos" ]; then
  echo "Sin zombis ni huérfanos."
  exit 0
fi

echo "TIPO	PID	DETALLE	COMANDO"
echo "$hallazgos"
zombis=$(printf '%s\n' "$hallazgos" | grep -c '^ZOMBI' || true)
huerfanos=$(printf '%s\n' "$hallazgos" | grep -c '^HUERFANO' || true)
echo "Resumen: $zombis zombi(s), $huerfanos huérfano(s)."
exit 1
