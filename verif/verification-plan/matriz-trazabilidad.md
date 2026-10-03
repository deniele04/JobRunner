# Matriz de trazabilidad — Avance 1

Relaciona cada criterio del Avance 1 con sus casos de prueba, sus pruebas automatizadas y su último resultado, y cada requisito RF/RNF con los TC que lo cubren. Plan: [plan-de-verificacion.md](plan-de-verificacion.md).

**Última ejecución formal:** `verif/results/20261002-avance1/` (ver [resumen](../results/20261002-avance1/resumen.md))

**Numeración de TC:** alineada con el PDF 05 del Plan de Verificación: TC-005 es cancelar un trabajo y TC-006 es el código de salida.

## Criterios y casos

| Criterio del Avance 1 | TC | Pruebas automatizadas | Estado |
|---|---|---|---|
| Enviar un trabajo y obtener un ID único | [TC-001](../test-cases/TC-001.md) | Extremo a extremo pendiente: requiere el CLI (PR #32). Verificación unitaria complementaria: `test_ids_unicos_en_2000_trabajos` (FAIL, ver DEF-001) | BLOCKED |
| Estados y transiciones del modelo | [TC-003](../test-cases/TC-003.md) | `test_exito_termina_en_succeeded_con_codigo_0`, `test_codigo_de_salida_distinto_de_cero_termina_en_failed`, `test_transiciones_validas`, `test_transiciones_invalidas_lanzan_error` | PASS |
| Consultar estado y listar trabajos | [TC-004](../test-cases/TC-004.md) | Pendiente: requiere el CLI (PR #32) | BLOCKED |
| Cancelar un trabajo | [TC-005](../test-cases/TC-005.md) | `test_cancelar_trabajo_en_ejecucion`, `test_cancelar_trabajo_inexistente`, `test_trabajo_cancelado_no_cambia_de_estado_en_poll` | PASS |
| Ejecutar como proceso separado | [TC-006](../test-cases/TC-006.md) | `test_trabajo_corre_en_proceso_separado` | PASS |
| Obtener el código de salida | [TC-006](../test-cases/TC-006.md) | `test_exito_termina_en_succeeded_con_codigo_0`, `test_codigo_de_salida_distinto_de_cero_termina_en_failed`, `test_stderr_del_trabajo_se_guarda_en_archivo` | PASS |
| Comandos inválidos sin terminar el servicio | [TC-008](../test-cases/TC-008.md) | `test_comando_inexistente_falla_sin_tumbar_el_gestor`, `test_argv_vacio_se_rechaza_y_no_registra_trabajo` | PASS (a nivel de `JobManager`) |
| Construcción reproducible desde un clon limpio | [TC-014](../test-cases/TC-014.md) | `verif/scripts/verify.sh` | PASS |
| Pruebas y script de verificación | — | `./scripts/test.sh`, `verif/scripts/verify.sh` | Evidencia en `verif/results/` |

## Cobertura de requisitos

El Plan de Verificación exige listar RF-01 a RF-24 y RNF-01 a RNF-26 sin huecos. **Esta sección está incompleta:** el repositorio solo contiene los códigos que citan los ADR en su sección «Requisitos afectados». Falta, para cada código, su texto y el TC que lo cubre; ambos datos están en los PDF (requisitos y PDF 05) y deben pasarse a la columna **TC**. «—» en **Citado en** significa que ningún ADR lo menciona.

### Requisitos funcionales

| Código | Citado en | TC |
|---|---|---|
| RF-01 | — | por asignar |
| RF-02 | ADR-0003 | por asignar |
| RF-03 | — | por asignar |
| RF-04 | ADR-0001, ADR-0003 | por asignar |
| RF-05 | — | por asignar |
| RF-06 | — | por asignar |
| RF-07 | ADR-0002 | por asignar |
| RF-08 | ADR-0003 | por asignar |
| RF-09 | ADR-0002, ADR-0003 | por asignar |
| RF-10 | ADR-0001, ADR-0003 | por asignar |
| RF-11 | — | por asignar |
| RF-12 | ADR-0002 | por asignar |
| RF-13 | ADR-0002 | por asignar |
| RF-14 | — | por asignar |
| RF-15 | — | por asignar |
| RF-16 | — | por asignar |
| RF-17 | — | por asignar |
| RF-18 | ADR-0003 | por asignar |
| RF-19 | ADR-0003 | por asignar |
| RF-20 | ADR-0003 | por asignar |
| RF-21 | ADR-0003 | por asignar |
| RF-22 | ADR-0003 | por asignar |
| RF-23 | — | por asignar |
| RF-24 | — | por asignar |

### Requisitos no funcionales

| Código | Citado en | TC |
|---|---|---|
| RNF-01 | ADR-0001 | por asignar |
| RNF-02 | ADR-0001, ADR-0002 | por asignar |
| RNF-03 | ADR-0001 | por asignar |
| RNF-04 | — | por asignar |
| RNF-05 | — | por asignar |
| RNF-06 | ADR-0002 | por asignar |
| RNF-07 | — | por asignar |
| RNF-08 | ADR-0003 | por asignar |
| RNF-09 | — | por asignar |
| RNF-10 | ADR-0002 | por asignar |
| RNF-11 | ADR-0002 | por asignar |
| RNF-12 | ADR-0003 | por asignar |
| RNF-13 | — | por asignar |
| RNF-14 | ADR-0003 | por asignar |
| RNF-15 | — | por asignar |
| RNF-16 | — | por asignar |
| RNF-17 | ADR-0001 | por asignar |
| RNF-18 | — | por asignar |
| RNF-19 | ADR-0001 | por asignar |
| RNF-20 | — | por asignar |
| RNF-21 | — | por asignar |
| RNF-22 | — | por asignar |
| RNF-23 | — | por asignar |
| RNF-24 | ADR-0003 | por asignar |
| RNF-25 | — | por asignar |
| RNF-26 | — | por asignar |

### Códigos citados en los ADR que están fuera del rango

Los siguientes códigos no existen entre RF-01 a RF-24 ni RNF-01 a RNF-26. Hay que revisar si el ADR tiene un error de código o si el rango del plan es mayor.

| Código | Citado en |
|---|---|
| RNF-28 | ADR-0002 |
| RNF-31 | ADR-0002 |
| RNF-32 | ADR-0003 |

## Defectos

| ID | Descripción | TC afectado | Estado |
|---|---|---|---|
| DEF-001 | **IDs de trabajo con colisiones.** `Job.new()` (`src/jobrunner/jobs.py`) genera el ID con `uuid.uuid4().hex[:4]`: solo 65 536 valores posibles. Al crear 2000 trabajos la prueba encuentra decenas de IDs repetidos (28 IDs repetidos en la ejecución formal `20261002-avance1`; entre 18 y 39 en cinco corridas locales). Además, `JobManager.submit()` guarda el trabajo en `self._jobs[job.id]`, por lo que un ID repetido sobrescribe en silencio al trabajo anterior. | TC-001 | Abierto. Lo corrige el PR #34 |
| DEF-002 | **Archivos de salida sin cerrar.** `JobManager.submit()` abre los archivos de salida y de errores con `open()` y nunca los cierra en el proceso padre. Python lo reporta como `ResourceWarning` en `unittest.log`. Con muchos trabajos puede agotar descriptores de archivo. | TC-006 | Abierto. Lo corrige el PR #34 |

Al integrarse el PR #34: volver a correr `verif/scripts/verify.sh`, comprobar que `test_ids_unicos_en_2000_trabajos` pasa y que `unittest.log` ya no contiene `ResourceWarning`, y entonces pasar DEF-001 y DEF-002 a **Cerrado**.

## Pendiente de integración

| PR | Contenido | Efecto en la verificación |
|---|---|---|
| #32 | Servidor y CLI | TC-001 y TC-004 pasan de BLOCKED a ejecutables. `verify.sh` todavía no automatiza la prueba extremo a extremo: hay que agregarla antes de que esos casos puedan pasar a PASS con evidencia. |
| #34 | Corrección de DEF-001 y DEF-002 | Ver sección Defectos. |

## TC citados en los ADR y fuera del Avance 1

| TC | Origen | Tema | Hito |
|---|---|---|---|
| TC-002 | ADR-0001 | Paralelismo con procesos separados (GIL) | 2 |
| TC-007, TC-022 | ADR-0002 | Escrituras concurrentes en SQLite | 2 |
| TC-023 | ADR-0003 | Contrato de mensajes JSON | 3 |
