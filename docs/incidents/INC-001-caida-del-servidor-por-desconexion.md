# INC-001 — El servidor termina cuando un cliente se desconecta o envía bytes inválidos

| Campo | Valor |
|---|---|
| **Identificador** | INC-001 |
| **Fecha de detección** | 07/10/2026 (reproducido de nuevo el 29/10/2026 sobre `main`, commit `572140d`) |
| **Detectado por** | Daniel Alejandro Huerta Camberos, en la verificación posterior a la entrega del Avance 1 |
| **Severidad** | Alta: el servicio deja de atender a todos los clientes |
| **Requisitos afectados** | RNF-08 (una solicitud inválida o una desconexión no debe terminar el servicio), RF-22, RF-28, RNF-30 |
| **Versiones afectadas** | `v0.1.0` y `main` hasta la integración de la corrección |
| **Corrección** | Josué Said Delgadillo Gutiérrez |
| **Prueba de regresión** | TC-019 (Diego Armando Durán Hernández) |
| **Estado** | Causa identificada y corrección probada localmente; pendiente de integrar en `main` |

## Síntomas

- El proceso del servidor termina con un `Traceback` y deja de responder.
- El socket `data/jobrunner.sock` desaparece, así que cualquier comando del CLI responde: `Error: no se pudo conectar al servidor en data/jobrunner.sock. Esta corriendo ./scripts/run.sh?`
- La bitácora termina en el último evento normal, sin `servicio_detenido`.
- Los trabajos que estaban en ejecución siguen vivos sin dueño (huérfanos adoptados por el proceso 1), y su registro se pierde porque el servidor guardaba los trabajos solo en memoria.

## Cómo reproducirlo

Con el servicio iniciado (`./scripts/run.sh`), desde la raíz del repositorio:

**Caso A: el cliente se va antes de recibir la respuesta.** Es lo que ocurre si el usuario presiona Ctrl+C en el CLI mientras espera, por ejemplo durante un `cancel` que tarda 5 s.

```bash
python3 -c 'import socket; s=socket.socket(socket.AF_UNIX); s.connect("data/jobrunner.sock"); s.sendall(b"{\"cmd\":\"list\"}\n"); s.close()'
```

**Caso B: llegan bytes que no son texto UTF-8 válido.**

```bash
python3 -c 'import socket; s=socket.socket(socket.AF_UNIX); s.connect("data/jobrunner.sock"); s.sendall(b"\xff\xfe\n"); s.close()'
```

Después de cualquiera de los dos: `PYTHONPATH=src python3 -m jobrunner.cli list` ya no puede conectarse.

## Evidencia

Caso A, salida del servidor (29/10/2026):

```
JobRunner escuchando en data/jobrunner.sock
Traceback (most recent call last):
  ...
  File ".../src/jobrunner/server.py", line 95, in serve
    conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
BrokenPipeError: [Errno 32] Broken pipe
```

Caso B, salida del servidor:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte
```

Bitácora del caso A: termina en el último evento del trabajo, sin `servicio_detenido`:

```
2026-10-29T15:41:15Z INFO servicio_iniciado job=- socket=data/jobrunner.sock
2026-10-29T15:41:16Z INFO recibido job=8bba8103-... programa=sh
2026-10-29T15:41:16Z INFO iniciado job=8bba8103-... pid=398
2026-10-29T15:41:16Z INFO terminado job=8bba8103-... estado=FAILED codigo=3
```

Trabajo huérfano después de la caída (`ps`): `sleep 120` con PPID 1.

## Hipótesis

1. El servidor no atrapa los errores que ocurren al **enviar** la respuesta, solo los de la lectura y los del procesamiento de la solicitud.
2. El servidor solo atrapa `json.JSONDecodeError` al convertir la solicitud, pero los bytes inválidos fallan antes, al decodificar el texto.
3. Cualquier excepción no atrapada dentro del ciclo de conexiones sale de `serve()`, que cierra el socket y termina el proceso.

Se contrastaron reproduciendo cada caso por separado (casos A y B) y leyendo la línea exacta del `Traceback`. Las tres se confirmaron.

## Causa

En `serve()` (`src/jobrunner/server.py`), el manejo de cada conexión tiene tres huecos:

- `conn.sendall(...)` está fuera de cualquier `try`. Si el cliente ya cerró la conexión, el sistema operativo responde con `EPIPE` y Python lanza `BrokenPipeError`.
- `data.decode("utf-8")` lanza `UnicodeDecodeError`, que no es `json.JSONDecodeError`, así que el `except` existente no lo atrapa.
- La lectura solo atrapa `socket.timeout`; otros errores de conexión (por ejemplo, un reinicio de la conexión) también terminarían el servidor.

En los tres casos la excepción sale del `while True`, el bloque `finally` cierra y borra el socket, y el proceso termina.

## Corrección

Cambio en `src/jobrunner/server.py`, probado localmente sobre `main` el 29/10/2026:

```diff
-                except socket.timeout:
+                except OSError:
                     continue
 ...
-                except json.JSONDecodeError:
+                except ValueError:
                     response = {"error": "JSON invalido"}
 ...
-                conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
+                try:
+                    conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
+                except OSError:
+                    bitacora.error("respuesta_no_entregada", motivo="el cliente se desconecto")
```

- `OSError` incluye `socket.timeout` y los demás errores de conexión.
- `ValueError` incluye `json.JSONDecodeError` y `UnicodeDecodeError`.
- Una respuesta que no se pudo entregar ya no termina el servidor; queda registrada en la bitácora. La solicitud se aplicó de todos modos, como define el ADR-0007.

Resultado con la corrección: en el caso A el servidor sigue vivo y registra `ERROR respuesta_no_entregada`; en el caso B responde `{"error": "JSON invalido"}`; un `list` posterior responde normalmente. Las 17 pruebas unitarias siguen en `PASS`.

## Prueba de regresión

**TC-019 — Desconexión durante una solicitud** (RF-28, RF-22, RNF-08), automatizada en las pruebas de integración:

1. Iniciar el servidor.
2. Enviar `{"cmd":"list"}` y cerrar la conexión sin leer la respuesta.
3. Enviar bytes no UTF-8 (`\xff\xfe`) y leer la respuesta.
4. Ejecutar `list` desde el CLI.

**Resultado esperado:** el servidor sigue vivo; el paso 3 responde `{"error": "JSON invalido"}`; el paso 4 responde con la lista de trabajos; la bitácora contiene `respuesta_no_entregada` y `solicitud_invalida`.

## Aprendizaje

- Las pruebas unitarias del ejecutor no detectaban este fallo porque no levantan el servidor. Hacía falta una prueba de robustez con el servidor real y clientes que se comportan mal.
- Cada `try` debe atrapar la familia de errores correcta (`OSError`, `ValueError`), no solo un caso particular.
