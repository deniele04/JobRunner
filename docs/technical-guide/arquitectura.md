# Arquitectura de JobRunner

Versión final (entrega final, v1.0.0). Decisiones relacionadas: [ADR-0003](../decisions/0003-mecanismo-de-comunicacion.md), [ADR-0004](../decisions/0004-cola-concurrencia-y-saturacion.md), [ADR-0006](../decisions/0006-cancelacion-escalamiento-y-cierre-controlado.md), [ADR-0007](../decisions/0007-solicitudes-duplicadas-desconexiones-y-clientes.md), [ADR-0008](../decisions/0008-transporte-de-red-y-restriccion-de-acceso.md) y [ADR-0009](../decisions/0009-protocolo-v1.md). El formato de los mensajes está en la [guía del protocolo](protocolo-y-persistencia.md), la seguridad en [seguridad.md](seguridad.md) y los estados en el [modelo de estados](modelo-estados.md).

## Componentes

JobRunner está compuesto por cuatro piezas, todas en `src/jobrunner/` y solo con la biblioteca estándar de Python (ADR-0001):

1. **CLI (cli.py, comando `royito`)** — cliente de línea de comandos. Traduce cada comando (`submit`, `status`, `list`, `cancel`, `output`, `health`) en una solicitud JSON con `"v": 1` y la envía al servicio por el **socket Unix** (por defecto) o por **TCP** (`--host`, `--port` o las variables `JOBRUNNER_HOST` y `JOBRUNNER_PORT`). Calcula su código de salida (0, 1 o 2) y, ante un error, imprime operación, causa y acción.

2. **Servidor (server.py)** — proceso que arranca todo lo demás: abre el socket Unix y, si se pidió `--listen`, el socket TCP; recupera los trabajos guardados; y ejecuta el ciclo principal. Contiene `responder()` (valida la solicitud: JSON, objeto, versión) y `handle_request()` (despacha cada comando al `JobManager`).

3. **Red (red.py, clase `Red`)** — el componente de red. Atiende **todas las conexiones, Unix y TCP, en un solo hilo con `selectors`**. Por cada conexión guarda un búfer de entrada y otro de salida, corta los mensajes en cada `\n`, aplica los límites del protocolo (64 KiB por mensaje, cierre a los 30 s sin datos) y, solo en los sockets TCP, aplica la **lista de orígenes permitidos** (`--allow`). Cuenta las conexiones abiertas y los accesos rechazados (`Red.estadisticas()`, que usa `health`). No conoce los trabajos: recibe un callback que convierte una línea en una respuesta.

4. **Executor (executor.py, clase `JobManager`)** — lógica central: crea, ejecuta, consulta, cancela y lista trabajos, lanzándolos como subprocesos del sistema operativo; lee su salida (`output`) y resume el estado del servicio (`health`). Es el único lugar donde cambian los estados. Guarda cada cambio en SQLite (store.py) y registra los eventos en la bitácora (bitacora.py).

```
royito ──Unix──┐                       ┌─ responder() ── handle_request() ── JobManager ── subprocesos
               ├─► Red (selectors) ───►│                                        │
royito ──TCP───┘   lista --allow       └─ Red.estadisticas() ──► health         ├─ Store (SQLite)
 (--host/--port)   límites 64 KiB/30 s                                          └─ bitácora
```

## Recorrido de una solicitud

El flujo de un `submit` local es el siguiente; el de un cliente remoto solo cambia los pasos 2 y 3.

1. El usuario corre `royito submit -- sleep 5`.

2. La CLI abre la conexión: el socket Unix (sin `--host`) o, con `--host`, una conexión TCP (hasta 5 s para conectar). Si no puede, termina con «no se pudo conectar a HOST:PUERTO» y la acción sugerida.

3. La CLI envía una línea `{"v": 1, "cmd": "submit", "argv": ["sleep", "5"]}\n`.

