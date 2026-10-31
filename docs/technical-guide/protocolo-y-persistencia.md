# Guía técnica: protocolo y persistencia

Esta guía describe cómo se comunican el CLI y el servidor, y cómo el servidor guarda y recupera el estado de los trabajos. Complementa la [arquitectura](arquitectura.md) y el [modelo de estados](modelo-estados.md). Decisiones relacionadas: [ADR-0002](../decisions/0002-modelo-de-persistencia.md), [ADR-0003](../decisions/0003-mecanismo-de-comunicacion.md) y [ADR-0005](../decisions/0005-recuperacion-al-arrancar.md).

## 1. Protocolo cliente-servidor

### Transporte
- Socket Unix de flujo (`AF_UNIX`), por defecto en `data/jobrunner.sock` (variable `JOBRUNNER_SOCKET` o argumento `--socket`).
- Una solicitud por conexión: el cliente se conecta, envía **una línea** con un objeto JSON terminada en salto de línea (`\n`), lee **una línea** con la respuesta y cierra.
- El servidor atiende una conexión a la vez. Si el cliente no completa la línea en 5 segundos, el servidor descarta la conexión y sigue con la siguiente.

### Solicitudes
Toda solicitud es un objeto JSON con el campo `cmd`.

| `cmd` | Campos | Respuesta correcta |
|---|---|---|
| `submit` | `argv` (lista no vacía de textos no vacíos), `request_id` (opcional, texto no vacío) | El trabajo |
| `status` | `id` | El trabajo |
| `list` | `state` (opcional: QUEUED, RUNNING, SUCCEEDED, FAILED o CANCELED) | `{"jobs": [...]}` |
| `cancel` | `id` | El trabajo, ya en estado CANCELED |

Ejemplo de `submit` y su respuesta (el trabajo):

```
{"cmd": "submit", "argv": ["sleep", "30"], "request_id": "demo-1"}

{"id": "63c4512b-3526-45a4-91cf-0879d31b2d64", "argv": ["sleep", "30"],
 "created_at": "2026-10-29T16:21:26.597483+00:00", "state": "RUNNING",
 "exit_code": null, "started_at": "2026-10-29T16:21:26.597714+00:00",
 "finished_at": null, "stdout_path": "data/63c4512b-....out",
 "stderr_path": "data/63c4512b-....err", "error": null,
 "request_id": "demo-1", "pid": 565}
```

Campos de un trabajo: `id`, `argv`, `created_at`, `state`, `exit_code`, `started_at`, `finished_at`, `stdout_path`, `stderr_path`, `error`, `request_id` y `pid`. `error` es `null` cuando no hubo error. `exit_code` negativo significa que el proceso murió por una señal (por ejemplo, `-15` es SIGTERM).

### Errores
Un error de la operación es un objeto con **únicamente** la clave `error`:

| Situación | Respuesta |
|---|---|
| Comando desconocido | `{"error": "comando desconocido: foo"}` |
| `argv` vacío o con elementos no válidos | `{"error": "argv debe ser una lista no vacia de strings"}` |
| `request_id` vacío o que no es texto | `{"error": "request_id debe ser un string no vacio"}` |
| `status` o `cancel` sin `id` | `{"error": "falta id"}` |
| ID inexistente | `{"error": "no existe el trabajo <id>"}` |
| Cancelar un trabajo ya terminado | `{"error": "El trabajo <id> ya termino en estado <ESTADO>; no se puede cancelar"}` |
| Línea que no es JSON ni UTF-8 válido | `{"error": "JSON invalido"}` |

Importante: el campo `error` de un trabajo (`"error": null` o un texto como `SIGTERM`) **no** es un error de la operación. El CLI sale con código 1 solo cuando la respuesta contiene únicamente la clave `error`.

