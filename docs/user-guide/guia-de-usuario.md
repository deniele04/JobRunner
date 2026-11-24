# Guía de usuario — JobRunner

JobRunner ejecuta comandos de Linux como **trabajos** en segundo plano. Un servicio (el servidor) lanza y controla cada trabajo, y el usuario lo opera desde un cliente de línea de comandos (el CLI) para enviar, consultar, listar y cancelar trabajos, ver su salida y revisar la salud del servicio, en la misma computadora o desde otra por una red privada o VPN.

Esta guía explica cómo instalarlo y usarlo sin ayuda del equipo (RNF-23).

## 1. Requisitos

- Linux (Ubuntu 22.04 o 24.04) o Windows con WSL2.
- Python 3.10 o superior (Ubuntu ya lo trae).
- `git`.
- No se necesitan permisos de administrador ni dependencias externas.

## 2. Instalación

**Solo en Windows, la primera vez:** abrir PowerShell como administrador, ejecutar `wsl --install`, reiniciar la computadora y abrir **Ubuntu** desde el menú Inicio.

En la terminal de Linux o de Ubuntu:

```bash
python3 --version          # debe ser 3.10 o superior
cd ~
git clone https://github.com/deniele04/JobRunner.git
cd JobRunner
./scripts/setup.sh
```

`setup.sh` debe terminar con `Construcción OK`.

> **Importante en WSL:** clona el repositorio dentro de tu carpeta personal (`~`), no en `/mnt/c/...`. En las carpetas de Windows el socket del servicio no funciona.

## 3. Iniciar y detener el servicio

En una terminal:

```bash
cd ~/JobRunner
./scripts/run.sh
```

Debe aparecer `JobRunner escuchando en data/jobrunner.sock`. Deja esa terminal abierta mientras uses JobRunner.

Opciones del servicio:

```bash
./scripts/run.sh --max-jobs 2 --queue-size 3
```

| Opción | Qué hace | Por defecto |
|---|---|---|
| `--max-jobs` | Cuántos trabajos se ejecutan al mismo tiempo | 3 |
| `--queue-size` | Cuántos trabajos pueden esperar en la cola | 10 |
| `--listen [HOST:PUERTO]` | Además del socket Unix, escucha por TCP para clientes de otros equipos. Sin valor usa `127.0.0.1:7070`. Sin esta opción no se abre ningún puerto | Desactivado |
| `--allow RED` | Red de origen permitida por TCP, en CIDR (se puede repetir). Con `--allow` solo se aceptan las redes indicadas: para conectarte también por TCP desde el mismo equipo, agrega `--allow 127.0.0.1`. El socket local no pasa por esta lista. Solo con `--listen` | Solo `127.0.0.1` y `::1` |

Para atender a otro equipo, ver la [conexión entre dos equipos](conexion-lan-vpn.md). Nunca abras puertos en el router: JobRunner solo se usa en `localhost`, en una red local privada o en una VPN.

Si ya se ejecutan `--max-jobs` trabajos, los nuevos esperan en la cola (`QUEUED`) y arrancan en orden de llegada. Si la cola también está llena, el trabajo se rechaza.

Los trabajos se guardan en `data/jobrunner.db`. Si el servicio se reinicia, el historial se conserva: los trabajos que estaban en `QUEUED` vuelven a la cola y los que estaban en `RUNNING` quedan en `FAILED` con el motivo «interrumpido por reinicio».

Para detener el servicio, presiona **Ctrl+C** en esa terminal (o envía `SIGTERM`). El cierre es controlado: deja de aceptar conexiones y cierra las abiertas, libera el puerto TCP, cancela los trabajos en ejecución, conserva la cola para el siguiente arranque y elimina el socket. Un segundo Ctrl+C fuerza el cierre inmediato.

## 4. Usar el cliente

Abre **otra** terminal y prepárala una vez:

```bash
cd ~/JobRunner
export PATH="$PWD/scripts:$PATH"
```

Esto habilita el comando `royito` en esa terminal. (Funciona igual con `./scripts/royito`, o con `PYTHONPATH=src python3 -m jobrunner.cli` si prefieres el comando largo.)

