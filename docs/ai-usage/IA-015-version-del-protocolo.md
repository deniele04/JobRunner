# IA-015 — Version del protocolo (campo v)

| Campo | Valor |
|---|---|
| **Fecha** | 20/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 4 - Operacion remota (entrega final) |
| **Artefactos afectados** | src/jobrunner/server.py, src/jobrunner/red.py, src/jobrunner/cli.py, verif/integration/test_tc023_version_protocolo.py y ajustes de aserciones en pruebas existentes |
| **Clasificacion** | En revision |

## 1. Objetivo

Implementar la tarea J4 segun ADR-0009 (regla 1): que toda respuesta lleve `"v": 1`, que una solicitud sin `v` se tome como version 1 y que una version distinta reciba un error claro. Se uso la IA para el cambio y las pruebas de TC-023.

## 2. Entrada proporcionada

- ADR-0009, `server.py`, `red.py` y `cli.py` con J2 y J3, y las pruebas existentes.

## 3. Resultado recibido

1. `server.py`: `responder` agrega `"v": 1` (primero) a todas las respuestas, revisa la version antes que el comando y rechaza solicitudes que no son un objeto JSON.
2. `red.py`: el aviso de mensaje demasiado grande tambien lleva `v`.
3. `cli.py`: envia `"v": 1`, rechaza un servidor con otra version y calcula el codigo de salida ignorando `v`.
4. 15 pruebas de integracion nuevas (`test_tc023_version_protocolo.py`).

## 4. Revision realizada

- Se ejecutaron las 222 pruebas del proyecto: todas pasan; las nuevas se repitieron sin fallos intermitentes.
- Al agregar `v` fallaron 11 pruebas que comparaban la respuesta exacta o buscaban solo la clave `error`; se ajustaron sus aserciones (sin cambiar nombres de prueba) y se confirmo que el comportamiento no cambio.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| `v` en todas las respuestas y error de version del ADR | Adoptado | Aceptado |
| Estricto: solo el entero 1 es valido (no `"1"`, `1.0` ni `true`) | Adoptado | Aceptado con ajustes |
| Regla del codigo de salida de la CLI: error del servicio = solo `error` y `v` | Adoptada; se avisa a quien mantiene la CLI | Aceptado con ajustes |

## 6. Limitaciones del resultado de la IA

- Un servidor viejo (sin `v`) respondera sin ese campo; la CLI lo acepta.
- No hay politica para una futura `v2` (el ADR-0009 la deja fuera de este hito).

## 7. Prueba o verificacion agregada

| Caso | Pruebas | Resultado |
|---|---|---|
| TC-023 | test_tc023_version_protocolo.py (15) | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (20/11/2026)

## 8. Aprendizaje

- En Python `True == 1` y `1.0 == 1`; para que `v` sea estricto hay que comparar el tipo.
- Agregar un campo a todas las respuestas rompe las pruebas que comparan el diccionario completo: conviene comprobar solo las claves que importan.
