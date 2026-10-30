# IA-009 — Casos TC-019, TC-020 y TC-024 (desconexion, muerte subita y estres)

| Campo | Valor |
|---|---|
| **Fecha** | 30/10/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 2 - Concurrencia y persistencia (Avance 2) |
| **Artefactos afectados** | verif/test-cases/TC-019.md, TC-020.md, TC-024.md, verif/integration/helpers_procesos.py, test_tc019_desconexion.py, test_tc020_trabajo_muere.py, test_tc024_estres.py |
| **Clasificacion** | En revision |

## 1. Objetivo

Segun la minuta, Josue debe escribir las pruebas y los casos TC-019 (desconexion), TC-020 (un trabajo que muere de golpe) y TC-024 (muchos trabajos sin dejar procesos). Se uso la IA para disenar las pruebas con el servidor real y redactar los tres documentos.

## 2. Entrada proporcionada

- La minuta, los helpers de integracion, `procesos.sh`, `verify.sh`, el formato de TC-025 y el codigo actual de `server.py` y `executor.py` en `main`.

## 3. Resultado recibido

1. `helpers_procesos.py`: linea base de PID, revision de zombis y huerfanos y conteo de descriptores abiertos.
2. 11 pruebas de integracion repartidas en tres archivos y los tres documentos de caso.

## 4. Revision realizada

- Las pruebas se ejecutaron 10 veces seguidas sin fallos intermitentes.
- Durante la escritura fallaron por errores de la propia prueba (`EAGAIN` por `listen(5)` y una comprobacion de `error` que ignoraba que el trabajo trae `error: null`); se corrigieron en la prueba, sin tocar el servidor.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Pruebas y documentos de TC-019, TC-020 y TC-024 | Adoptados; estado Pendiente hasta la ejecucion formal | Aceptado |
| Reintento de connect ante EAGAIN | Adoptado; el limite listen(5) queda anotado | Aceptado con ajustes |

## 6. Limitaciones del resultado de la IA

- Los codigos RF/RNF estan por confirmar contra el documento de requisitos.
- Las pruebas de zombis y huerfanos dependen de `procesos.sh` y de Linux (`/proc`).
- Diego debe mapear los nuevos nombres de prueba en `verify.sh`.

## 7. Prueba o verificacion agregada

| Caso | Pruebas | Resultado |
|---|---|---|
| TC-019 | test_tc019_desconexion.py (4) | Cumple |
| TC-020 | test_tc020_trabajo_muere.py (5) | Cumple |
| TC-024 | test_tc024_estres.py (2) | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (30/10/2026)

## 8. Aprendizaje

- Un trabajo que termina trae `error: null`, asi que un error del servicio se distingue por tener solo la clave `error`.
- Medir descriptores abiertos detecta fugas que una prueba de estados no ve.