| Para… | Comando |
|---|---|
| Enviar un trabajo | `royito submit -- <comando> [argumentos]` |
| Consultar un trabajo | `royito status <id>` |
| Listar todos los trabajos | `royito list` |
| Listar por estado | `royito list --state <ESTADO>` |
| Cancelar un trabajo | `royito cancel <id>` |
| Ver la salida de un trabajo | `royito output <id>` (con `--stderr` para los errores) |
| Ver la salud del servicio | `royito health` |
| Usar un servicio de otro equipo | `royito --host HOST --port PUERTO <comando>` (sección 4.7) |
| Ver la ayuda | `royito --help`, o `royito <comando> --help` |

### 4.1 Enviar un trabajo

```bash
royito submit -- sh -c 'echo hola; exit 3'
```

El servicio responde con los datos del trabajo. Copia el valor de `"id"`: lo necesitas para consultarlo o cancelarlo.

Si no estás seguro de que el envío llegó (por ejemplo, se cortó la conexión), repítelo con `--request-id`: el servicio no crea un segundo trabajo y devuelve el mismo, con `"duplicado": true`.

```bash
royito submit --request-id respaldo-1 -- sleep 30
```

El `request_id` lleva de 1 a 64 caracteres: letras, números, `-` y `_`. Si lo reusas con otro comando, el servicio lo rechaza.

Escribe siempre `--` antes del comando. Sin él, las opciones del comando (por ejemplo, el `-l` de `ls -l`) se confunden con opciones del cliente.

### 4.2 Consultar un trabajo

```bash
royito status <id>
```

| Campo | Significado |
|---|---|
| `id` | Identificador único del trabajo |
| `argv` | Comando y argumentos que se enviaron |
| `state` | Estado actual (sección 5) |
| `exit_code` | Código de salida cuando el trabajo termina (sección 6) |
| `created_at`, `started_at`, `finished_at` | Fecha y hora (UTC) de recepción, inicio y fin |
| `stdout_path`, `stderr_path` | Archivos con la salida y los errores del trabajo |
| `error` | Motivo cuando el trabajo no pudo ejecutarse, o la señal que lo terminó |
| `pid` | Número del proceso del trabajo en el sistema |
| `request_id` | Identificador opcional del cliente para no crear el mismo trabajo dos veces (ADR-0007) |

### 4.3 Listar trabajos

```bash
royito list
royito list --state FAILED
```

El filtro acepta mayúsculas o minúsculas: `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED` o `CANCELED`.

### 4.4 Cancelar un trabajo

```bash
royito cancel <id>
```

El servicio envía SIGTERM al trabajo y responde de inmediato, así que la respuesta todavía dice `RUNNING`. Consulta con `status`: en unos instantes pasa a `CANCELED`. Si a los 5 segundos sigue vivo, el servicio lo obliga a terminar (SIGKILL).

Un trabajo en `QUEUED` se cancela al instante y nunca llega a ejecutarse. Cancelar dos veces el mismo trabajo devuelve su estado, sin repetir la señal.

No se puede cancelar un trabajo que ya terminó.

### 4.5 Ver la salida de un trabajo

La salida normal y la de errores se guardan por separado. Con `royito output` se leen desde el cliente, también por red:

```bash
royito output <id>             # lo que el trabajo imprimió
royito output <id> --stderr    # los errores del trabajo
royito output <id> --raw       # solo el texto, sin el JSON
```

La respuesta es un JSON con `id`, `stream` (`stdout` o `stderr`), `data` (el texto) y `truncated`. Se devuelve el **final** de la salida, hasta 64 KiB; si había más al principio, `truncated` es `true` (con `--raw` aparece un aviso). `--max-bytes N` pide menos (de 1 a 65536). Un trabajo en cola todavía no tiene salida y devuelve `data` vacío; uno en ejecución devuelve lo que lleva hasta ese momento.

En el equipo del servicio también se pueden leer los archivos directamente: `cat data/<id>.out` y `cat data/<id>.err`.

### 4.6 Ver la salud del servicio

```bash
royito health
```

