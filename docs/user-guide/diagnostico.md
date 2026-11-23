# Guía de diagnóstico

Qué revisar cuando JobRunner no se comporta como se espera, incluido un incidente que nadie anunció. Todos los comandos se corren desde la raíz del repositorio (`~/JobRunner`).

## 1. Primeros cinco minutos

Antes de cambiar nada, revisa en este orden y guarda lo que veas:

```bash
pgrep -af jobrunner.server                     # 1. ¿El servidor está vivo? ¿Hay más de uno?
ls -l data/jobrunner.sock                      # 2. ¿Existe el socket?
royito list | head -20                         # 3. ¿Responde? (usa: export PATH="$PWD/scripts:$PATH")
tail -20 data/jobrunner.log                    # 4. ¿Qué fue lo último que pasó?
grep " ERROR " data/jobrunner.log | tail -10   # 5. ¿Qué errores hubo?
royito health                                  # 6. Trabajos por estado, límites, base de datos, clientes y accesos rechazados
```

Y, si hay trabajos o red de por medio:

```bash
verif/scripts/procesos.sh revisar --patron 'sleep'     # zombis y huérfanos (cambia 'sleep' por el comando de los trabajos)
ps -o pid,ppid,pgid,stat,cmd -p $(pgrep -d, -f jobrunner.server)   # estado del servidor
ps -eo pid,ppid,pgid,stat,cmd | grep -v grep | grep -E "jobrunner|sleep"   # servidor y trabajos
ss -ltnp | grep 7070                                   # ¿quién escucha en el puerto TCP?
ss -tnp | grep 7070                                    # conexiones abiertas al puerto
```

En la columna `STAT` de `ps`: `S` o `R` = normal, `Z` = zombi, `T` = detenido (por ejemplo con `kill -STOP`).

## 2. Síntomas y qué hacer

### El cliente no se conecta

| Lo que ves | Revisa | Causa probable | Qué hacer |
|---|---|---|---|
| `Error: no se pudo conectar al servidor en data/jobrunner.sock...` y `pgrep` no muestra nada | `tail data/jobrunner.log`: ¿la última línea es `servicio_detenido`? | Sin `servicio_detenido`: el servidor murió de golpe (`kill -9` o un error). Con `servicio_detenido`: alguien lo detuvo | Busca un `Traceback` en la terminal del servidor y reinícialo con `./scripts/run.sh`. Al arrancar recupera los trabajos (sección 2.3) |
| El mismo error, pero `pgrep` muestra el servidor | ¿Acaba de arrancar? | Está recuperando trabajos: puede tardar unos segundos mientras termina los procesos que quedaron vivos | Espera a `JobRunner escuchando` |
| `royito` se queda esperando y no responde | `ps -o stat -p <pid del servidor>` muestra `T` | El servidor está detenido con `SIGSTOP` | `kill -CONT <pid del servidor>`. Los trabajos y las solicitudes siguen donde iban |
| `pgrep` muestra **dos** servidores | `grep servicio_iniciado data/jobrunner.log \| tail -2` | Se inició un segundo servidor con la misma carpeta `data/`. El segundo tomó el socket y marcó los trabajos del primero como interrumpidos (DEF-008) | Detén los dos (Ctrl+C o `kill -INT`), revisa con `procesos.sh` que no queden trabajos sueltos y arranca uno solo |
| `Permission denied` al correr un script | — | Se perdió el permiso de ejecución | `chmod +x scripts/royito scripts/*.sh verif/scripts/*.sh` |

### 2.1 Desde otro equipo (TCP)

| Lo que ves | Revisa | Causa probable | Qué hacer |
|---|---|---|---|
| `royito` dice «cerro la conexion sin responder» (u otro cliente recibe «Connection reset by peer») | `grep acceso_rechazado data/jobrunner.log` en el servidor, o `rejected_access` en `royito health` | La IP del cliente no está en `--allow`. Con `--allow`, solo entran las redes indicadas (`127.0.0.1` incluido solo si se agrega) | Reinicia el servidor con `--allow <IP del cliente>/32` |
| `royito` dice «no se pudo conectar a HOST:PUERTO (Connection refused)» | `ss -ltn \| grep 7070` en el servidor | El servidor no escucha por TCP (falta `--listen`) o escucha en otra IP o puerto | Revisa la línea `JobRunner escuchando en ... (TCP)` al arrancar |
| `royito` dice «no se pudo conectar a HOST:PUERTO (timed out)» o se queda esperando | `tailscale status` en los dos equipos y la prueba con `curl` de [conexion-lan-vpn.md](conexion-lan-vpn.md) | Problema de red: Tailscale apagado, cuentas distintas o firewall | Corrige la red antes de revisar JobRunner |
| La conexión se cierra sola tras un rato sin enviar nada | `grep conexion_inactiva data/jobrunner.log` | Comportamiento normal: 30 s sin datos (ADR-0009) | Nada; el cliente abre otra conexión |
| `mensaje demasiado grande (maximo 65536 bytes)` | `grep "mensaje demasiado grande" data/jobrunner.log` | El mensaje superó 64 KiB | Enviar comandos más cortos |
| `version de protocolo no soportada` | — | El cliente es de otra versión del protocolo | Usar el cliente del mismo repositorio que el servidor |

