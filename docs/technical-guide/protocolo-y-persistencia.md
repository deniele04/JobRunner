# Guía técnica: protocolo y persistencia

Esta guía describe cómo se comunican los clientes y el servidor (protocolo v1), y cómo el servidor guarda y recupera el estado de los trabajos. Con ella, un tercero puede escribir su propio cliente sin leer el código. Complementa la [arquitectura](arquitectura.md), el [modelo de estados](modelo-estados.md) y la [seguridad](seguridad.md). Decisiones relacionadas: [ADR-0002](../decisions/0002-modelo-de-persistencia.md), [ADR-0003](../decisions/0003-mecanismo-de-comunicacion.md), [ADR-0005](../decisions/0005-recuperacion-al-arrancar.md), [ADR-0007](../decisions/0007-solicitudes-duplicadas-desconexiones-y-clientes.md), [ADR-0008](../decisions/0008-transporte-de-red-y-restriccion-de-acceso.md) y [ADR-0009](../decisions/0009-protocolo-v1.md).

## 1. Protocolo cliente-servidor (v1)

### 1.1 Transportes
El servidor ofrece dos transportes con el mismo protocolo:

| Transporte | Cómo se activa | Quién puede conectarse |
|---|---|---|
| Socket Unix (`AF_UNIX`) | Siempre. Ruta por defecto `data/jobrunner.sock` (variable `JOBRUNNER_SOCKET` o argumento del servidor) | Quien tenga permiso sobre el archivo del socket |
| TCP | Solo con `--listen [HOST:PUERTO]`; sin valor, `127.0.0.1:7070`. Sin `--listen` no se abre ningún puerto | Solo los orígenes permitidos (sección 1.6 y [seguridad](seguridad.md)) |

Ejemplo para escuchar en una red privada (VPN Tailscale): `python3 -m jobrunner.server --listen 100.64.0.5:7070 --allow 100.64.0.0/10`.

### 1.2 Mensajes y delimitación
- Cada mensaje es **un objeto JSON en una sola línea, en UTF-8, terminada en salto de línea** (`\n`, byte 0x0A). El JSON no debe contener saltos de línea sin escapar.
- Una conexión puede llevar **varias solicitudes**: el servidor responde **una línea por solicitud, en el mismo orden** en que llegaron. Un cliente puede enviar una y esperar, o enviar varias seguidas.
- Un mensaje puede llegar en pedazos (varios envíos o incluso byte a byte): el servidor lo reensambla hasta ver el salto de línea. Las líneas en blanco se ignoran.
- Si el cliente se cierra con una solicitud incompleta (sin salto de línea), esa solicitud **no se procesa** (queda `solicitud_invalida` con motivo `solicitud incompleta` en la bitácora).
- El cliente debe leer hasta recibir el salto de línea de la respuesta, no asumir que llega en un solo `recv`.

### 1.3 Límites
| Límite | Valor | Qué pasa si se excede |
|---|---|---|
| Tamaño de un mensaje | 64 KiB (65 536 bytes, sin contar el salto de línea) | Respuesta `{"v": 1, "error": "mensaje demasiado grande..."}` y se cierra la conexión |
| Inactividad de una conexión | 30 s sin recibir datos | El servidor cierra la conexión |
| Trabajos en ejecución | `--max-jobs` (por defecto 3) | Los demás esperan en cola |
| Cola de espera | `--queue-size` (por defecto 10) | `submit` responde `cola llena` |
| `request_id` | 1 a 64 caracteres: letras, números, `-` y `_` | Error de validación |

Un cliente lento o que no lee su respuesta no bloquea a los demás: el servidor atiende todas las conexiones con un solo hilo y selectores, sin esperar a ninguna.

### 1.4 Campo de versión `v`
- **Toda respuesta** lleva `"v": 1` como primer campo (éxito, error, JSON inválido, mensaje demasiado grande).
- En la solicitud, `v` es opcional: si falta se toma como 1. Solo se acepta el **entero 1** (no `"1"`, `1.0` ni `true`).
- Cualquier otro valor recibe `{"v": 1, "error": "version de protocolo no soportada: <valor> (soportada: 1)"}`; no se ejecuta nada, se registra `solicitud_invalida` y la conexión sigue abierta. La versión se revisa antes que el comando.
- Un cliente debe rechazar una respuesta con una `v` distinta de la que habla. Si la respuesta no trae `v` (servidor anterior a v1), puede aceptarla.
- La CLI `royito` envía `"v": 1` y aplica estas reglas.

### 1.5 Comandos
Toda solicitud es un objeto con el campo `cmd` (y opcionalmente `v`).

| `cmd` | Campos | Respuesta correcta |
|---|---|---|
| `submit` | `argv` (lista no vacía de textos no vacíos), `request_id` (opcional) | El trabajo |
| `status` | `id` | El trabajo |
| `list` | `state` (opcional: QUEUED, RUNNING, SUCCEEDED, FAILED o CANCELED) | `{"v": 1, "jobs": [...]}` |
| `cancel` | `id` | El trabajo, ya en estado CANCELED |
| `output` | `id`, `stream` (opcional: `stdout` por defecto o `stderr`), `max_bytes` (opcional: entero de 1 a 65536) | `{"v": 1, "id", "stream", "data", "truncated"}` (sección 1.8) |
| `health` | Ninguno | El resumen de salud (sección 1.8) |

