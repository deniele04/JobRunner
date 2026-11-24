# IA-021 — Correccion de la descripcion de cancel en la guia del protocolo

| Campo | Valor |
|---|---|
| **Fecha** | 23/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 4 - Operacion remota (entrega final) |
| **Artefactos afectados** | docs/technical-guide/protocolo-y-persistencia.md |
| **Clasificacion** | En revision |

## 1. Objetivo

Corregir un error de la guia del protocolo (J7, IA-018): decia que `cancel` devuelve el trabajo ya en estado CANCELED, pero para un trabajo en ejecucion devuelve RUNNING y pasa a CANCELED despues.

## 2. Entrada proporcionada

- La salida real de la prueba entre equipos por VPN (cancel de un trabajo en ejecucion: RUNNING en la respuesta, CANCELED en el status siguiente), `executor.py` (`cancel`) y el ADR-0006.

## 3. Resultado recibido

1. La fila de `cancel` en la tabla de comandos distingue trabajo en cola y trabajo en ejecucion.
2. Una nota «Cancelacion» explica SIGTERM, el escalamiento a SIGKILL a los 5 s, la segunda cancelacion y que el cliente debe confirmar con `status`.

## 4. Revision realizada

- Se comparo el texto con el codigo de `cancel` y con la guia de usuario, que ya describia este comportamiento correctamente.
- El error venia de la guia escrita en IA-018: se habia tomado el resumen del comando sin revisar el caso de un trabajo en ejecucion.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Fila de cancel corregida y nota de cancelacion | Adoptadas | Aceptado |

## 6. Limitaciones del resultado de la IA

- Solo se corrige la guia del protocolo; el comportamiento del servicio no cambia.

## 7. Prueba o verificacion agregada

| Caso | Verificacion | Resultado |
|---|---|---|
| Documentacion | Comparacion con `executor.py`, ADR-0006 y la evidencia de la prueba por VPN | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (23/11/2026)

## 8. Aprendizaje

- Un error de documentacion se descubre al comparar la guia con la salida real de una prueba; conviene contrastar cada afirmacion del protocolo con un caso real antes de darla por buena.
