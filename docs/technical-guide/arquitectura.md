# Arquitectura de JobRunner

## Componentes

JobRunner está compuesto por tres piezas:

1. **CLI (cli.py)** — cliente de línea de comandos que el usuario invoca directamente. Traduce cada comando (submit, status, list, cancel) en una petición JSON y la envía al servidor por un socket Unix.

2. **Servidor (server.py)** — proceso daemon que escucha en un socket Unix, recibe una línea JSON por petición, la despacha al JobManager y devuelve la respuesta como una línea JSON.

3. **Executor (executor.py, clase JobManager)** — lógica central que crea, ejecuta, consulta y cancela trabajos, lanzándolos como subprocesos del sistema operativo.

## Recorrido de una solicitud

El flujo completo de un comando submit es el siguiente:

1. El usuario corre python3 -m jobrunner.cli submit -- sleep 5.

2. CLI arma el JSON {"cmd": "submit", "argv": ["sleep", "5"]} y lo envía por el socket Unix al servidor.

3. Servidor recibe la línea, la parsea, y llama a JobManager.submit(argv).

4. JobManager.submit() decide según el lugar disponible (ADR-0004): si hay menos de max_jobs trabajos en ejecución, crea el Job y lo lanza con subprocess.Popen (que internamente hace fork + exec) y pasa a RUNNING; si no hay lugar pero la cola tiene espacio (queue_size), el Job queda en QUEUED y se agrega a la cola FIFO; si la cola está llena lanza ColaLlena, no crea ningún trabajo y el servidor responde con un error.

5. El tiempo de inicio (started_at) se registra cuando el trabajo sale de la cola y se lanza como proceso, no cuando llega.

6. El servidor ejecuta JobManager.tick() cada 0.5 s y antes de atender cada solicitud. tick() recoge los procesos terminados (poll()), aplica el escalamiento de cancelación y arranca trabajos de la cola mientras haya lugar. Así el estado y el código de salida (exit_code) se actualizan aunque nadie consulte status o list.

7. El servidor arma la respuesta JSON con el estado actual del trabajo y la devuelve por el mismo socket.

8. El CLI recibe la respuesta y la imprime en pantalla.

## Cola y ciclo del servidor

El servidor atiende una solicitud a la vez, pero ninguna operación espera: accept() tiene un tiempo de espera de 0.5 s y, en cada vuelta del ciclo, el servidor llama a JobManager.tick().

1. poll(): recoge los procesos terminados. Un trabajo cuyo ID está en la tabla de cancelaciones pasa a CANCELED; los demás pasan a SUCCEEDED o FAILED según su código de salida.

2. Escalamiento: si pasaron 5 s desde una cancelación y el proceso sigue vivo, se envía SIGKILL al grupo de procesos.

3. Arranque desde la cola: mientras haya menos de max_jobs procesos en ejecución, se saca el primer trabajo de la cola FIFO y se lanza.

Parámetros del servicio: --max-jobs (por defecto 3) y --queue-size (por defecto 10), por ejemplo ./scripts/run.sh --max-jobs 2 --queue-size 3. Si no hay lugar para correr y la cola está llena, submit se rechaza de inmediato con el mensaje "cola llena (capacidad N); intenta más tarde". Un trabajo aceptado nunca se bloquea ni se pierde. Al guardar cada trabajo en SQLite, los QUEUED sobreviven a un reinicio y recuperar() los vuelve a meter a la cola, en su orden original y respetando max_jobs.

## Cancelación sin bloqueo

cancel() ya no espera al proceso (ADR-0006). Para un trabajo en cola, lo saca de la cola y lo pasa a CANCELED. Para un trabajo en ejecución, envía SIGTERM al grupo de procesos, anota el plazo de 5 s para el SIGKILL y responde de inmediato con el trabajo todavía en RUNNING. El trabajo pasa a CANCELED cuando tick() recoge su proceso. Una segunda cancelación devuelve el estado real sin reenviar señales.

## Eventos de la bitácora relacionados

Además de recibido, iniciado, terminado y cancelado, la cola y la cancelación registran: en_cola (el trabajo espera; incluye su posición), rechazado (cola llena; no se crea trabajo), cancelacion_solicitada (se envió SIGTERM) y escalamiento (se envió SIGKILL).

## Diagrama resumido

CLI -> socket Unix -> Servidor -> JobManager.submit() -> (lugar: Popen -> RUNNING | sin lugar: cola FIFO -> QUEUED | cola llena: ColaLlena) ; cada 0.5 s: tick() -> poll() -> escalamiento -> arrancar de la cola -> codigo de salida -> respuesta JSON -> socket Unix -> CLI