Ejemplo (los saltos de línea son solo para leer; en el cable va todo en una línea):

```
{"v": 1, "cmd": "submit", "argv": ["sleep", "30"], "request_id": "demo-1"}

{"v": 1, "id": "63c4512b-3526-45a4-91cf-0879d31b2d64", "argv": ["sleep", "30"],
 "created_at": "2026-10-29T16:21:26.597483+00:00", "state": "RUNNING",
 "exit_code": null, "started_at": "2026-10-29T16:21:26.597714+00:00",
 "finished_at": null, "stdout_path": "data/63c4512b-....out",
 "stderr_path": "data/63c4512b-....err", "error": null,
 "request_id": "demo-1", "pid": 565}
```

Campos de un trabajo: `id`, `argv`, `created_at`, `state`, `exit_code`, `started_at`, `finished_at`, `stdout_path`, `stderr_path`, `error`, `request_id` y `pid`. `error` es `null` cuando no hubo error. `exit_code` negativo significa que el proceso murió por una señal (por ejemplo, `-15` es SIGTERM). Si el `submit` repite un `request_id` ya usado con el mismo comando, la respuesta es el trabajo existente con `"duplicado": true`; el primer envío no lleva ese campo.

Un cliente mínimo en Python (TCP):

```python
import json, socket

with socket.create_connection(("127.0.0.1", 7070)) as c:
    c.sendall(json.dumps({"v": 1, "cmd": "list"}).encode() + b"\n")
    datos = b""
    while not datos.endswith(b"\n"):
        trozo = c.recv(4096)
        if not trozo:
            break
        datos += trozo
respuesta = json.loads(datos)
if respuesta.get("v", 1) != 1:
    raise RuntimeError("version de protocolo distinta")
```

### 1.6 Orígenes permitidos (TCP)
- Sin `--allow`, solo se aceptan conexiones desde `127.0.0.1` y `::1`.
- Con `--allow RED` (repetible, CIDR), **esa lista reemplaza** a la de por defecto: para permitir también el loopback hay que incluirlo (`--allow 127.0.0.1`).
- Un origen no permitido se cierra sin leer nada ni responder, y queda `acceso_rechazado` con su IP en la bitácora. El cliente solo ve que la conexión se cerró.
- Redes aceptables: loopback, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` y `100.64.0.0/10`. El servidor no arranca con `0.0.0.0`, `::` ni direcciones públicas, ni en `--listen` ni en `--allow`.
- El socket Unix no pasa por esta lista.

### 1.7 Errores
Un error de la operación es un objeto cuyas únicas claves son `v` y `error`:

| Situación | Respuesta (`error`) |
|---|---|
| Comando desconocido | `comando desconocido: foo` |
| `argv` vacío o con elementos no válidos | `argv debe ser una lista no vacia de strings` / `argv debe contener solo strings no vacios` |
| `request_id` con formato no válido | `request_id debe ser texto de 1 a 64 caracteres (letras, numeros, - y _)` |
| `request_id` ya usado con otro comando | Error y no cambia nada (evento `request_id_en_uso`) |
| Cola llena | `cola llena (capacidad N); intenta más tarde` |
| Servicio en cierre | `el servicio se esta cerrando; no acepta trabajos nuevos` |
| `status`, `cancel` u `output` sin `id` | `falta id` |
| ID inexistente | `no existe el trabajo <id>` (en `cancel` y `output`, `No existe el trabajo <id>`) |
| `list` con un estado desconocido | `Estado desconocido: <X>` |
| `list` con un `state` que no es texto | `state debe ser texto (QUEUED, RUNNING, SUCCEEDED, FAILED o CANCELED)` |
| `output` con un `stream` no válido | `stream debe ser stdout o stderr` |
| `output` con un `max_bytes` no válido | `max_bytes debe ser un entero de 1 a 65536` |
| `output` de un trabajo terminado cuyo archivo ya no existe | `la salida del trabajo <id> no esta disponible: no existe su archivo <ruta>` |
| Cancelar un trabajo ya terminado | `El trabajo <id> ya termino en estado <ESTADO>; no se puede cancelar` |
| Línea que no es JSON ni UTF-8 válido | `JSON invalido` |
| JSON válido que no es un objeto | `la solicitud debe ser un objeto JSON` |
| Versión no soportada | `version de protocolo no soportada: <valor> (soportada: 1)` |
| Mensaje de más de 64 KiB | `mensaje demasiado grande...` (y se cierra la conexión) |
| Falla inesperada del servidor | `error interno: <detalle>` |

Importante: el campo `error` **dentro de un trabajo** (`"error": null` o un texto como `SIGTERM`) no es un error de la operación. Regla para clientes: es error del servicio la respuesta cuyas claves, **excluyendo `v`**, son exactamente `["error"]`. Un trabajo FAILED es una operación exitosa (la CLI sale con código 0); un error del servicio hace que la CLI salga con código 1.

### 1.8 Comandos `output` y `health`

Los dos solo leen: no cambian el estado de ningún trabajo y funcionan igual por el socket Unix y por TCP.

**`output`** devuelve el **final** de la salida de un trabajo.

```
{"v": 1, "cmd": "output", "id": "63c4512b-3526-45a4-91cf-0879d31b2d64"}
{"v": 1, "cmd": "output", "id": "63c4512b-...", "stream": "stderr", "max_bytes": 1024}

