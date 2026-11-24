# Revisión cruzada

Aquí queda el registro de lo que encuentra el **otro equipo** al verificar JobRunner. El proceso completo (cómo se recibe la versión candidata, cómo se responde y cómo se regresa cada defecto) está en la sección 12 del [plan de verificación](../verification-plan/plan-de-verificacion.md).

## Qué hay en esta carpeta

| Archivo | Qué es |
|---|---|
| `PLANTILLA.md` | Plantilla de un defecto. Se copia como `VC-NN.md` (`VC-01.md`, `VC-02.md`...) |
| `VC-NN.md` | Un defecto reportado por el otro equipo, con su análisis, su respuesta y sus regresiones |
| [`../results/<run-id>-remoto/`](../results/) | Evidencia de la operación entre dos equipos. Su lista de comprobación está en [EVIDENCIA-REMOTA.md](EVIDENCIA-REMOTA.md) |

## Flujo de un defecto

1. **Se recibe.** El otro equipo reporta qué hizo, qué esperaba y qué pasó, con el hash de la versión que probó.
2. **Se registra.** Verificación abre la Issue `[Defecto] VC-NN` (plantilla `.github/ISSUE_TEMPLATE/defecto.md`), la asigna al responsable del módulo y crea `VC-NN.md` a partir de la plantilla.
3. **Se analiza.** El responsable decide si es un defecto, una limitación o un uso incorrecto, y por qué.
4. **Se responde.** Una de tres respuestas: *Corregido*, *No es defecto* o *Limitación aceptada* (cada una con lo que debe incluir, en el plan).
5. **Se regresa.** Si se corrigió: PR con una prueba de regresión que falla sin la corrección, `./scripts/test.sh` sin `FAILED` y las pruebas del caso afectado en `PASS`. Todo queda anotado en `VC-NN.md`.
6. **Se cierra.** El defecto pasa a «Cerrado» en la matriz y en la lista de defectos solo con las regresiones en `PASS`, o con su justificación.

## Lista de defectos reportados

| VC | Issue | Módulo | Responsable | Respuesta | Regresión | Estado |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | No se realizó verificación cruzada (ver `docs/defectos-y-limitaciones.md`) |

Verificación (Diego) mantiene esta tabla al día y avisa de los defectos sin respuesta.

## Responsables por módulo

| Módulo | Responsable |
|---|---|
| Red, protocolo y persistencia (`server.py`, `red.py`, `store.py`) | Josué |
| Cola, cancelación, `output`, `health` y cliente (`executor.py`, `cli.py`) | Juan |
| Pruebas, `verify.sh` y `procesos.sh` | Diego |
| Bitácora y documentación | Daniel |
