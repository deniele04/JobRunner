# Guía de usuario — JobRunner

JobRunner ejecuta comandos de Linux como **trabajos** en segundo plano. Un servicio (el servidor) lanza y controla cada trabajo, y el usuario lo opera desde un cliente de línea de comandos (el CLI) para enviar, consultar, listar y cancelar trabajos.

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

Si ya se ejecutan `--max-jobs` trabajos, los nuevos esperan en la cola (`QUEUED`) y arrancan en orden de llegada. Si la cola también está llena, el trabajo se rechaza.

Los trabajos se guardan en `data/jobrunner.db`. Si el servicio se reinicia, el historial se conserva: los trabajos que estaban en `QUEUED` vuelven a la cola y los que estaban en `RUNNING` quedan en `FAILED` con el motivo «interrumpido por reinicio».

Para detener el servicio, presiona **Ctrl+C** en esa terminal.

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
| Ver la ayuda | `royito --help` |

### 4.1 Enviar un trabajo

```bash
royito submit -- sh -c 'echo hola; exit 3'
```

El servicio responde con los datos del trabajo. Copia el valor de `"id"`: lo necesitas para consultarlo o cancelarlo.

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

La salida normal y la de errores se guardan por separado:

```bash
cat data/<id>.out      # lo que el trabajo imprimió
cat data/<id>.err      # los errores del trabajo
```

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

| Situación | Lo que responde | Qué hacer |
|---|---|---|
| El servicio no está iniciado | `Error: no se pudo conectar al servidor en data/jobrunner.sock. Esta corriendo ./scripts/run.sh?` | Iniciar el servicio (sección 3) |
| El comando no existe | El trabajo queda en `FAILED` con `"error": "No se pudo ejecutar '...'"` | Revisar el nombre del comando |
| La cola está llena | `{"error": "cola llena (capacidad N); intenta más tarde"}` | Esperar a que terminen trabajos, o iniciar el servicio con un `--queue-size` mayor |
| El ID no existe | `{"error": "no existe el trabajo <id>"}` | Copiar el ID completo desde `submit` o `list` |
| Cancelar un trabajo terminado | `{"error": "El trabajo ... ya termino en estado ...; no se puede cancelar"}` | Nada: el trabajo ya terminó |
| Estado inválido en `list --state` | `{"error": "error interno: Estado desconocido: ..."}` | Usar uno de los cinco estados (sección 5) |
| Subcomando mal escrito | `invalid choice: '...' (choose from 'submit', 'status', 'list', 'cancel')` | Usar uno de los cuatro subcomandos |
| `submit` sin comando | `the following arguments are required: argv` | Escribir el comando después de `--` |
| Opciones sin `--` (por ejemplo `submit ls -l`) | `unrecognized arguments: -l` | Escribir `--` antes del comando |

## 9. Problemas conocidos

Se actualizan en las release notes de cada versión.

- Solo funciona en la misma computadora; el acceso en red llega en el Avance 3.
- Un trabajo que terminó justo antes de una caída del servicio queda como `FAILED` «interrumpido por reinicio», porque su resultado no alcanzó a guardarse.
- El servicio atiende a un cliente a la vez; un cliente que se conecta y no envía nada retrasa a los demás hasta 5 segundos.