{"v": 1, "id": "63c4512b-3526-45a4-91cf-0879d31b2d64", "stream": "stdout",
 "data": "hola\n", "truncated": false}
```

| Campo de la respuesta | Significado |
|---|---|
| `id` | El trabajo consultado |
| `stream` | `stdout` (`data/<id>.out`) o `stderr` (`data/<id>.err`) |
| `data` | Texto UTF-8: como mucho `max_bytes` bytes (por defecto y como máximo 65 536) tomados del **final** del archivo. Los bytes que no sean UTF-8 válido se sustituyen por `\ufffd`; si el corte cae a la mitad de un carácter, se descarta ese pedazo |
| `truncated` | `true` si el archivo tenía más bytes de los devueltos (se perdió el principio) |

Un trabajo en `QUEUED` todavía no tiene archivos: devuelve `data` vacío. Uno en `RUNNING` devuelve lo que lleva escrito. Los errores (id inexistente, `stream` o `max_bytes` no válidos, archivo borrado) son errores de la operación (sección 1.7). Un cliente que necesite más de 64 KiB debe leer el archivo en el equipo del servicio.

**`health`** devuelve el resumen de salud (RF-24).

```
{"v": 1, "cmd": "health"}

{"v": 1, "version": "1.0.0", "uptime_seconds": 42.7,
 "jobs_by_state": {"QUEUED": 1, "RUNNING": 2, "SUCCEEDED": 5, "FAILED": 1, "CANCELED": 0},
 "running": 2, "max_jobs": 3, "queued": 1, "queue_size": 10,
 "database": "ok", "clients": 2, "rejected_access": 0}
```

| Campo | Significado |
|---|---|
| `version` | Versión del software del servicio (no es la versión `v` del protocolo) |
| `uptime_seconds` | Segundos desde que arrancó el gestor de trabajos, con un decimal |
| `jobs_by_state` | Trabajos por estado; la suma es el total de trabajos que conoce el servicio |
| `running`, `max_jobs` | Trabajos en `RUNNING` y el límite de `--max-jobs` |
| `queued`, `queue_size` | Trabajos en `QUEUED` y el límite de `--queue-size` |
| `database` | `"ok"` si la base responde; `"error: <causa>"` si no (`health` no falla por eso); `"no configurada"` si el gestor se usa sin base |
| `clients` | Conexiones abiertas en este instante, Unix y TCP, incluida la de quien pregunta |
| `rejected_access` | Conexiones TCP cerradas por origen no permitido desde que arrancó el servicio (ADR-0008) |

`health` nunca trae la clave `error`, así que el cliente lo trata como operación exitosa aunque `database` informe un problema.

### 1.9 Duplicados y desconexiones (`request_id`)
- Si `submit` trae un `request_id` que ya existe con el mismo comando, el servidor devuelve el trabajo existente con `"duplicado": true` y no crea otro proceso (evento `duplicado`).
- Una solicitud recibida completa se aplica aunque el cliente se desconecte antes de leer la respuesta. El cliente puede confirmarla con `status`, `list` o reenviando el mismo `request_id`.
- Sin `request_id`, cada `submit` crea un trabajo nuevo.
- Desde la CLI: `royito submit --request-id <texto> <comando>`.

### 1.10 Historial de versiones
| Versión | Cambios |
|---|---|
| v1 | Primera versión versionada (entrega final). Socket Unix y TCP; campo `v` en toda respuesta; varias solicitudes por conexión; límite de 64 KiB y 30 s de inactividad; comandos `submit`, `status`, `list`, `cancel`, `output` y `health`. Antes de v1 (Hitos 1 a 3) el protocolo no llevaba `v` y solo usaba el socket Unix con una solicitud por conexión; un cliente así sigue funcionando porque sin `v` se toma como 1. |

Una versión nueva se anunciaría aquí. Agregar campos opcionales no cambia la versión; cambiar el significado de un campo o quitarlo sí.

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
- La CLI espera hasta 5 s para abrir la conexión TCP, pero no tiene tiempo de espera propio si el servidor acepta y luego no responde.
- `output` devuelve como máximo los últimos 64 KiB de la salida de un trabajo.
- El protocolo no tiene autenticación ni cifrado: la protección es la lista de orígenes y la red privada o VPN (ver [seguridad](seguridad.md)).

## 5. Pruebas relacionadas
TC-007 (reinicio sin perder trabajos), TC-009 (cierre controlado), TC-011 (restricción de acceso), TC-012 (mensajes en red), TC-018 (duplicados y desconexiones), TC-022 (interrupción durante una escritura) y TC-023 (versión del protocolo). Ver `verif/test-cases/` y `verif/integration/`.
