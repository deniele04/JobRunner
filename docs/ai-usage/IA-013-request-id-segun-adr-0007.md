# IA-013 — request_id alineado con el ADR-0007

| Campo | Valor |
|---|---|
| **Fecha** | 19/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 4 - Operacion remota (entrega final) |
| **Artefactos afectados** | src/jobrunner/executor.py, src/jobrunner/server.py, verif/unit/test_persistencia.py, verif/unit/test_reinicio_servidor.py, verif/test-cases/TC-018.md, verif/scripts/verify.sh |
| **Clasificacion** | En revision |

## 1. Objetivo

La revision del PR de los ADR encontro que el codigo de `submit` no cumplia el ADR-0007: no marcaba el duplicado, no rechazaba un comando distinto con el mismo `request_id` y no validaba el largo. Se uso la IA para corregir el codigo (en vez de rebajar el ADR) y agregar las pruebas.

## 2. Entrada proporcionada

- El comentario de la revision, el ADR-0007, `executor.py`, `server.py`, TC-018 y las pruebas existentes de `request_id`.

## 3. Resultado recibido

1. `validar_request_id` (1 a 64 caracteres: letras, numeros, `-` y `_`) y la excepcion `RequestIdEnUso`.
2. Un reenvio con el mismo comando devuelve el trabajo con `"duplicado": true`; con otro comando devuelve error y no crea nada.
3. 5 pruebas nuevas; TC-018 y `verify.sh` actualizados.

## 4. Revision realizada

- Se ejecutaron las 182 pruebas del proyecto: todas pasan; las pruebas existentes no cambiaron de nombre.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Corregir el codigo segun el ADR-0007 | Adoptado | Aceptado |
| Pruebas nuevas en TC-018 | Adoptadas; Diego debe confirmar el mapeo en `verify.sh` | Aceptado |

## 6. Limitaciones del resultado de la IA

- La comparacion de comandos usa solo `argv`; no considera variables de entorno ni directorio de trabajo, que el servicio no recibe.
- Los `request_id` ya guardados con caracteres fuera de la regla siguen funcionando en la base, pero no se pueden reenviar.

## 7. Prueba o verificacion agregada

| Caso | Pruebas | Resultado |
|---|---|---|
| TC-018 | 5 nuevas en test_persistencia.py y test_reinicio_servidor.py | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (19/11/2026)

## 8. Aprendizaje

- Un ADR marcado "sin decisiones abiertas" hay que contrastarlo con el codigo antes de aprobarlo.