4. `Red` acepta la conexión. **Solo si es TCP**, comprueba que la IP de origen esté en `--allow` (por defecto solo `127.0.0.1` y `::1`); si no lo está, cierra la conexión sin leer nada, la cuenta como rechazada y registra `acceso_rechazado` con la IP. El socket Unix no pasa por esta lista.

5. `Red` lee sin bloquearse y acumula los bytes en el búfer de la conexión. Cuando aparece un `\n`, entrega la línea completa; si una línea supera 64 KiB responde `mensaje demasiado grande` y cierra la conexión.

6. `responder()` interpreta la línea: si no es JSON válido, no es un objeto o trae una versión `v` distinta de 1, responde con un error. Si no, llama a `handle_request()`.

7. `handle_request()` llama a `JobManager.submit(argv)`. Según el lugar disponible (ADR-0004): si hay menos de `max_jobs` trabajos en ejecución, crea el `Job` y lo lanza con `subprocess.Popen` y pasa a `RUNNING`; si no hay lugar pero la cola tiene espacio (`queue_size`), queda en `QUEUED` en la cola FIFO; si la cola está llena lanza `ColaLlena`, no crea ningún trabajo y se responde un error.

8. El tiempo de inicio (`started_at`) se registra cuando el trabajo sale de la cola y se lanza como proceso, no cuando llega.

9. `responder()` agrega `"v": 1` como primer campo de la respuesta y `Red` la escribe en el búfer de salida de esa conexión, terminada en `\n`. Si el cliente no puede recibir todo de una vez, el resto se envía cuando el socket vuelva a estar listo, sin detener a los demás clientes.

10. La CLI lee hasta el `\n`, revisa que `v` sea 1, imprime el JSON y sale con 0 (o con 1 si la respuesta es un error del servicio).

Una conexión puede llevar varias solicitudes; se responden en el mismo orden. Aunque haya muchas conexiones abiertas, **una solicitud completa se ejecuta de una vez y sin intercalarse con otra**: por eso el estado de los trabajos solo cambia en un hilo y no hay candados (ADR-0007, ADR-0009).

### `output`: leer la salida de un trabajo

`handle_request()` valida `id`, `stream` (`stdout` o `stderr`) y `max_bytes` (1 a 65 536, por defecto 65 536) y llama a `JobManager.output()`. Esta abre `data/<id>.out` o `.err`, se coloca a `max_bytes` del final y lee ese tramo; responde `{id, stream, data, truncated}`. Solo lee archivos: **no cambia ningún estado ni toca la cola**. Un trabajo en cola todavía no tiene archivos y devuelve `data` vacío. Lo que cabe en la respuesta es como máximo el final de 64 KiB; para más hay que leer el archivo en el equipo del servicio.

### `health`: resumen de salud

`handle_request()` ejecuta `tick()` (para no informar procesos que ya terminaron como si siguieran vivos), pide a `JobManager.health()` la versión, el tiempo activo, el conteo de trabajos por estado, `running` frente a `max_jobs`, `queued` frente a `queue_size` y el estado de la base (una lectura de prueba), y le suma lo que informa `Red.estadisticas()`: conexiones abiertas (incluida la de quien pregunta) y accesos rechazados. Tampoco cambia ningún estado de trabajo. Si la base falla, `health` lo informa en el campo `database` en lugar de fallar.

## Cola y ciclo del servidor

El servidor atiende varias conexiones, pero ninguna operación espera: en cada vuelta del ciclo principal ejecuta `JobManager.tick()` y luego `Red.atender(0.5)`, que espera como máximo 0.5 s a que haya algo que leer o escribir. Sin tráfico, `tick()` corre cada 0.5 s; con tráfico corre al terminar cada tanda de solicitudes. `status`, `list` y `health` también lo ejecutan antes de responder.

1. `poll()`: recoge los procesos terminados. Un trabajo cuyo ID está en la tabla de cancelaciones pasa a `CANCELED`; los demás pasan a `SUCCEEDED` o `FAILED` según su código de salida.