| Campo | Significado |
|---|---|
| `version` | Versión del software del servicio |
| `uptime_seconds` | Segundos desde que arrancó el servicio |
| `jobs_by_state` | Cuántos trabajos hay en cada estado (`QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELED`) |
| `running` y `max_jobs` | Trabajos en ejecución frente al límite (`--max-jobs`) |
| `queued` y `queue_size` | Trabajos en cola frente a su capacidad (`--queue-size`) |
| `database` | `ok` si la base de datos responde; `error: ...` si no |
| `clients` | Conexiones abiertas ahora, incluida la del propio `royito health` |
| `rejected_access` | Conexiones TCP rechazadas desde que arrancó el servicio por venir de una red que no está en `--allow` |

### 4.7 Usar un servicio de otro equipo

Si el servicio se inició con `--listen`, desde otro equipo se usa el mismo `royito`, con `--host` y `--port` **antes** del comando:

```bash
royito --host 192.168.1.20 --port 7070 submit -- sleep 30
royito --host 192.168.1.20 --port 7070 list
```

Para no repetirlos, usa variables de entorno (la opción tiene prioridad sobre la variable):

```bash
export JOBRUNNER_HOST=192.168.1.20
export JOBRUNNER_PORT=7070        # opcional: sin él se usa 7070
royito list
```

Sin host, `royito` usa el socket Unix local, como siempre. `--port` sin `--host` es un error. Los comandos y las respuestas son los mismos que en local.

## 5. Estados de un trabajo

| Estado | Significado |
|---|---|
| `QUEUED` | Recibido; espera en la cola porque ya se ejecutan `--max-jobs` trabajos |
| `RUNNING` | En ejecución |
| `SUCCEEDED` | Terminó con código 0 |
| `FAILED` | Terminó con un código distinto de 0, o no se pudo ejecutar |
| `CANCELED` | Se canceló antes de terminar |

`SUCCEEDED`, `FAILED` y `CANCELED` son estados finales: ya no cambian.

## 6. Códigos de salida de un trabajo

| `exit_code` | Significado |
|---|---|
| `0` | El trabajo terminó bien |
| Positivo (por ejemplo `3`) | El trabajo terminó con error; el número lo decide el propio programa |
| `-15` | Lo terminó la señal SIGTERM: se canceló y obedeció |
| `-9` | Lo terminó la señal SIGKILL: se canceló y hubo que forzarlo |
| `null` | El trabajo no ha terminado, o no se pudo ejecutar (ver `error`) |

En bash, los dos casos con señal se muestran como 143 y 137 (128 + el número de la señal).

## 7. Bitácora

El servicio registra cada evento en `data/jobrunner.log`. El formato, los tipos de evento y cómo consultarla están en [bitacora.md](bitacora.md).

## 8. Errores comunes

`royito` termina con código **0** si la operación se hizo (un trabajo `FAILED` también es una operación hecha), **1** si el servicio la rechazó o no se pudo conectar, y **2** si el comando se escribió mal. Ante un error, la respuesta JSON sale en la salida normal y en la salida de errores aparece una línea `Error al <operación>: <causa>. Que hacer: <acción>.`

### Al usar el cliente

