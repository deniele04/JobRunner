# AI-LOG — Registro de uso de IA

Índice de los usos de inteligencia artificial en el proyecto JobRunner. Cada fila enlaza a su registro completo en esta carpeta, que explica qué se pidió, qué respondió la IA, qué revisó el equipo, qué se aceptó, modificó o rechazó, y cómo se verificó.

**Herramienta usada en todos los registros:** Claude.

## Registros

| Registro | Fecha | Usado por | Tema | Hito |
|---|---|---|---|---|
| [IA-001](IA-001-organizacion-issues.md) | 28/09/2026 | Daniel Alejandro Huerta Camberos | Organización del Avance 1 en Issues | 1 |
| [IA-002](IA-002-adr-documentacion-servidor-cli.md) | 02/10/2026 | Josué Said Delgadillo Gutiérrez | Corrección de ADR, documentación técnica y servidor + CLI | 1 |
| [IA-003](IA-003-correccion-bugs-executor.md) | 02/10/2026 | Josué Said Delgadillo Gutiérrez | Corrección de bugs del ejecutor | 1 |
| [IA-004](IA-004-adr-persistencia-recuperacion.md) | 27/10/2026 | Josué Said Delgadillo Gutiérrez | ADR-0002 (esquema y retención) y ADR-0005 (recuperación) | 2 |
| [IA-005](IA-005-modulo-persistencia-sqlite.md) | 27/10/2026 | Josué Said Delgadillo Gutiérrez | Módulo de persistencia SQLite (`store.py`) | 2 |
| [IA-006](IA-006-robustez-servidor-y-codigo-salida-cli.md) | 29/10/2026 | Josué Said Delgadillo Gutiérrez | Robustez del servidor y código de salida del CLI | 2 |
| [IA-007](IA-007-persistencia-recuperacion-y-request-id.md) | 29/10/2026 | Josué Said Delgadillo Gutiérrez | Persistencia conectada, recuperación al arrancar y `request_id` | 2 |
| [IA-008](IA-008-casos-de-prueba-y-guia-persistencia.md) | 29/10/2026 | Josué Said Delgadillo Gutiérrez | Casos TC-007, TC-018 y TC-022 y guía de protocolo y persistencia | 2 |
| [IA-009](IA-009-casos-desconexion-muerte-subito-estres.md) | 30/10/2026 | Josué Said Delgadillo Gutiérrez | Casos TC-019, TC-020 y TC-024 (desconexión, muerte súbita y estrés) | 2 |
| [IA-010](IA-010-bitacora-documentacion-y-entrega.md) | 30/10/2026 | Daniel Alejandro Huerta Camberos | Bitácora de eventos, ADR-0007, INC-001, guía de usuario y documentación de la entrega | 2 |

## Cómo agregar un registro

1. Crear `IA-NNN-tema-corto.md` en `docs/ai-usage/`, con el siguiente número libre y el formato de los registros anteriores: objetivo, entrada proporcionada, resultado recibido, revisión realizada, cambios aplicados (aceptado, modificado o rechazado), limitaciones, verificación y aprendizaje.
2. Agregar su fila a la tabla de este índice en el mismo PR.
