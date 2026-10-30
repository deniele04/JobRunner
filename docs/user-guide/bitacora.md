# Bitácora de eventos

El servicio registra lo que ocurre en el archivo `data/jobrunner.log`. Sirve para saber qué pasó con cada trabajo y para diagnosticar errores (RF-14).

## Formato

Cada evento ocupa una línea con la fecha y hora en UTC, el nivel (`INFO` o `ERROR`), el tipo de evento y el ID del trabajo:

```
2026-10-25T18:30:00Z INFO recibido job=7076f32d-9147-4047-8a0c-5adcb19f852f programa=sh
2026-10-25T18:30:00Z INFO iniciado job=7076f32d-9147-4047-8a0c-5adcb19f852f pid=2986
2026-10-25T18:30:01Z INFO terminado job=7076f32d-9147-4047-8a0c-5adcb19f852f estado=FAILED codigo=3
```

Cuando el evento no corresponde a un trabajo, aparece `job=-`.

## Eventos

| Evento | Nivel | Cuándo ocurre | Datos |
|---|---|---|---|
| `servicio_iniciado` | INFO | El servicio empieza a escuchar | `socket` |
| `servicio_detenido` | INFO | El servicio se detiene | — |
| `recibido` | INFO | Se acepta un trabajo nuevo | `programa` |
| `en_cola` | INFO | El trabajo espera porque ya se ejecutan `--max-jobs` trabajos | `posicion` |
| `iniciado` | INFO | El trabajo empieza a ejecutarse | `pid` |
| `terminado` | INFO | El trabajo termina por sí solo | `estado`, `codigo` |
| `cancelacion_solicitada` | INFO | Se envió SIGTERM a un trabajo en ejecución | — |
| `escalamiento` | INFO | El trabajo siguió vivo 5 s después de SIGTERM y se envía SIGKILL | `senal` |
| `cancelado` | INFO | El trabajo queda cancelado | `codigo` o `estado_previo` |
| `recuperado` | INFO | Al arrancar, se recupera un trabajo guardado en la base | `estado`, `motivo` |
| `duplicado` | INFO | Llega un `request_id` ya usado; se devuelve el trabajo existente | `request_id` |
| `rechazado` | ERROR | La cola está llena; el trabajo no se registra (`job=-`) | `motivo`, `programa` |
| `no_se_pudo_iniciar` | ERROR | El comando no existe o no se puede ejecutar | `motivo` |
| `solicitud_invalida` | ERROR | Llega un mensaje que no es JSON válido | `motivo` |
| `error_interno` | ERROR | Una solicitud provoca un error inesperado | `motivo` |
| `cliente_desconectado` | ERROR | El cliente cerró la conexión antes de recibir la respuesta | `motivo` |

## Consultar la bitácora

```bash
cat data/jobrunner.log                    # toda la bitácora
tail -f data/jobrunner.log                # ver los eventos en vivo
grep "job=<id>" data/jobrunner.log        # todo lo que le pasó a un trabajo
grep " ERROR " data/jobrunner.log         # solo los errores
```

## Qué no se registra

La bitácora guarda solo el nombre del programa de cada trabajo (por ejemplo `programa=sh`), nunca sus argumentos, su salida ni las variables de entorno, para no exponer datos sensibles (RNF-15). La salida de cada trabajo sigue en `data/<id>.out` y `data/<id>.err`.
