# Bitácora de eventos

El servicio registra lo que ocurre en el archivo `data/jobrunner.log`. Sirve para saber qué pasó con cada trabajo, quién intentó conectarse y para diagnosticar errores (RF-14). El código está en `src/jobrunner/bitacora.py`.

## Formato

Cada evento ocupa una línea con la fecha y hora en UTC, el nivel (`INFO` o `ERROR`), el tipo de evento, el ID del trabajo y sus datos:

```
2026-10-25T18:30:00Z INFO recibido job=7076f32d-9147-4047-8a0c-5adcb19f852f programa=sh
2026-10-25T18:30:00Z INFO iniciado job=7076f32d-9147-4047-8a0c-5adcb19f852f pid=2986
2026-10-25T18:30:01Z INFO terminado job=7076f32d-9147-4047-8a0c-5adcb19f852f estado=FAILED codigo=3
2026-11-22T15:49:21Z ERROR acceso_rechazado job=- ip=127.0.0.2
```

Cuando el evento no corresponde a un trabajo, aparece `job=-`.

## Eventos del servicio y de los trabajos

| Evento | Nivel | Cuándo ocurre | Datos |
|---|---|---|---|
| `servicio_iniciado` | INFO | El servicio empieza a escuchar | `socket`; con `--listen`, también `tcp` (dirección y puerto) y `permitidas` (redes de origen) |
| `recibido` | INFO | Se acepta un trabajo nuevo | `programa` |
| `en_cola` | INFO | El trabajo espera porque ya se ejecutan `--max-jobs` trabajos | `posicion` |
| `iniciado` | INFO | El trabajo empieza a ejecutarse | `pid` |
| `terminado` | INFO | El trabajo termina por sí solo | `estado`, `codigo` |
| `cancelacion_solicitada` | INFO | Se envió SIGTERM a un trabajo en ejecución | — |
| `escalamiento` | INFO | El trabajo siguió vivo 5 s después de SIGTERM y se envía SIGKILL | `senal` |
| `cancelado` | INFO | El trabajo queda cancelado | `codigo` o `estado_previo` |
| `recuperado` | INFO | Al arrancar, se recupera un trabajo guardado en la base | `estado`, `motivo` |
| `duplicado` | INFO | Llega un `request_id` ya usado con el mismo comando; se devuelve el trabajo existente | `request_id` |
| `red_cerrada` | INFO | Primer paso del cierre controlado: se dejan de aceptar conexiones, se cierran las abiertas y se libera el puerto | `conexiones` (cuántas se cerraron), `tcp` (`-` si no había `--listen`) |
| `servicio_detenido` | INFO | Termina el cierre controlado | `cancelados`, `en_cola` |
| `request_id_en_uso` | ERROR | Llega un `request_id` ya usado con **otro** comando; se rechaza y no se crea trabajo | `request_id` (el `job` es el del trabajo que ya lo tiene) |
| `rechazado` | ERROR | La cola está llena; el trabajo no se registra (`job=-`) | `motivo`, `programa` |
| `no_se_pudo_iniciar` | ERROR | El comando no existe o no se puede ejecutar | `motivo` |
| `cierre_incompleto` | ERROR | Al cerrar, quedaron procesos que no terminaron a tiempo | `motivo`, `pendientes` |
| `error_interno` | ERROR | Una solicitud o una conexión provoca un error inesperado | `motivo` |

## Eventos de conexión y de red

| Evento | Nivel | Cuándo ocurre | Datos |
|---|---|---|---|
| `acceso_rechazado` | ERROR | Una conexión TCP llega desde una dirección que no está permitida (`--allow`); se cierra sin leer nada (ADR-0008) | `ip` |
| `conexion_inactiva` | INFO | Una conexión pasó 30 s sin enviar datos y se cierra (ADR-0009) | `motivo`, `origen` |
| `cliente_desconectado` | ERROR | El cliente cerró la conexión antes de recibir la respuesta | `motivo` |
| `solicitud_invalida` | ERROR | Llega un mensaje que no se puede atender | `motivo` (tabla siguiente) |

`origen` es la IP del cliente en TCP, o `unix` en el socket local.

### Motivos de `solicitud_invalida`

| `motivo` | Qué pasó | Qué recibe el cliente |
|---|---|---|
| `JSON invalido` | El mensaje no es JSON o no es texto UTF-8 | `{"v": 1, "error": "JSON invalido"}` |
| `la solicitud no es un objeto JSON` | Es JSON, pero no un objeto (por ejemplo, una lista) | `{"v": 1, "error": "la solicitud debe ser un objeto JSON"}` |
| `version de protocolo no soportada` | El campo `v` no es `1`; el dato `version` muestra lo que llegó | `{"v": 1, "error": "version de protocolo no soportada: 2 (soportada: 1)"}` |
| `mensaje demasiado grande` | El mensaje superó 64 KiB sin salto de línea; incluye `maximo` y `origen` | El error y la conexión se cierra |
| `solicitud incompleta` | El cliente cerró la conexión con un mensaje sin salto de línea; no se ejecuta nada | Nada: el cliente ya se fue |

## Consultar la bitácora

```bash
cat data/jobrunner.log                         # toda la bitácora
tail -f data/jobrunner.log                     # ver los eventos en vivo
grep "job=<id>" data/jobrunner.log             # todo lo que le pasó a un trabajo
grep " ERROR " data/jobrunner.log              # solo los errores
grep acceso_rechazado data/jobrunner.log       # intentos de conexión no autorizados
grep -E "servicio_iniciado|red_cerrada|servicio_detenido" data/jobrunner.log   # arranques y cierres
```

## Qué no se registra

La bitácora guarda solo el nombre del programa de cada trabajo (por ejemplo `programa=sh`), nunca sus argumentos, su salida ni las variables de entorno, para no exponer datos sensibles (RNF-15). La salida de cada trabajo sigue en `data/<id>.out` y `data/<id>.err`.

Tampoco se registra el contenido de los mensajes rechazados: de una conexión no autorizada solo se guarda la IP.
