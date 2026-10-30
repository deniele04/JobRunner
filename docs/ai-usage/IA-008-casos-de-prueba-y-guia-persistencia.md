# IA-008 — Casos TC-007, TC-018 y TC-022 y guia tecnica de protocolo y persistencia

| Campo | Valor |
|---|---|
| **Fecha** | 29/10/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 2 - Concurrencia y persistencia (Avance 2) |
| **Artefactos afectados** | verif/test-cases/TC-007.md, TC-018.md, TC-022.md, verif/unit/test_reinicio_servidor.py, verif/unit/test_interrupcion_escritura.py, docs/technical-guide/protocolo-y-persistencia.md |
| **Clasificacion** | En revision |

## 1. Objetivo

La minuta del 20/10/2026 asigna a Josue los casos TC-007, TC-018 y TC-022 y la guia tecnica de protocolo y persistencia, ademas de resolver la decision abierta de como verificar TC-022 de forma repetible. Se uso la IA para:

1. Disenar y escribir las pruebas automatizadas de los tres casos.

2. Redactar los documentos de los casos con el formato de los TC existentes.

3. Redactar la guia tecnica a partir del codigo y de respuestas reales del servidor.

## 2. Entrada proporcionada

- La minuta del 20/10/2026, los ADR-0002, ADR-0003 y ADR-0005 y el formato de TC-005.

- El codigo de `server.py`, `executor.py`, `store.py` y `cli.py`, y el plan y la matriz de verificacion.

## 3. Resultado recibido

1. TC-022 repetible: un proceso hijo escribe en la base y se mata con SIGKILL antes de confirmar la transaccion o justo despues, 10 veces en cada modo; luego se reabre la base y se comprueba el estado y `PRAGMA integrity_check`.

2. TC-007 y TC-018 con servidor real: se levanta el servidor, se mata con SIGKILL, se reinicia y se comprueban historial, recuperacion y duplicados.

3. Los tres documentos de caso y la guia `protocolo-y-persistencia.md`, con ejemplos tomados de respuestas reales del servidor.

## 4. Revision realizada

- Las pruebas se ejecutaron varias veces seguidas sin fallos intermitentes.

- La prueba de desconexion del cliente fallo contra el servidor sin la correccion del PR #51 y paso con ella, lo que confirma que detecta ese defecto.

- Josue ejecuto la suite completa en WSL antes del commit.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Forma repetible de verificar TC-022 (matar con SIGKILL en un punto fijo) | Adoptada; cierra la decision abierta de la minuta | Aceptado |
| Pruebas y documentos de TC-007, TC-018 y TC-022 | Adoptados; estado Pendiente hasta la ejecucion formal de verify.sh | Aceptado |
| Guia tecnica de protocolo y persistencia | Adoptada | Aceptado |

## 6. Limitaciones del resultado de la IA

- La numeracion y el contenido de TC-018 se tomaron de la minuta (tarea de Josue sobre persistencia y duplicados); falta confirmarlos contra el PDF 05.

- Los codigos RF/RNF de cada caso estan por confirmar, porque el documento de requisitos no esta en el repositorio.

- TC-022 verifica la atomicidad de SQLite con la ruta de escritura de `Store`; no simula fallos de disco.

- Los casos quedan en estado Pendiente hasta que Diego ejecute `verify.sh` sobre el commit candidato.

## 7. Prueba o verificacion agregada

| Caso | Pruebas | Resultado |
|---|---|---|
| TC-007 | test_reinicio_servidor.py y test_persistencia.py | Cumple |
| TC-018 | test_reinicio_servidor.py y test_persistencia.py | Cumple |
| TC-022 | test_interrupcion_escritura.py (3 pruebas) | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (29/10/2026)

## 8. Aprendizaje

- Una prueba de interrupcion es repetible si la interrupcion ocurre en un punto fijo del codigo y no depende de tiempos.

- Probar con el servidor real permite descubrir defectos que las pruebas unitarias no ven, como la caida por desconexion del cliente.

- Documentar las limitaciones conocidas en la guia evita que se presenten como funciones terminadas.
