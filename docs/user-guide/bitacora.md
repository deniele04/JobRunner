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
| `servicio_detenido` | INFO | El servicio se detiene con Ctrl+C | — |
| `recibido` | INFO | Se acepta un trabajo nuevo | `programa` |
| `iniciado` | INFO | El trabajo empieza a ejecutarse | `pid` |
| `terminado` | INFO | El trabajo termina por sí solo | `estado`, `codigo` |
| `cancelado` | INFO | El trabajo se cancela | `codigo` o `estado_previo` |
| `no_se_pudo_iniciar` | ERROR | El comando no existe o no se puede ejecutar | `motivo` |
| `solicitud_invalida` | ERROR | Llega un mensaje que no es JSON válido | `motivo` |
| `error_interno` | ERROR | Una solicitud provoca un error inesperado | `motivo` |

## Consultar la bitácora

```bash
cat data/jobrunner.log                    # toda la bitácora
tail -f data/jobrunner.log                # ver los eventos en vivo
grep "job=<id>" data/jobrunner.log        # todo lo que le pasó a un trabajo
grep " ERROR " data/jobrunner.log         # solo los errores
```

## Qué no se registra

La bitácora guarda solo el nombre del programa de cada trabajo (por ejemplo `programa=sh`), nunca sus argumentos, su salida ni las variables de entorno, para no exponer datos sensibles (RNF-15). La salida de cada trabajo sigue en `data/<id>.out` y `data/<id>.err`.