2. Escalamiento: si pasaron 5 s desde una cancelación y el proceso sigue vivo, se envía `SIGKILL` al grupo de procesos.

3. Arranque desde la cola: mientras haya menos de `max_jobs` procesos en ejecución, se saca el primer trabajo de la cola FIFO y se lanza.

Parámetros del servicio: `--max-jobs` (por defecto 3), `--queue-size` (por defecto 10), `--listen [HOST:PUERTO]` (sin valor, `127.0.0.1:7070`; sin la opción no se abre ningún puerto TCP) y `--allow RED` (repetible, solo con `--listen`). Por ejemplo `./scripts/run.sh --max-jobs 2 --queue-size 3 --listen 192.168.1.20:7070 --allow 192.168.1.30/32`. El servicio se niega a arrancar si `--listen` o `--allow` abrirían el servicio a `0.0.0.0`, `::` o una red pública (ADR-0008).

Si no hay lugar para correr y la cola está llena, `submit` se rechaza de inmediato con el mensaje `cola llena (capacidad N); intenta más tarde`. Un trabajo aceptado nunca se bloquea ni se pierde. Al guardar cada trabajo en SQLite, los `QUEUED` sobreviven a un reinicio y `recuperar()` los vuelve a meter a la cola, en su orden original y respetando `max_jobs`.

## Cancelación sin bloqueo

`cancel()` no espera al proceso (ADR-0006). Para un trabajo en cola, lo saca de la cola y lo pasa a `CANCELED`. Para un trabajo en ejecución, envía `SIGTERM` al grupo de procesos, anota el plazo de 5 s para el `SIGKILL` y responde de inmediato con el trabajo todavía en `RUNNING`. El trabajo pasa a `CANCELED` cuando `tick()` recoge su proceso. Una segunda cancelación (con el trabajo todavía cancelándose o ya `CANCELED`) devuelve el estado real, sin error y sin reenviar señales. Cancelar por TCP o por el socket Unix es lo mismo.

## Cierre controlado

Con Ctrl+C o `SIGTERM` el servidor (ADR-0006): 1) cierra los sockets de escucha y todas las conexiones (`Red.cerrar()`: no se acepta nada nuevo y los puertos TCP quedan libres; lo que estaba listo para enviarse se intenta mandar una vez), 2) cancela los trabajos en ejecución, 3) conserva los `QUEUED` para el siguiente arranque y 4) registra el cierre y elimina el socket. Un segundo Ctrl+C fuerza el `SIGKILL`.

## Eventos de la bitácora relacionados

Además de `recibido`, `iniciado`, `terminado` y `cancelado`, la cola y la cancelación registran: `en_cola` (el trabajo espera; incluye su posición), `rechazado` (cola llena; no se crea trabajo), `cancelacion_solicitada` (se envió `SIGTERM`) y `escalamiento` (se envió `SIGKILL`). La red registra: `acceso_rechazado` (origen fuera de `--allow`, con su IP), `solicitud_invalida` (JSON inválido, versión no soportada, mensaje demasiado grande o solicitud incompleta), `cliente_desconectado` (el envío de la respuesta falló porque el cliente ya no estaba), `conexion_inactiva` (30 s sin datos) y `red_cerrada` (al cerrar el servicio). La bitácora no guarda los argumentos de los trabajos.

## Diagrama resumido

CLI (`royito`) -> socket Unix o TCP (`--host`/`--port`) -> Red (selectors; en TCP, lista `--allow`; búfer por conexión; 64 KiB y 30 s) -> `responder()` (JSON, objeto, versión `v`) -> `handle_request()` -> `JobManager` (`submit` | `status` | `list` | `cancel` | `output` | `health`) -> (`submit`: lugar: `Popen` -> `RUNNING` | sin lugar: cola FIFO -> `QUEUED` | cola llena: `ColaLlena`) ; cada 0.5 s: `tick()` -> `poll()` -> escalamiento -> arrancar de la cola -> código de salida -> respuesta JSON con `"v": 1` -> Red -> CLI
