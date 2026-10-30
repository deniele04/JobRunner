# IA-010 — Bitácora de eventos, documentación del Avance 2 y coordinación de la entrega

| Campo | Valor |
|---|---|
| **Fecha** | 30/10/2026 (uso entre el 20/10 y el 30/10/2026) |
| **Herramienta** | Claude |
| **Usado por** | Daniel Alejandro Huerta Camberos |
| **Revisado por** | Pendiente de revisión |
| **Hito** | Hito 2 — Concurrencia y persistencia (Avance 2) |
| **Artefactos afectados** | `src/jobrunner/bitacora.py`, `verif/unit/test_bitacora.py`, `docs/decisions/0007-solicitudes-duplicadas-desconexiones-y-clientes.md`, `project-management/CRONOGRAMA.md`, `project-management/minutas/2026-10-20.md`, `verif/test-cases/TC-025.md`, `docs/user-guide/bitacora.md`, `docs/user-guide/guia-de-usuario.md`, `docs/incidents/INC-001-caida-del-servidor-por-desconexion.md`, estado de los ADR-0002, ADR-0005, ADR-0006 y ADR-0007 |
| **Clasificación** | Mixto: resultados aceptados y modificados (ver sección 5) |

## 1. Objetivo

La minuta del 20/10/2026 asigna a Daniel el código de la bitácora de eventos, el incidente técnico, la guía de usuario y el cierre de la entrega. Se usó la IA para:

1. Escribir el módulo de la bitácora y sus pruebas, y conectarlo al ejecutor y al servidor.
2. Redactar el ADR-0007, el cronograma v4, el caso TC-025 y la sección de bitácora de la guía.
3. Reproducir y documentar el incidente INC-001.
4. Redactar la guía de usuario.
5. Revisar el avance del equipo, repartir los pendientes del 30/10 y actualizar los documentos con lo que se integró.

## 2. Entrada proporcionada

- El enunciado del Avance 2, la minuta del 20/10/2026 y los PDF del profesor (estándares y plan de verificación).
- El código de `main` (`server.py`, `executor.py`, `cli.py`, `jobs.py`, `store.py`) y los PR del equipo.

Prompts utilizados (textuales, algunos):

> 1. "De acuerdo a la minuta, elabora un avance de mi parte para hacer un Pull request"
> 2. "dame la minuta, el incidente y la guia de usuario"
> 3. "dame el analisis actual, y si falta algo dime que hacer cada integrante y en orden"
> 4. "Bien, dame mis documentos corregidos a excepcion del que tengo que esperar a Diego"

## 3. Resultado recibido

1. `bitacora.py` (un evento por línea con fecha UTC, nivel, tipo e ID del trabajo; sin argumentos del trabajo) y 5 pruebas en `test_bitacora.py`.
2. ADR-0007 (atención secuencial de clientes, `request_id` opcional y reglas de desconexión), cronograma v4, TC-025 y la sección de bitácora de la guía.
3. INC-001 con su reproducción (cliente que se va sin leer la respuesta y bytes no UTF-8), evidencia, hipótesis, causa y una corrección propuesta.
4. Guía de usuario con instalación, uso del CLI, estados, códigos de salida y errores comunes.
5. Análisis del avance con pruebas ejecutadas sobre `main`, lista de pendientes por integrante y la actualización de INC-001, la guía, la bitácora y el estado de los ADR.

## 4. Revisión realizada

- La bitácora se probó con `./scripts/test.sh` antes del PR #42 y con el servidor real (envío, cancelación y comando inexistente).
- El INC-001 se reprodujo sobre `main` (commit `572140d`) con los dos casos documentados.
- La tabla de eventos de `bitacora.md` se armó con las llamadas reales a la bitácora en `executor.py` y `server.py`.
- Las pruebas de robustez del servidor se ejecutaron sobre el commit anterior a la corrección: fallan sin ella y pasan con ella.
- Al revisar el avance se encontraron con la IA dos problemas reales en `main` (una prueba marcada como fallo esperado que ya pasaba y una prueba de doble cancelación que fallaba al azar), que se asignaron a Diego y a Juan.

## 5. Cambios aplicados

| Resultado de la IA | Decisión del equipo | Clasificación |
|---|---|---|
| Módulo `bitacora.py` y sus 5 pruebas | Integrados en el PR #42 | **Aceptado** |
| Minuta del 20/10 con secciones de "versión revisada", "estado del proyecto" y "pendientes" | Se quitaron esas secciones a petición de Daniel | **Modificado** |
| ADR-0007, cronograma v4, TC-025 y sección de bitácora | Integrados en el PR #50 | **Aceptado** |
| Corrección propuesta para INC-001 (`except OSError`, `except ValueError` y evento `respuesta_no_entregada`) | Se integró la corrección de Josué (PR #51), con excepciones específicas y el evento `cliente_desconectado`; el INC-001 se actualizó a esa versión | **Modificado** |
| Guía de usuario | Integrada en el PR #50 y actualizada con la cola, la cancelación sin bloqueo y la persistencia | **Aceptado** |
| Archivos de tareas detallados por integrante para el 30/10 | Se reemplazaron por una lista corta de pendientes, porque eran largos y confundían | **Modificado** |

## 6. Limitaciones del resultado de la IA

- Los códigos RF/RNF se tomaron de la minuta y de los ADR; el documento de requisitos no está en el repositorio.
- La primera corrección propuesta para INC-001 no fue la que se integró; el documento tuvo que actualizarse después.
- La IA no tiene acceso de escritura al repositorio: todos los cambios los subió Daniel desde su rama.

## 7. Prueba o verificación agregada

| Artefacto | Prueba | Resultado |
|---|---|---|
| `bitacora.py` | `test_bitacora.py` (5 pruebas) y TC-025 | Cumple |
| INC-001 | TC-019: `test_cliente_que_se_desconecta_antes_de_la_respuesta` y `test_bytes_que_no_son_texto_valido` | Cumple |
| Guía de usuario y `bitacora.md` | Comandos y respuestas comparados con el servidor real | Cumple |

**Verificó:** Daniel Alejandro Huerta Camberos (30/10/2026)

## 8. Aprendizaje

- Un registro de incidente debe describir la corrección que realmente se integró, no la que se propuso.
- Sacar la lista de eventos del código evita que la documentación se quede atrás.
- Para coordinar al equipo funcionan mejor las indicaciones cortas que los planes detallados.
