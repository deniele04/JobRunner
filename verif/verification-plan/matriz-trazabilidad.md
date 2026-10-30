# Matriz de trazabilidad — Avance 1

Relaciona cada criterio del Avance 1 con sus casos de prueba, sus pruebas automatizadas y su último resultado, y cada requisito RF/RNF con los TC que lo cubren. Plan: [plan-de-verificacion.md](plan-de-verificacion.md).

**Última ejecución formal:** `verif/results/20261028-integracion/` (ver [resumen](../results/20261028-integracion/resumen.md))

**Numeración de TC:** alineada con el PDF 05 del Plan de Verificación: TC-005 es cancelar un trabajo y TC-006 es el código de salida.

## Criterios y casos

| Criterio del Avance 1 | TC | Pruebas automatizadas | Estado |
|---|---|---|---|
| Enviar un trabajo y obtener un ID único | [TC-001](../test-cases/TC-001.md) | `verif/integration/test_tc001_enviar_trabajo.py` (6 pruebas, servidor y CLI reales); unitaria complementaria `test_ids_unicos_en_2000_trabajos` | FAIL (DEF-003) |
| Estados y transiciones del modelo | [TC-003](../test-cases/TC-003.md) | `test_exito_termina_en_succeeded_con_codigo_0`, `test_codigo_de_salida_distinto_de_cero_termina_en_failed`, `test_transiciones_validas`, `test_transiciones_invalidas_lanzan_error` | PASS |
| Consultar estado y listar trabajos | [TC-004](../test-cases/TC-004.md) | `verif/integration/test_tc004_consultar_listar.py` (8 pruebas, servidor y CLI reales) | FAIL (DEF-003) |
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
| DEF-001 | **IDs de trabajo con colisiones.** `Job.new()` generaba el ID con `uuid.uuid4().hex[:4]` (65 536 valores). | TC-001 | Cerrado. `Job.new()` usa el UUID completo; `test_ids_unicos_en_2000_trabajos` pasa en `20261028-integracion` |
| DEF-002 | **Archivos de salida sin cerrar** en `JobManager.submit()`. | TC-006 | Cerrado. `submit()` abre los archivos con `with`; `unittest.log` de `20261028-integracion` no contiene `ResourceWarning` |
| DEF-003 | **El CLI devuelve código de salida 1 en consultas exitosas.** `print_response()` (`src/jobrunner/cli.py`) evalúa `"error" in response`; el JSON de todo trabajo trae la clave `error` (con valor `null`), así que `submit` y `status` de un trabajo existente terminan con código 1 aunque no haya error. `list` no se ve afectado. Incumple RF-17. Corrección sugerida: `response.get("error")`. | TC-001, TC-004 | Abierto. Pruebas que lo detectan: `test_submit_exitoso_termina_con_codigo_0`, `test_status_y_list_exitosos_terminan_con_codigo_0` |
| DEF-004 | **Zombis de trabajos terminados que nadie consulta.** `JobManager.poll()` solo se llama desde `status`, `list` y `cancel`; un trabajo que termina y no se consulta queda como proceso zombi (`[true] <defunct>`) hasta la siguiente consulta. Afecta RF-29 y RNF-33. La corrección prevista es el ciclo de 0,5 s del servidor (minuta 20/10, ADR-0004). | TC-020, TC-024 | Cerrado. El ciclo de 0,5 s del servidor (`tick()`, ADR-0004) recoge los procesos terminados; `test_servidor_inactivo_no_deja_zombis` pasa sin marca |

## Comportamiento aún no implementado (fallos esperados)

| Prueba (`expectedFailure`) | Motivo | Cuándo se quita la marca |
|---|---|---|
| `test_cierre_ordenado_no_deja_huerfanos` | Al recibir Ctrl+C el servidor no cancela los trabajos `RUNNING` y el hijo queda huérfano (RF-15, RNF-25, RNF-30; TC-009). Lo resuelve el cierre controlado de ADR-0006. | Al implementar ADR-0006: la prueba pasará y `unittest` avisará de un «unexpected success» |

## Pendiente de integración

Los PR #32 (servidor y CLI) y #34 (corrección de DEF-001 y DEF-002) ya están en `main`.

| Pendiente | Efecto en la verificación |
|---|---|
| Corregir DEF-003 | TC-001 y TC-004 pasan a PASS al repetir `verify.sh`. |
| Cierre controlado (ADR-0006) | Se quita la marca `expectedFailure` restante de `verif/integration/test_procesos.py` (`test_cierre_ordenado_no_deja_huerfanos`). |

## TC citados en los ADR y fuera del Avance 1

| TC | Origen | Tema | Hito |
|---|---|---|---|
| TC-002 | ADR-0001 | Paralelismo con procesos separados (GIL) | 2 |
| TC-007, TC-022 | ADR-0002 | Escrituras concurrentes en SQLite | 2 |
| TC-023 | ADR-0003 | Contrato de mensajes JSON | 3 |
