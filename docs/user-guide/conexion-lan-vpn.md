# Conexión entre dos equipos (VPN o LAN privada)

Este instructivo explica cómo usar JobRunner desde otro equipo: un equipo corre el **servidor** y otro usa el **cliente**. Se apoya en el [ADR-0008](../decisions/0008-transporte-de-red-y-restriccion-de-acceso.md) y en la [guía de usuario](guia-de-usuario.md).

## Reglas de seguridad

- El servicio ejecuta comandos del sistema: quien pueda conectarse puede ejecutar programas en el equipo del servidor.
- Solo se usa en localhost, en una LAN privada o en la VPN (Tailscale). **Nunca** se abre un puerto en el router ni se usa una dirección pública (RNF-26).
- El servidor se niega a arrancar con `--listen 0.0.0.0`, `--listen [::]:PUERTO` o una dirección pública, y con `--allow` de redes públicas.
- JobRunner no cifra los mensajes. Entre dos equipos, el cifrado lo da Tailscale. En una LAN sin VPN el tráfico viaja en claro.

## Opción recomendada: Tailscale

Tailscale crea una red privada entre los equipos, con direcciones `100.x.y.z` (rango `100.64.0.0/10`), sin abrir puertos.

### 1. Instalar Tailscale en los dos equipos

Las dos máquinas deben iniciar sesión con **la misma cuenta** de Tailscale (o una debe invitar a la otra a su red).

**Si el servidor corre en WSL**, hay dos formas. Usa **solo una**: Tailscale no debe correr al mismo tiempo en Windows y dentro de WSL.

| Forma | Cuándo usarla | Pasos |
|---|---|---|
| A. Tailscale dentro de WSL | La más sencilla; funciona en Windows 10 y 11 | Sección 1.1 |
| B. Tailscale en Windows y WSL en modo `mirrored` | Windows 11 22H2 o superior, si Tailscale ya está instalado en Windows | Sección 1.2 |

