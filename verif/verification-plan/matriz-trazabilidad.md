# Matriz de trazabilidad — Avance 1

Relaciona cada criterio del Avance 1 con sus casos de prueba, sus pruebas automatizadas y su último resultado. Plan: [plan-de-verificacion.md](plan-de-verificacion.md).

**Última ejecución formal:** `verif/results/20261002-avance1/` (ver [resumen](../results/20261002-avance1/resumen.md))

> La columna **RF/RNF** está por asignar: el repositorio no contiene el texto de los requisitos, solo sus códigos en los ADR.

## Criterios y casos

| Criterio del Avance 1 | RF/RNF | TC | Pruebas automatizadas | Estado |
|---|---|---|---|---|
| Enviar un trabajo y obtener un ID único | por asignar | [TC-001](../test-cases/TC-001.md) | Extremo a extremo pendiente (requiere CLI). Verificación unitaria complementaria: `test_ids_unicos_en_2000_trabajos` (FAIL, ver DEF-001) | BLOCKED |
| Ejecutar como proceso separado | por asignar | [TC-005](../test-cases/TC-005.md) | `test_trabajo_corre_en_proceso_separado` | PASS |
| Obtener el código de salida | por asignar | [TC-005](../test-cases/TC-005.md) | `test_exito_termina_en_succeeded_con_codigo_0`, `test_codigo_de_salida_distinto_de_cero_termina_en_failed`, `test_stderr_del_trabajo_se_guarda_en_archivo` | PASS |
| Estados y transiciones del modelo | por asignar | [TC-003](../test-cases/TC-003.md) | `test_exito_termina_en_succeeded_con_codigo_0`, `test_codigo_de_salida_distinto_de_cero_termina_en_failed`, `test_transiciones_validas`, `test_transiciones_invalidas_lanzan_error` | PASS |
| Cancelar un trabajo | por asignar | [TC-006](../test-cases/TC-006.md) | `test_cancelar_trabajo_en_ejecucion`, `test_cancelar_trabajo_inexistente`, `test_trabajo_cancelado_no_cambia_de_estado_en_poll` | PASS |
| Consultar estado y listar trabajos | por asignar | [TC-004](../test-cases/TC-004.md) | Pendiente (requiere CLI) | BLOCKED |
| Comandos inválidos sin terminar el servicio | por asignar | [TC-008](../test-cases/TC-008.md) | `test_comando_inexistente_falla_sin_tumbar_el_gestor`, `test_argv_vacio_se_rechaza_y_no_registra_trabajo` | PASS (a nivel de `JobManager`) |
| Construcción reproducible desde un clon limpio | por asignar | [TC-014](../test-cases/TC-014.md) | `verif/scripts/verify.sh` | PASS |
| Pruebas y script de verificación | por asignar | — | `./scripts/test.sh`, `verif/scripts/verify.sh` | Evidencia en `verif/results/` |

## Defectos abiertos

| ID | Descripción | TC afectado | Estado |
|---|---|---|---|
| DEF-001 | **IDs de trabajo con colisiones.** `Job.new()` (`src/jobrunner/jobs.py`) genera el ID con `uuid.uuid4().hex[:4]`: solo 65 536 valores posibles. Al crear 2000 trabajos la prueba encuentra decenas de IDs repetidos (33 en la ejecución formal `20261002-avance1`; entre 18 y 39 en cinco corridas locales). Además, `JobManager.submit()` guarda el trabajo en `self._jobs[job.id]`, por lo que un ID repetido sobrescribe en silencio al trabajo anterior. La rama `fix/bugs-ejecutor` ya usa el UUID completo; está pendiente de integrar a `main`. | TC-001 | Abierto |
| DEF-002 | **Archivos de salida sin cerrar.** `JobManager.submit()` abre los archivos de salida y de errores con `open()` y nunca los cierra en el proceso padre. Python lo reporta como `ResourceWarning` en `unittest.log`. Con muchos trabajos puede agotar descriptores de archivo. La rama `fix/bugs-ejecutor` ya los abre con `with`; pendiente de integrar a `main`. | TC-005 | Abierto |

Cuando se integre la corrección de DEF-001, `test_ids_unicos_en_2000_trabajos` debe pasar y TC-001 podrá avanzar en cuanto el CLI esté disponible.

## TC citados en los ADR y fuera del Avance 1

| TC | Origen | Tema | Hito |
|---|---|---|---|
| TC-002 | ADR-0001 | Paralelismo con procesos separados (GIL) | 2 |
| TC-007, TC-022 | ADR-0002 | Escrituras concurrentes en SQLite | 2 |
| TC-023 | ADR-0003 | Contrato de mensajes JSON | 3 |
