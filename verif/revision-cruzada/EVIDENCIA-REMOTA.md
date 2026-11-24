# Evidencia de operación entre dos equipos

Respalda TC-010 y RNF-26 (uso remoto solo en localhost, LAN privada o VPN). Se hace entre Josué (servidor) y un cliente de otro equipo, con Verificación (Diego) revisando, con el servicio en una máquina y el cliente en otra.

La evidencia va en `verif/results/<run-id>-remoto/`. Para revisarla:

```bash
python3 verif/scripts/revisar_evidencia_remota.py <run-id>
```

`verify.sh` marca TC-010 como `PASS` solo si esa carpeta existe y las pruebas de Juan pasan.

## Pasos

1. **Servidor** (equipo A): arrancar con la dirección privada o de VPN y permitir solo al cliente.
   `python3 -m jobrunner.server --listen <IP-privada>:<puerto> --allow <IP-del-cliente>`
2. **Cliente** (equipo B): ejecutar `submit`, `status`, `list`, `output` y `cancel` contra esa dirección y guardar la salida completa.
3. **Health:** consultar `health` desde el cliente y guardar la respuesta.
4. **Rechazo:** con una lista `--allow` que no incluya al cliente, intentar conectarse; debe cerrarse sin ejecutar nada y quedar `acceso_rechazado` en la bitácora.
5. **Bitácora:** al terminar, copiar la bitácora del servidor.
6. **Revisar** con el script de arriba y subir la carpeta.

## Archivos que debe tener la carpeta

Cada fila acepta cualquiera de los nombres indicados; los primeros son los de la prueba real.

| Archivo | Contenido |
|---|---|
| `jobrunner.log` (o `*bitacora*`) | Bitácora del servicio durante la prueba; debe incluir un `acceso_rechazado` |
| `prueba-vpn-servidor*` (o `equipo-servidor*`) | Grabación o salida del equipo que corre el servicio |
| `prueba-vpn-cliente*` (o `equipo-cliente*`) | Comandos del cliente y su salida |
| `health*` | Respuesta de `health` desde el cliente |
| `configuracion*` (o `red*`) | Opciones con las que se inició el servicio y la red usada (LAN privada o VPN) |
| `resumen.md` (o `LEEME*`) | Quién, cuándo, commit probado y resultado de cada prueba |

## Evidencia existente

La prueba entre equipos por VPN (Tailscale) de Josué y Daniel está en `verif/results/20261123-remoto/`. El revisor la da por completa:

```bash
python3 verif/scripts/revisar_evidencia_remota.py 20261123
```

`verify.sh` la reconoce por la carpeta `verif/results/*-remoto/` y con ella TC-010 puede quedar en `PASS`. Si la ejecución formal final se hace con otro `<run-id>` y el código cambió después de esa prueba, hay que repetirla.

## Cuidado

- No incluir IP públicas, usuarios, contraseñas ni claves de VPN: el revisor avisa si aparece una IP pública.
- Si WSL queda detrás de NAT, definir con Daniel y Josué el modo de red (Tailscale dentro de WSL o `mirrored`) antes de la prueba; ver la sección 10 del plan.
