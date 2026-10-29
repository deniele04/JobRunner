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

Una segunda cancelacion sobre un trabajo que ya se esta cancelando devuelve su estado real sin reenviar senales. Si el proceso termino solo antes de ser recogido, se recoge primero con su resultado real (SUCCEEDED o FAILED) y cancelar responde que ya termino: un estado final nunca se reescribe como CANCELED.
