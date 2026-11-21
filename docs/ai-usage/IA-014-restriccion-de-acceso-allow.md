# IA-014 — Restriccion de acceso por red (--allow)

| Campo | Valor |
|---|---|
| **Fecha** | 19/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 4 - Operacion remota (entrega final) |
| **Artefactos afectados** | src/jobrunner/red.py, src/jobrunner/server.py, verif/unit/test_red.py, verif/integration/test_acceso_tcp.py |
| **Clasificacion** | En revision |

## 1. Objetivo

Implementar la tarea J3 segun ADR-0008: que el servidor solo acepte por TCP a los origenes permitidos (`--allow`, en CIDR) y se niegue a arrancar si se le pide escuchar en `0.0.0.0`, `::` o una direccion publica. Se uso la IA para disenar la validacion y las pruebas.

## 2. Entrada proporcionada

- ADR-0008 (reglas 2 a 5), `red.py` y `server.py` de J2 y las pruebas TCP existentes.

## 3. Resultado recibido

1. `red.py`: `parsear_red`, `redes_permitidas`, `es_permitida` y `validar_escucha`; la clase `Red` cierra sin leer a los origenes no permitidos, registra `acceso_rechazado ip=...` y cuenta los rechazos.
2. `server.py`: opcion `--allow` repetible, validacion al arrancar y registro de los origenes permitidos.
3. 15 pruebas unitarias y 15 de integracion nuevas.

## 4. Revision realizada

- Se ejecutaron las 207 pruebas del proyecto: todas pasan; las pruebas de acceso se repitieron 3 veces sin fallos intermitentes.
- Las pruebas de integracion usan 127.0.0.2 como origen no permitido, asi que no hace falta otra maquina.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Validacion de `--listen` y `--allow` al arrancar | Adoptada | Aceptado |
| El loopback (127.0.0.1 y ::1) siempre esta permitido, ademas de lo que diga `--allow` | Adoptada; se aclara en el ADR-0008 | Aceptado con ajustes |
| `--allow` sin `--listen` es un error de uso | Adoptado | Aceptado |

## 6. Limitaciones del resultado de la IA

- Se filtra por la direccion de origen de la conexion; no hay autenticacion ni cifrado (el token compartido quedo fuera del Hito 3).
- El contador de rechazos existe (`Red.rechazadas`), pero el comando `health` que lo mostraria todavia no esta implementado.
- Las pruebas no pueden comprobar una red privada real (192.168.x o Tailscale); eso se verifica a mano en J8.

## 7. Prueba o verificacion agregada

| Alcance | Pruebas | Resultado |
|---|---|---|
| Validacion y origenes | verif/unit/test_red.py (15 nuevas) | Cumple |
| Servidor con --allow | verif/integration/test_acceso_tcp.py (15) | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (19/11/2026)

## 8. Aprendizaje

- 127.0.0.2 sirve como "otro equipo" para probar el rechazo sin salir de la maquina.
- Rechazar al arrancar es mas seguro que avisar: un `--listen 0.0.0.0` por descuido deja el servicio abierto sin que nadie lo note.
