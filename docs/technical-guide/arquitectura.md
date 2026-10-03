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

4. JobManager.submit() crea un objeto Job en estado QUEUED, y lo lanza con subprocess.Popen (que internamente hace fork + exec en el sistema operativo).

5. El trabajo pasa a estado RUNNING inmediatamente después de lanzarse.

6. En algún momento posterior, al consultar status o list, el servidor llama a JobManager.poll(), que revisa si el proceso ya terminó y actualiza su código de salida (exit_code) y estado final (SUCCEEDED o FAILED).

7. El servidor arma la respuesta JSON con el estado actual del trabajo y la devuelve por el mismo socket.

8. El CLI recibe la respuesta y la imprime en pantalla.



## Diagrama resumido



CLI -> socket Unix -> Servidor -> JobManager.submit() -> Popen (fork+exec) -> RUNNING -> poll() -> codigo de salida -> respuesta JSON -> socket Unix -> CLI