| Situación | Lo que responde | Qué hacer |
|---|---|---|
| El servicio no está iniciado (local) | `Error: no se pudo conectar al servidor en data/jobrunner.sock. Esta corriendo ./scripts/run.sh?` | Iniciar el servicio (sección 3) |
| No hay servicio en ese host y puerto | `Error: no se pudo conectar a HOST:PUERTO (...)` | Revisa que el servicio use `--listen`, que el host y el puerto sean correctos y que tu IP esté en `--allow` |
| Tu IP no está en `--allow` | `Error: el servidor en HOST:PUERTO cerro la conexion sin responder...` | Pide que agreguen tu IP con `--allow` en el servicio |
| `--port` sin `--host` | `--port requiere --host (o la variable JOBRUNNER_HOST)` | Agrega `--host` o define `JOBRUNNER_HOST` |
| El puerto no es válido | `puerto invalido` o `puerto fuera de rango` | Usa un número de 1 a 65535 |
| El comando no existe | El trabajo queda en `FAILED` con `"error": "No se pudo ejecutar '...'"` | Revisar el nombre del comando |
| La cola está llena | `{"error": "cola llena (capacidad N); intenta más tarde"}` | Esperar a que terminen trabajos, o iniciar el servicio con un `--queue-size` mayor |
| El ID no existe | `{"error": "no existe el trabajo <id>"}` (en `cancel` y `output`, con `No` en mayúscula) | Copiar el ID completo desde `submit` o `list` |
| Cancelar un trabajo terminado | `{"error": "El trabajo ... ya termino en estado ...; no se puede cancelar"}` | Nada: el trabajo ya terminó |
| Estado inválido en `list --state` | `{"error": "Estado desconocido: ..."}` | Usar uno de los cinco estados (sección 5) |
| `output --max-bytes` fuera de rango | `{"error": "max_bytes debe ser un entero de 1 a 65536"}` | Usar un valor de 1 a 65536 |
| El archivo de salida ya no existe | `{"error": "la salida del trabajo ... no esta disponible..."}` | Revisar que no se hayan borrado archivos de `data/` en el servicio |
| El servicio se está cerrando | `{"error": "el servicio se esta cerrando; no acepta trabajos nuevos"}` | Esperar a que vuelva a iniciar y repetir |
| Subcomando mal escrito | `invalid choice: '...' (choose from 'submit', 'status', 'list', 'cancel', 'output', 'health')` | Usar uno de los seis subcomandos |
| `submit` sin comando | `the following arguments are required: argv` | Escribir el comando después de `--` |
| Opciones sin `--` (por ejemplo `submit ls -l`) | `unrecognized arguments: -l` | Escribir `--` antes del comando |

### Al iniciar el servicio con red

El servicio se niega a arrancar y explica por qué:

| Situación | Lo que responde | Qué hacer |
|---|---|---|
| `--listen 0.0.0.0:7070` | `no se puede escuchar en 0.0.0.0: abriria el servicio a cualquier red; usa una direccion privada o la de Tailscale` | Usar la IP privada o la de Tailscale |
| `--listen` con IP pública | `no se puede escuchar en ... no es privada; usa loopback, 10.x, 172.16-31.x, 192.168.x o 100.64-127.x (Tailscale)` | Igual que arriba |
| `--listen` sin puerto | `direccion invalida: ... (usa HOST:PUERTO)` | Escribir `HOST:PUERTO`, por ejemplo `127.0.0.1:7070` |
| Puerto mayor a 65535 | `puerto fuera de rango: ...` | Usar un puerto válido, por ejemplo 7070 |
| `--allow 0.0.0.0/0` | `red no permitida: 0.0.0.0/0 abriria el servicio a cualquier origen` | Permitir solo la IP del cliente (`/32`) o una red privada |
| `--allow` con red pública | `red no permitida: ... no es privada (...)` | Igual que arriba |
| `--allow` mal escrito | `red invalida: ... (usa CIDR, p. ej. 192.168.1.0/24)` | Escribir la red en CIDR |
| `--allow` sin `--listen` | `--allow solo tiene efecto con --listen` | Agregar `--listen` |
| La IP de `--listen` no es de este equipo | `Error: no se pudo abrir el servicio: [Errno 99] Cannot assign requested address` | Usar la IP que muestra `tailscale ip -4` o `hostname -I` en ese equipo |
| El puerto ya está en uso | `Error: no se pudo abrir el servicio: [Errno 98] Address already in use` | Cerrar el otro programa o usar otro puerto |

Si algo falla durante la operación, sigue la [guía de diagnóstico](diagnostico.md).

## 9. Problemas conocidos

Se actualizan en las release notes de cada versión. La lista completa, con su estado, está en [defectos-y-limitaciones.md](../defectos-y-limitaciones.md).

- El acceso en red no autentica ni cifra: solo se limita por la red de origen (`--allow`). Úsalo en `localhost`, en una red privada o en una VPN, nunca expuesto a Internet.
- Un trabajo que terminó justo antes de una caída del servicio queda como `FAILED` «interrumpido por reinicio», porque su resultado no alcanzó a guardarse.
- Una solicitud de más de 64 KiB se rechaza, y una conexión que no envía nada durante 30 segundos se cierra; mientras tanto no retrasa a los demás clientes.
- Solo se aceptan direcciones IPv4 de Tailscale (`100.x`); las IPv6 de Tailscale no están permitidas.
