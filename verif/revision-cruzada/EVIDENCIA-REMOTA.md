# Evidencia de operación entre dos equipos

Respalda TC-010 y RNF-26 (uso remoto solo en localhost, LAN privada o VPN). Se hace entre Verificación (Diego) y Josué, con el servicio en una máquina y el cliente en otra.

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
4. **Rechazo:** desde una tercera dirección no permitida (o con otro `--allow`) intentar conectarse; debe cerrarse sin ejecutar nada y quedar `acceso_rechazado` en la bitácora.
5. **Bitácora:** al terminar, copiar la bitácora del servidor.
6. **Revisar** con el script de arriba y subir la carpeta.

## Archivos que debe tener la carpeta

| Archivo | Contenido |
|---|---|
| `equipo-servidor-bitacora*` | Bitácora del servicio durante la prueba |
| `equipo-cliente-comandos*` | Comandos del cliente y su salida |
| `health*` | Respuesta de `health` |
| `rechazo*` | Intento desde un origen no permitido y su resultado |
| `red*` | Tipo de red (LAN privada o VPN) y direcciones usadas |
| `LEEME*` | Quién, cuándo, hash de la versión probada y resultado |

## Cuidado

- No incluir IP públicas, usuarios, contraseñas ni claves de VPN: el revisor avisa si aparece una IP pública.
- Si WSL queda detrás de NAT, definir con Daniel y Josué el modo de red (Tailscale dentro de WSL o `mirrored`) antes de la prueba; ver la sección 10 del plan.
