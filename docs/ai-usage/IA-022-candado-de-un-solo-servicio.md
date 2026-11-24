# IA-022 — Candado de un solo servicio por carpeta (DEF-008)

| Campo | Valor |
|---|---|
| **Fecha** | 23/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 4 - Operacion remota (entrega final) |
| **Artefactos afectados** | src/jobrunner/server.py, verif/integration/test_def008_servicio_unico.py, docs/defectos-y-limitaciones.md, docs/technical-guide/protocolo-y-persistencia.md, docs/user-guide/diagnostico.md |
| **Clasificacion** | En revision |

## 1. Objetivo

Corregir DEF-008 (RF-15, RNF-08): un segundo servidor sobre la misma carpeta de datos borraba el socket del primero, marcaba sus trabajos en RUNNING como FAILED y terminaba sus procesos, y el primero quedaba corriendo sin que ningun cliente lo alcanzara. Se uso la IA para elegir la correccion, implementarla y escribir las pruebas.

## 2. Entrada proporcionada

- El registro de DEF-008 con sus dos correcciones propuestas (negarse si el socket responde, o un candado fcntl.flock), `server.py` y el ayudante de pruebas de integracion.

## 3. Resultado recibido

1. `_tomar_candado`: candado exclusivo no bloqueante sobre `jobrunner.lock` en la carpeta de datos, tomado antes de tocar el socket o la base. Si otro servicio lo tiene, termina con «ya hay un servicio JobRunner usando la carpeta ...».
2. 9 pruebas con servidor real.
3. Actualizacion del registro de defectos, la guia tecnica y el diagnostico.

## 4. Revision realizada

- Se eligio el candado y no la comprobacion del socket: el candado cubre tambien otro nombre de socket en la misma carpeta (misma base) y no tiene la carrera de dos servicios que arrancan a la vez.
- El sistema libera el candado si el servicio muere de golpe, asi que no queda un candado viejo; hay una prueba con SIGKILL.
- Los trabajos no heredan el candado (el descriptor no es heredable); hay una prueba con un trabajo vivo tras matar al servicio.
- Al correr la suite sin PYTHONUNBUFFERED fallaba test_con_listen_el_puerto_indicado_queda_abierto (TC-013): el aviso de arranque no se vaciaba al redirigir la salida; se agrego flush=True a los avisos de arranque y cierre de server.py.
- Se comprobo que 5 de las 9 pruebas fallan sin la correccion y pasan con ella; la suite completa no cambia de resultado.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Candado `fcntl.flock` sobre `jobrunner.lock` | Adoptado | Aceptado |
| Pruebas y documentacion del candado | Adoptadas | Aceptado |

## 6. Limitaciones del resultado de la IA

- `fcntl` solo existe en Linux y macOS; el proyecto apunta a Linux y WSL2 (ADR-0001).
- El candado no protege una carpeta compartida por red (NFS) entre equipos distintos.

## 7. Prueba o verificacion agregada

| Caso | Pruebas | Resultado |
|---|---|---|
| DEF-008 | test_def008_servicio_unico.py (9) | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (23/11/2026)

## 8. Aprendizaje

- Un candado del sistema operativo es mas robusto que comprobar si el socket responde: se libera solo al morir el proceso y no tiene carrera entre dos arranques simultaneos.
- Una prueba de regresion debe fallar sin la correccion; conviene comprobarlo quitandola un momento.
