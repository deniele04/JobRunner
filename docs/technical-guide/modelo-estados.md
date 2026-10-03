# Modelo de estados de un trabajo

## Estados

Un trabajo (Job) puede estar en uno de 5 estados, definidos en jobs.py:

| Estado | Descripcion |
|---|---|
| QUEUED | El trabajo fue creado pero aun no se lanza como proceso. |
| RUNNING | El proceso del trabajo esta en ejecucion. |
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

- QUEUED puede pasar a RUNNING (se lanzo el proceso) o CANCELED (se cancelo antes de lanzarse).

- RUNNING puede pasar a SUCCEEDED, FAILED o CANCELED.

- Ningun estado final puede transicionar a otro estado.

Cualquier intento de transicion fuera de esta tabla lanza un ValueError en Job.transition().

## Cancelacion

Cuando se cancela un trabajo en estado QUEUED, simplemente se marca como CANCELED sin que exista un proceso que detener.

Cuando se cancela un trabajo en estado RUNNING, JobManager.cancel() sigue un escalamiento de senales:

1. Envia SIGTERM al grupo de procesos (os.killpg), pidiendo una terminacion ordenada.

2. Espera hasta 5 segundos (proc.wait(timeout=5)) a que el proceso termine por si solo.

3. Si tras esos 5 segundos el proceso sigue vivo, se envia SIGKILL para forzar su terminacion inmediata.

Al terminar, el trabajo queda en estado CANCELED con su exit_code y finished_at registrados.

