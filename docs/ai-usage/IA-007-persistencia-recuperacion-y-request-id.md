# IA-007 — Persistencia conectada, recuperacion al arrancar y request_id

| Campo | Valor |
|---|---|
| **Fecha** | 29/10/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 2 - Concurrencia y persistencia (Avance 2) |
| **Artefactos afectados** | src/jobrunner/executor.py, src/jobrunner/server.py, src/jobrunner/cli.py, verif/unit/test_persistencia.py |
| **Clasificacion** | En revision |

## 1. Objetivo

Conectar el modulo `store.py` (PR #45) al `JobManager` para que cada cambio de estado quede guardado, implementar la recuperacion al arrancar del ADR-0005 y el manejo de solicitudes duplicadas con `request_id` (RF-12, RF-13, RF-27, RF-28). Se uso la IA para:

1. Disenar los puntos exactos donde guardar el estado en `submit`, `poll` y `cancel`.

2. Escribir la recuperacion al arrancar y la deteccion de `request_id` repetido.

3. Escribir las pruebas unitarias y comprobar el flujo completo con un servidor real que se reinicia.

## 2. Entrada proporcionada

- La minuta del 20/10/2026 (decisiones 6, 7 y 8) y los ADR-0002 y ADR-0005 ya integrados en `main`.

- El codigo real de `executor.py`, `server.py`, `cli.py` y `store.py` en `main`.

## 3. Resultado recibido

1. `executor.py`: `JobManager` recibe un `Store` opcional y guarda el trabajo tras iniciarlo, al terminar (`poll`) y al cancelarlo. El arranque del proceso se separo en `_iniciar`. Nuevo metodo `recuperar()`: carga el historial, pasa los RUNNING a FAILED con el motivo "interrumpido por reinicio" y termina su grupo de procesos, y reanuda los QUEUED. `submit` acepta `request_id` y devuelve el mismo trabajo si se repite.

2. `server.py`: crea el `Store` en `data/jobrunner.db`, llama a `recuperar()` al arrancar, acepta `request_id` en `submit` y cierra el `Store` al detenerse.

3. `cli.py`: opcion `--request-id` en `submit`.

4. `test_persistencia.py`: 11 pruebas unitarias.

## 4. Revision realizada

- Josue ejecuto las pruebas en WSL.

- Se probo con un servidor real: un trabajo con `request_id`, un reenvio con el mismo `request_id`, la muerte del servidor con `kill -9` y un nuevo arranque; el historial se conservo y el trabajo interrumpido quedo en FAILED.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Guardar el estado en submit, poll y cancel | Adoptado | Aceptado |
| Recuperacion al arrancar segun el ADR-0005 | Adoptado | Aceptado |
| request_id repetido devuelve el mismo trabajo | Adoptado (decision 8 de la minuta) | Aceptado |

## 6. Limitaciones del resultado de la IA

- Un trabajo que termino pero que el servidor no alcanzo a consultar (`poll`) antes de morir queda como FAILED "interrumpido por reinicio", porque su resultado real no se guardo. La revision periodica cada 0.5 s de la decision 3 de la minuta lo reduce.

- La recuperacion de trabajos QUEUED usa el arranque inmediato actual; cuando exista la cola con limite de concurrencia habra que integrarla (PR de Juan Jose).

- La verificacion de la interrupcion durante una escritura (TC-022) sigue pendiente.

- La IA no tuvo acceso al entorno del equipo; las pruebas finales las corre Josue.

## 7. Prueba o verificacion agregada

| Prueba | Que verifica | Resultado |
|---|---|---|
| test_submit_guarda_el_trabajo_en_ejecucion_con_su_pid | submit guarda estado, pid y argv | Cumple |
| test_el_estado_final_queda_guardado | Se guarda el estado final y el codigo de salida | Cumple |
| test_la_cancelacion_queda_guardada | Se guarda CANCELED | Cumple |
| test_reinicio_conserva_el_historial_de_trabajos_terminados | El historial es igual tras reiniciar (TC-007) | Cumple |
| test_recuperacion_marca_running_como_failed_y_termina_su_proceso | RUNNING pasa a FAILED y el proceso muere | Cumple |
| test_recuperar_dos_veces_da_el_mismo_resultado | La recuperacion es idempotente | Cumple |
| test_recuperacion_reanuda_los_trabajos_en_cola | Los QUEUED se reanudan | Cumple |
| test_request_id_repetido_devuelve_el_mismo_trabajo | Un solo trabajo y un solo proceso | Cumple |
| test_request_id_repetido_despues_de_reiniciar | El duplicado se detecta tras reiniciar | Cumple |
| test_request_id_invalido_es_rechazado | request_id vacio o de otro tipo da error | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (29/10/2026)

## 8. Aprendizaje

- Un reinicio solo es seguro si cada cambio de estado se guarda en el momento en que ocurre.

- Un identificador de solicitud que se guarda junto al trabajo permite reconocer duplicados incluso despues de reiniciar.

- Terminar el grupo de procesos de un trabajo interrumpido evita procesos huerfanos tras una caida.
