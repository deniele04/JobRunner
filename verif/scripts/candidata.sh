#!/usr/bin/env bash
# Prepara la versión candidata que se entrega al otro equipo (D5).
#
# Uso: verif/scripts/candidata.sh
#
# Comprueba que el árbol esté limpio, que el README y la guía existan, que
# `./scripts/test.sh` termine sin FAILED, y al final imprime el hash del commit
# que se debe pasar al otro equipo. No cambia nada del repositorio.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2

fallos=0
ok()   { echo "  OK    $1"; }
mal()  { echo "  FALLA $1"; fallos=$((fallos + 1)); }

echo "== Versión candidata =="

if [ -z "$(git status --porcelain)" ]; then ok "árbol de trabajo limpio"; else mal "hay cambios sin commit"; fi

for f in README.md scripts/setup.sh scripts/test.sh; do
  if [ -s "$f" ]; then ok "$f existe"; else mal "falta $f"; fi
done

guia="$(ls docs/user-guide/guia-de-usuario.md 2>/dev/null | head -1)"
if [ -n "$guia" ]; then ok "guía de usuario: $guia"; else mal "falta docs/user-guide/guia-de-usuario.md"; fi

echo "== Pruebas =="
if salida="$(./scripts/test.sh 2>&1)"; then
  if echo "$salida" | grep -q "FAILED"; then mal "test.sh imprime FAILED"; else ok "test.sh sin FAILED"; fi
else
  echo "$salida" | tail -15
  mal "test.sh terminó con error"
fi

echo
echo "Commit candidato: $(git rev-parse HEAD)"
echo "Rama:             $(git rev-parse --abbrev-ref HEAD)"
if [ "$fallos" -eq 0 ]; then
  echo "Resultado: LISTA para entregar. Pasa el hash, el README y la guía al otro equipo."
  exit 0
fi
echo "Resultado: NO está lista ($fallos problema(s))."
exit 1