### Duplicados y desconexiones (`request_id`)
- Si `submit` trae un `request_id` que ya existe, el servidor devuelve el trabajo existente y no crea otro proceso. Se registra el evento `duplicado` en la bitácora.
- Una solicitud recibida completa se aplica aunque el cliente se desconecte antes de leer la respuesta. El cliente puede confirmarla con `status`, `list` o reenviando el mismo `request_id`.
- Sin `request_id`, cada `submit` crea un trabajo nuevo.
- Desde el CLI: `royito submit --request-id <texto> <comando>`.

## 2. Persistencia

### Dónde se guarda
Todo vive en el directorio del socket (por defecto `data/`):

| Archivo | Contenido |
|---|---|
| `jobrunner.db` | Base SQLite con una fila por trabajo |
| `jobrunner.log` | Bitácora de eventos |
| `<id>.out`, `<id>.err` | Salida estándar y de error de cada trabajo |

### Esquema
Una tabla, `jobs`, definida en `src/jobrunner/store.py`:

```sql
CREATE TABLE IF NOT EXISTS jobs (
  id           TEXT PRIMARY KEY,
  request_id   TEXT UNIQUE,
  argv         TEXT NOT NULL,           -- lista en JSON
  state        TEXT NOT NULL CHECK (state IN
               ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELED')),
  exit_code    INTEGER,
  error        TEXT,
  pid          INTEGER,                 -- líder del grupo de procesos
  created_at   TEXT NOT NULL,
  started_at   TEXT,
  finished_at  TEXT,
  stdout_path  TEXT,
  stderr_path  TEXT
)
```

`request_id` es `UNIQUE`: la base de datos impide dos trabajos con el mismo identificador. Los trabajos sin `request_id` guardan NULL y no chocan entre sí. Las fechas están en ISO 8601 UTC.

### Cuándo se guarda
Solo el servidor escribe. Cada escritura es una transacción propia (`Store.save` usa `with conn:`): se guarda completa o no se guarda. El `JobManager` guarda un trabajo:
1. Al iniciarlo (con su `pid`) o al fallar el arranque del proceso.
2. Al terminar, cuando `poll()` recoge su código de salida (ocurre en cada `status`, `list` o `cancel`).
3. Al cancelarlo.

### Retención
Se conservan todos los registros y archivos de salida. No hay borrado automático en el Hito 2.

## 3. Recuperación al arrancar

Antes de aceptar solicitudes, el servidor llama a `JobManager.recuperar()` (ADR-0005):

| Estado guardado | Qué hace el servidor |
|---|---|
| QUEUED | Lo reanuda: lo inicia de nuevo y registra `recuperado` |
| RUNNING | Termina su grupo de procesos si sigue vivo (SIGTERM y, tras 5 s, SIGKILL), lo pasa a FAILED con `error = "interrumpido por reinicio"` y registra `recuperado` |
| SUCCEEDED, FAILED, CANCELED | No los toca; quedan disponibles para `status` y `list` |

La recuperación es idempotente: repetirla da el mismo resultado, porque los estados ya cambiados no se vuelven a tocar.

## 4. Limitaciones conocidas
- Un trabajo que terminó pero que el servidor no consultó antes de caer queda en FAILED «interrumpido por reinicio», porque su resultado real no se guardó.
- El PID guardado podría haberse reutilizado por otro proceso. Se mitiga enviando la señal al grupo de procesos solo si existe y es accesible; se acepta el riesgo residual (ADR-0005).
- El servidor atiende una solicitud a la vez y el CLI no tiene tiempo de espera propio si el servidor no responde.
- `list` con un estado desconocido responde `error interno: Estado desconocido: <X>` en lugar de un mensaje de validación.
- Una solicitud con JSON válido que no es un objeto responde con un error interno.

## 5. Pruebas relacionadas
TC-007 (reinicio sin perder trabajos), TC-018 (duplicados y desconexiones) y TC-022 (interrupción durante una escritura). Ver `verif/test-cases/` y `verif/unit/`.