**En Linux nativo o macOS:** instala la aplicación de Tailscale desde [tailscale.com/download](https://tailscale.com/download) e inicia sesión.

#### 1.1 Tailscale dentro de WSL

En la terminal de Ubuntu:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up            # abre el enlace que aparece e inicia sesión
tailscale ip -4              # muestra la IP 100.x.y.z de este equipo
```

Si `sudo tailscale up` responde que no puede conectarse a `tailscaled`, WSL no tiene systemd activo. Actívalo una sola vez:

1. Revisa el archivo: `cat /etc/wsl.conf`.
2. Si no tiene una sección `[boot]`, agrégala: `printf '\n[boot]\nsystemd=true\n' | sudo tee -a /etc/wsl.conf`. Si ya la tiene, ábrelo con `sudo nano /etc/wsl.conf` y agrega la línea `systemd=true` debajo de `[boot]` (guarda con Ctrl+O, Enter y sal con Ctrl+X).
3. En PowerShell: `wsl --shutdown`. Vuelve a abrir Ubuntu y repite `sudo tailscale up`.

#### 1.2 Tailscale en Windows y WSL en modo `mirrored`

1. Instala Tailscale para Windows e inicia sesión.
2. Crea o edita el archivo `%UserProfile%\.wslconfig` con:

   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

3. En PowerShell: `wsl --shutdown` y vuelve a abrir Ubuntu. En modo `mirrored`, WSL usa las mismas direcciones que Windows, incluida la `100.x` de Tailscale.
4. Permite la entrada al puerto 7070 hacia WSL (PowerShell como administrador, una sola vez):

   ```powershell
   New-NetFirewallHyperVRule -Name "JobRunner" -DisplayName "JobRunner 7070" -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 7070
   ```

### 2. Anotar las direcciones

En cada equipo:

```bash
tailscale ip -4
```

Con la forma B (Tailscale en Windows), corre ese comando en PowerShell; dentro de WSL la misma IP aparece con `hostname -I`.

| Equipo | Ejemplo | Dónde se usa |
|---|---|---|
| Servidor | `100.101.102.103` | `--listen` en el servidor y `--host` en el cliente |
| Cliente | `100.90.80.70` | `--allow` en el servidor |

### 3. Probar la red sin JobRunner

Así se sabe si un problema es de la red o de JobRunner.

En el servidor (con su IP `100.x`):

```bash
python3 -m http.server 7070 --bind 100.101.102.103
```

En el cliente:

```bash
curl -s http://100.101.102.103:7070/ | head -3
```

Si aparece HTML, la red funciona. Detén el servidor de prueba con Ctrl+C. Si no hay respuesta, revisa la sección «Si algo falla» antes de seguir.

### 4. Iniciar JobRunner en el servidor

```bash
cd ~/JobRunner
./scripts/run.sh --listen 100.101.102.103:7070 --allow 100.90.80.70/32
```

| Opción | Qué hace |
|---|---|
| `--listen HOST:PUERTO` | Además del socket Unix local, escucha por TCP en esa dirección. Sin `--listen` no se abre ningún puerto. `--listen` sin valor usa `127.0.0.1:7070` |
| `--allow RED` | Red de origen permitida, en notación CIDR. `/32` es una sola IP. Se puede repetir. `127.0.0.1` y `::1` siempre se permiten |

Debe aparecer:

```
JobRunner escuchando en data/jobrunner.sock
JobRunner escuchando en 100.101.102.103:7070 (TCP); origenes permitidos: 127.0.0.1/32,::1/128,100.90.80.70/32
```

Para permitir a todos los equipos de la red de Tailscale se puede usar `--allow 100.64.0.0/10`, pero es más seguro permitir solo la IP del cliente.

### 5. Usar JobRunner desde el cliente

El cliente también necesita una copia del repositorio (`git clone` y `./scripts/setup.sh`, como en la guía de usuario).

```bash
cd ~/JobRunner
export PATH="$PWD/scripts:$PATH"
royito --host 100.101.102.103 --port 7070 submit -- sleep 30
royito --host 100.101.102.103 --port 7070 list
```

Para no repetir `--host` y `--port` en cada comando:

```bash
export JOBRUNNER_HOST=100.101.102.103
export JOBRUNNER_PORT=7070
royito list
```

Los comandos y las respuestas son los mismos que en local, incluidos `royito output <id>` y `royito health`. Si no conecta, `royito` indica a qué `HOST:PUERTO` no pudo llegar.

### 6. Comprobar en la bitácora del servidor

```bash
grep -E "servicio_iniciado|acceso_rechazado|recibido" data/jobrunner.log | tail -5
```

- `servicio_iniciado` muestra `tcp=` y `permitidas=`.
- Una conexión desde una IP que no está en `--allow` aparece como `ERROR acceso_rechazado ip=<dirección>`.

### 7. Terminar

- Servidor: Ctrl+C. Cierra las conexiones, libera el puerto y cancela los trabajos en ejecución (evento `red_cerrada`).
- Para salir de la red de Tailscale: `sudo tailscale down`.

## Alternativa: LAN privada

Si no se puede usar Tailscale, los dos equipos se conectan a la misma red privada (por ejemplo, el punto de acceso de un celular) y se usa la IP privada del servidor (`192.168.x.x` o `10.x.x.x`):

```bash
./scripts/run.sh --listen 192.168.1.20:7070 --allow 192.168.1.30/32
```

- En WSL, la IP de la LAN es la de Windows y no la de WSL. Hace falta el modo `mirrored` (sección 1.2, pasos 2 a 4).
- En esta opción el tráfico no va cifrado. Úsala solo en una red de confianza.

## Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `Error: no se pudo abrir el servicio: [Errno 99] Cannot assign requested address` | La IP de `--listen` no pertenece a este equipo (en WSL sin `mirrored`, la IP de Windows no existe dentro de WSL) | Usa la IP que muestra `tailscale ip -4` en la misma terminal donde corre el servidor |
| `Error: no se pudo abrir el servicio: [Errno 98] Address already in use` | Otro programa usa el puerto (por ejemplo, el `http.server` de prueba) | Detén el otro programa o usa otro puerto |
| `no se puede escuchar en 0.0.0.0: abriria el servicio a cualquier red...` | Se intentó escuchar en todas las interfaces | Usa la IP `100.x` o la IP privada del equipo |
| `red no permitida: ... no es privada` | `--allow` con una red pública | Usa la IP del cliente con `/32` o una red privada |
| `--allow solo tiene efecto con --listen` | Falta `--listen` | Agrega `--listen HOST:PUERTO` |
| El cliente no conecta y `curl` del paso 3 tampoco | Problema de red: Tailscale apagado, cuentas distintas o firewall | `tailscale status` en ambos equipos; en modo `mirrored`, revisa la regla del paso 1.2 |
| El cliente muestra «cerro la conexion sin responder» (o «Connection reset by peer» en un cliente propio) | La IP del cliente no está en `--allow`; en el servidor aparece `acceso_rechazado` | Agrega la IP del cliente con `--allow` y reinicia el servidor |

Más casos en la [guía de diagnóstico](diagnostico.md).
