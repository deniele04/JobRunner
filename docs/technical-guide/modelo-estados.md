# Modelo de estados de un trabajo

## Estados

Un trabajo (Job) puede estar en uno de 5 estados, definidos en jobs.py:

| Estado | Descripcion |
|---|---|
| QUEUED | El trabajo fue aceptado y espera en la cola FIFO a que haya lugar (menos de max_jobs en ejecucion). No tiene proceso ni started_at. |
| RUNNING | El proceso del trabajo esta en ejecucion. Tambien lo esta mientras se cancela, desde que se envia SIGTERM hasta que se recoge su proceso. |
| SUCCEEDED | El proceso termino con codigo de salida 0. |
| FAILED | El proceso termino con codigo de salida distinto de 0, o no pudo lanzarse. |
| CANCELED | El trabajo fue cancelado por el usuario antes de terminar por si solo. |

SUCCEEDED, FAILED y CANCELED son estados finales (FINAL_STATES): una vez alcanzados, el trabajo no puede volver a cambiar de estado.

## Transiciones validas

Las transiciones permitidas, tomadas de VALID_TRANSITIONS en jobs.py, son:

VALID_TRANSITIONS = {

    QUEUED:    {RUNNING, CANCELED},

    RUNNING:   {SUCCEEDED, FAILED, CANCELED},

    SUCCEEDED: set(),

    FAILED:    set(),

    CANCELED:  set(),

}

Es decir:

- QUEUED puede pasar a RUNNING (salio de la cola y se lanzo el proceso; entonces se registra started_at) o CANCELED (se cancelo antes de lanzarse; sale de la cola y nunca arranca).

- RUNNING puede pasar a SUCCEEDED, FAILED o CANCELED.

- Ningun estado final puede transicionar a otro estado.

Cualquier intento de transicion fuera de esta tabla lanza un ValueError en Job.transition().

## Cola

Los trabajos entran en QUEUED cuando ya hay max_jobs trabajos en RUNNING (por defecto 3) y la cola tiene espacio (queue_size, por defecto 10). La cola es FIFO: tick() arranca primero al que llego primero cada vez que se libera un lugar. Si no hay lugar para correr ni para esperar, submit se rechaza con el error "cola llena" y no se crea ningun trabajo, asi que ese rechazo no es un estado. Si el servicio se reinicia, los trabajos QUEUED guardados vuelven a la cola en su orden original.

## Cancelacion

Cuando se cancela un trabajo en estado QUEUED, se saca de la cola y se marca como CANCELED sin que exista un proceso que detener.

Cuando se cancela un trabajo en estado RUNNING, JobManager.cancel() no bloquea al servidor (ADR-0006):

1. Envia SIGTERM al grupo de procesos (os.killpg), pidiendo una terminacion ordenada, y responde de inmediato con el trabajo todavia en RUNNING.

2. El ciclo del servidor (tick(), cada 0.5 s) recoge el proceso cuando termina y entonces el trabajo pasa a CANCELED, con su exit_code (-15 si obedecio SIGTERM) y finished_at.

3. Si a los 5 segundos de la solicitud el proceso sigue vivo, tick() envia SIGKILL al grupo y el trabajo termina en CANCELED con exit_code -9.

Una segunda cancelacion sobre un trabajo que ya se esta cancelando, o que ya esta CANCELED, devuelve su estado real sin reenviar senales y sin error. Si el proceso termino solo antes de ser recogido, se recoge primero con su resultado real (SUCCEEDED o FAILED) y cancelar responde que ya termino: un estado final nunca se reescribe como CANCELED.

## La red no agrega estados

El acceso remoto (TCP) y los comandos `output` y `health` no cambian este modelo: un trabajo sigue teniendo exactamente los cinco estados y las transiciones de la tabla anterior, y solo `JobManager` las ejecuta, en el mismo hilo y en el mismo lugar que antes (ADR-0007, ADR-0009).

- **Una conexión no es un estado del trabajo.** Que un cliente esté conectado, haya sido rechazado por `--allow` o se haya cerrado por inactividad (30 s sin datos) lo lleva `Red` en sus propios contadores (`health` informa `clients` y `rejected_access`); ningún trabajo cambia por eso.
- **Los trabajos no dependen de la conexión que los creó.** Cada trabajo es un proceso hijo del servidor, no del cliente: puede enviarse por un transporte y cancelarse o consultarse por el otro, y seguir viviendo cuando el cliente se va.
- **`output` y `health` solo leen.** `output` abre el archivo de salida y `health` cuenta los trabajos; ninguno hace una transición. Como `status` y `list`, `health` ejecuta antes `tick()`, que solo recoge lo que ya había terminado (`poll()`), arranca de la cola si hay lugar y aplica el escalamiento: son los mismos cambios que habría hecho el ciclo del servidor unos instantes después.
- **Un origen rechazado no deja rastro en los trabajos.** Si la IP no está en `--allow`, la conexión se cierra sin leer nada: no se crea ni se modifica ningún trabajo. Solo queda `acceso_rechazado` en la bitácora y +1 en `rejected_access`.

## Qué pasa si el cliente se desconecta a la mitad

Lo que decide el efecto es si el servidor llegó a recibir la solicitud completa, es decir, la línea terminada en `\n` (ADR-0007):

| Momento de la desconexión | Efecto en los trabajos | Qué queda registrado |
|---|---|---|
| Antes de enviar nada | Ninguno | Nada |
| A mitad de la solicitud (sin `\n`) | **Ninguno.** La solicitud incompleta se descarta: no se crea, cancela ni cambia nada | `solicitud_invalida` con motivo `solicitud incompleta` |
| Con la solicitud completa, antes de leer la respuesta | **La solicitud se aplica una sola vez.** Un `submit` crea su trabajo (`QUEUED` o `RUNNING`) y un `cancel` inicia la cancelación; solo se pierde la respuesta | `cliente_desconectado`, solo si al enviar la respuesta el sistema avisa de que el cliente ya no está (no siempre ocurre; la solicitud se aplicó de todos modos) |
| Con el trabajo ya en ejecución | Ninguno: el trabajo sigue en `RUNNING` hasta terminar, fallar o cancelarse | Nada |

Para saber si una solicitud se aplicó, el cliente consulta con `status` o `list`, o reenvía el `submit` con el mismo `request_id`: el servidor devuelve el trabajo existente con `"duplicado": true` y no crea otro (TC-018). Un cierre del servidor cierra primero las conexiones y después cancela los trabajos en ejecución, como se describe en la [arquitectura](arquitectura.md); los estados guardados en la base son los que recupera el siguiente arranque, sin importar qué clientes estaban conectados. Pruebas: TC-019 (`test_cierra_a_mitad_de_una_solicitud`, `test_cierra_sin_leer_la_respuesta_y_la_solicitud_se_aplica_una_vez`) y TC-012.