Para separar un problema de red de uno de JobRunner, primero prueba `royito --host <IP> --port 7070 health` desde el cliente. Si falla, prueba sin `royito` (cambia la IP y el puerto):

```bash
python3 -c 'import socket; s=socket.create_connection(("100.101.102.103", 7070), timeout=5); s.sendall(b"{\"cmd\":\"list\"}\n"); print(s.recv(200))'
```

Si responde `{"v": 1, ...}`, la red y el servidor funcionan.

### 2.2 Trabajos

| Lo que ves | Revisa | Causa probable | Qué hacer |
|---|---|---|---|
| `cola llena (capacidad N)` | `royito list --state RUNNING` y `royito list --state QUEUED` | Ya hay `--max-jobs` en ejecución y `--queue-size` en espera | Espera, cancela alguno o reinicia con valores mayores |
| Un trabajo sigue en `RUNNING` después de cancelarlo | `grep "job=<id>" data/jobrunner.log` | El trabajo ignora SIGTERM; a los 5 s llega `escalamiento` y SIGKILL | Espera 5 s y vuelve a consultar: queda `CANCELED` con `-9` |
| Un trabajo pasó a `FAILED` con `exit_code` `-9` y `error` `SIGKILL` sin que nadie lo cancelara | `grep "job=<id>" data/jobrunner.log` | Alguien terminó su proceso desde fuera (`kill -9 <pid>`) | Nada que corregir: el servidor lo detectó y no quedó zombi. Confírmalo con `ps -o pid,stat,cmd -p <pid>` (no debe salir nada) |
| Un trabajo `FAILED` con «No se pudo ejecutar» | `royito status <id>` | El comando no existe o no tiene permiso de ejecución | Corrige el comando |
| Aparece un `ZOMBI` en `procesos.sh` | `ps -o stat -p <pid del servidor>` | El servidor está detenido (`T`) y no recoge a sus hijos | `kill -CONT <pid del servidor>`; en menos de 0,5 s los recoge |
| Aparece un `HUERFANO` en `procesos.sh` | `pgrep -af jobrunner.server` | El servidor murió de golpe y sus trabajos siguen vivos | Reinicia el servidor: al arrancar termina esos grupos de procesos y marca los trabajos (sección 2.3) |
| `royito health` muestra `database` distinto de `ok` | `df -h .` y `ls -l data/` | La base no responde: disco lleno, permisos o archivo dañado | Libera espacio o corrige permisos; con el servidor apagado, revisa la base con el comando de la sección 2.3 |
| `running` llega a `max_jobs` y `queued` a `queue_size` en `royito health` | `royito list --state RUNNING` | El servicio está saturado | Espera, cancela trabajos o reinicia con límites mayores |

### 2.3 Después de una caída del servidor

Al reiniciar con `./scripts/run.sh`:

```bash
grep recuperado data/jobrunner.log | tail
verif/scripts/procesos.sh revisar --patron 'sleep'      # debe decir: Sin zombis ni huérfanos
```

- Los trabajos que estaban en `RUNNING` quedan `FAILED` «interrumpido por reinicio» y sus procesos se terminan.
- Los que estaban en `QUEUED` vuelven a la cola.
- Los terminados no cambian.

Para revisar la base directamente (con el servidor apagado):

```bash
python3 -c "import sqlite3; c=sqlite3.connect('data/jobrunner.db'); print(c.execute('pragma integrity_check').fetchone()[0]); print(c.execute('select state, count(*) from jobs group by state').fetchall())"
```

Debe imprimir `ok` y el número de trabajos por estado.

### 2.4 Al iniciar el servicio

| Lo que ves | Qué hacer |
|---|---|
| `Address already in use` | `ss -ltnp \| grep <puerto>` muestra quién lo usa. Si es un servidor viejo, detenlo; si no, usa otro puerto |
| `Cannot assign requested address` | La IP de `--listen` no es de este equipo. Usa la de `tailscale ip -4` o `hostname -I` |
| `no se puede escuchar en ...` o `red no permitida` | El servidor rechazó una dirección pública o `0.0.0.0` a propósito. Ver la [guía de usuario](guia-de-usuario.md#al-iniciar-el-servicio-con-red) |
| `no space left on device` | `df -h .` y `du -sh data/`. Libera espacio; los archivos `.out` y `.err` no se borran solos |

## 3. Guardar la evidencia de un incidente

Antes de reiniciar o corregir, guarda lo que se vio:

```bash
mkdir -p evidencia-incidente
cp data/jobrunner.log evidencia-incidente/
verif/scripts/procesos.sh revisar --patron 'sleep' > evidencia-incidente/procesos.txt 2>&1
ps -eo pid,ppid,pgid,stat,cmd > evidencia-incidente/ps.txt
royito list > evidencia-incidente/list.json 2>&1
royito health > evidencia-incidente/health.json 2>&1
```

Con eso se redacta el registro en `docs/incidents/` (ver el [índice de incidentes](../incidents/README.md)) y, si deja un defecto, se agrega a [defectos-y-limitaciones.md](../defectos-y-limitaciones.md).
