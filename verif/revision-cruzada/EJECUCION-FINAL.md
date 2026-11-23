# Ejecución formal final

Pasos de Verificación sobre el commit final integrado (versión `v1.0.0`). Se hace en WSL/Linux, nunca en Windows nativo.

## Antes

1. Todas las ramas de la entrega están integradas en `main` y no hay defectos de la verificación cruzada sin respuesta (`verif/revision-cruzada/README.md`).
2. `git pull origin main` y `./scripts/test.sh` sin `FAILED`.
3. `verif/scripts/candidata.sh` imprime «LISTA para entregar».
4. Existe `verif/results/<run-id>-remoto/` y `python3 verif/scripts/revisar_evidencia_remota.py <run-id>` la da por completa.
5. Quien evalúa TC-015 llenó `verif/manual/TC-015.md` (estado PASS o FAIL).

## Ejecución

```bash
verif/scripts/verify.sh <run-id>                  # run-id con la fecha, por ejemplo 20261201-v1.0.0
python3 verif/scripts/actualizar_matriz.py <run-id>
git diff verif/verification-plan/matriz-trazabilidad.md
```

## Después

1. Revisar que la matriz no tenga `Pendiente` ni `Sin TC`, y que cada `BLOCKED` o `FAIL` tenga su motivo o su defecto.
2. Subir en un PR `verif/results/<run-id>/` y la matriz actualizada, con `Closes #N` y las 3 aprobaciones.
3. **Pasar a Daniel** el hash del commit verificado y el `<run-id>` para las release notes y el AI-LOG.
4. Si después de esta ejecución cambia cualquier archivo de `src/` o de las pruebas, la ejecución se repite sobre el commit nuevo.
