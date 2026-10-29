# IA-006 — Robustez del servidor y codigo de salida del CLI

| Campo | Valor |
|---|---|
| **Fecha** | 29/10/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 2 - Concurrencia y persistencia (pendientes del Avance 1) |
| **Artefactos afectados** | src/jobrunner/cli.py, src/jobrunner/server.py, verif/unit/test_servidor_robusto.py |
| **Clasificacion** | En revision |

## 1. Objetivo

La minuta del 20/10/2026 lista como pendientes del Avance 1 que el servidor termina si un cliente se desconecta antes de recibir la respuesta o si recibe bytes que no son texto valido (RNF-08), y que el CLI sale con codigo 1 aunque la operacion sea exitosa (#36). Se uso la IA para:

1. Diagnosticar la causa de cada falla leyendo `server.py` y `cli.py`.

2. Proponer la correccion minima de cada una.

3. Escribir las pruebas que la verifican.

## 2. Entrada proporcionada

- El codigo actual de `server.py` y `cli.py` en `main`.

- La minuta del 20/10/2026 con la descripcion de los pendientes.

- El hallazgo previo de Josue: un `submit` exitoso hacia salir al CLI con codigo 1.

## 3. Resultado recibido

1. `cli.py`: `print_response` solo sale con codigo 1 cuando la respuesta contiene unicamente la clave `error` (`list(response) == ["error"]`). Antes bastaba que existiera la clave, y todo trabajo la trae (con valor `null` si no hubo error).

2. `server.py`: la decodificacion UTF-8 invalida se trata como JSON invalido (`UnicodeDecodeError`), y el envio de la respuesta se protege contra `BrokenPipeError` y `ConnectionResetError`, con un evento en la bitacora.

3. `test_servidor_robusto.py`: 6 pruebas, 2 sobre el servidor real y 4 sobre el codigo de salida.

## 4. Revision realizada

- Josue aplico los tres cambios con comandos `sed` y reviso el `git diff` antes de continuar.

- Josue ejecuto las 33 pruebas (27 anteriores y 6 nuevas) en WSL: todas en OK.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Distinguir error de la operacion de error del trabajo en el CLI | Adoptado; cierra el issue #36 | Aceptado |
| Tratar bytes invalidos como solicitud invalida | Adoptado | Aceptado |
| Proteger el envio de la respuesta ante desconexion del cliente | Adoptado | Aceptado |

## 6. Limitaciones del resultado de la IA

- La IA no ejecuto codigo; todas las pruebas las corrio Josue.

- Una solicitud con JSON valido pero que no es un objeto (por ejemplo una lista) sigue respondiendo "error interno"; no se cambio en este PR.

- El CLI no tiene un tiempo de espera propio si el servidor no responde.

## 7. Prueba o verificacion agregada

| Prueba | Que verifica | Resultado |
|---|---|---|
| test_bytes_que_no_son_texto_valido | El servidor responde con error y sigue vivo | Cumple |
| test_cliente_que_se_desconecta_antes_de_la_respuesta | El servidor sigue vivo tras 5 clientes que cierran sin leer | Cumple |
| test_trabajo_con_error_nulo_no_es_error | Un trabajo con error nulo sale con codigo 0 | Cumple |
| test_trabajo_fallido_sigue_siendo_una_operacion_exitosa | Un trabajo FAILED consultado sale con codigo 0 | Cumple |
| test_listado_no_es_error | list sale con codigo 0 | Cumple |
| test_error_de_operacion_sale_con_1 | Un error real sale con codigo 1 | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (29/10/2026)

## 8. Aprendizaje

- Un campo que siempre existe, aunque sea nulo, no sirve para distinguir un error: hay que mirar el valor o la forma de la respuesta.

- Distinguir el resultado de la operacion (la consulta funciono) del resultado del trabajo (el trabajo fallo) evita marcar como error una consulta correcta.

- Para probar robustez del servidor conviene levantarlo de verdad en un proceso aparte y comprobar despues que sigue respondiendo.
