# AI-LOG — Registro de uso de IA

Índice de los usos de inteligencia artificial en el proyecto JobRunner. Cada fila enlaza a su registro completo en esta carpeta, que explica qué se pidió, qué respondió la IA, qué revisó el equipo, qué se aceptó, modificó o rechazó, y cómo se verificó.

**Herramienta usada en todos los registros:** Claude.

## Registros

La columna «Revisado en» indica el Pull Request en que el equipo revisó y aprobó el registro junto con el trabajo que describe (3 aprobaciones por PR).

| Registro | Fecha | Usado por | Tema | Hito | Revisado en |
|---|---|---|---|---|---|
| [IA-001](IA-001-organizacion-issues.md) | 28/09/2026 | Daniel Alejandro Huerta Camberos | Organización del Avance 1 en Issues | 1 | PR #21 |
| [IA-002](IA-002-adr-documentacion-servidor-cli.md) | 02/10/2026 | Josué Said Delgadillo Gutiérrez | Corrección de ADR, documentación técnica y servidor + CLI | 1 | PR #14 y PR #32 |
| [IA-003](IA-003-correccion-bugs-executor.md) | 02/10/2026 | Josué Said Delgadillo Gutiérrez | Corrección de bugs del ejecutor | 1 | PR #34 |
| [IA-004](IA-004-adr-persistencia-recuperacion.md) | 27/10/2026 | Josué Said Delgadillo Gutiérrez | ADR-0002 (esquema y retención) y ADR-0005 (recuperación) | 2 | PR #44 |
| [IA-005](IA-005-modulo-persistencia-sqlite.md) | 27/10/2026 | Josué Said Delgadillo Gutiérrez | Módulo de persistencia SQLite (`store.py`) | 2 | PR #45 |
| [IA-006](IA-006-robustez-servidor-y-codigo-salida-cli.md) | 29/10/2026 | Josué Said Delgadillo Gutiérrez | Robustez del servidor y código de salida del CLI | 2 | PR #51 |
| [IA-007](IA-007-persistencia-recuperacion-y-request-id.md) | 29/10/2026 | Josué Said Delgadillo Gutiérrez | Persistencia conectada, recuperación al arrancar y `request_id` | 2 | PR #60 |
| [IA-008](IA-008-casos-de-prueba-y-guia-persistencia.md) | 29/10/2026 | Josué Said Delgadillo Gutiérrez | Casos TC-007, TC-018 y TC-022 y guía de protocolo y persistencia | 2 | PR #61 |
| [IA-009](IA-009-casos-desconexion-muerte-subito-estres.md) | 30/10/2026 | Josué Said Delgadillo Gutiérrez | Casos TC-019, TC-020 y TC-024 (desconexión, muerte súbita y estrés) | 2 | PR #68 |
| [IA-010](IA-010-bitacora-documentacion-y-entrega.md) | 30/10/2026 | Daniel Alejandro Huerta Camberos | Bitácora de eventos, ADR-0007, INC-001, guía de usuario y documentación de la entrega | 2 | PR #71 |
| [IA-011](IA-011-adr-red-y-protocolo.md) | 19/11/2026 | Josué Said Delgadillo Gutiérrez | ADR-0008 y ADR-0009 (red y protocolo v1) y actualización de ADR-0003 y ADR-0007 | 3 | PR #85 |
| [IA-012](IA-012-servidor-tcp-con-selectors.md) | 19/11/2026 | Josué Said Delgadillo Gutiérrez | Servidor TCP con varios clientes (selectors, --listen) | 4 | PR #87 |
| [IA-013](IA-013-request-id-segun-adr-0007.md) | 19/11/2026 | Josué Said Delgadillo Gutiérrez | request_id según el ADR-0007 (duplicado, otro comando, largo) | 4 | PR #89 |
| [IA-014](IA-014-restriccion-de-acceso-allow.md) | 19/11/2026 | Josué Said Delgadillo Gutiérrez | Restricción de acceso por red (--allow) y validación de --listen | 4 | PR #90 |
| [IA-015](IA-015-version-del-protocolo.md) | 20/11/2026 | Josué Said Delgadillo Gutiérrez | Versión del protocolo (campo v) | 4 | PR #91 |
| [IA-016](IA-016-cierre-controlado-con-tcp.md) | 21/11/2026 | Josué Said Delgadillo Gutiérrez | Cierre controlado con TCP | 4 | PR #92 |
| [IA-017](IA-017-casos-tc011-tc012-tc023.md) | 21/11/2026 | Josué Said Delgadillo Gutiérrez | Casos TC-011, TC-012 y TC-023 y corrección de `--allow` | 4 | PR #102 |
| [IA-018](IA-018-guia-protocolo-v1-y-seguridad.md) | 22/11/2026 | Josué Said Delgadillo Gutiérrez | Guía técnica del protocolo v1 y de seguridad | 4 | PR #103 |
| [IA-019](IA-019-planeacion-y-documentacion-entrega-final.md) | 23/11/2026 | Daniel Alejandro Huerta Camberos | Planeación de la entrega final, revisión de PR y documentación de usuario, defectos y diagnóstico | 3 y 4 | PR de este registro |

## Resumen por integrante

| Integrante | Registros |
|---|---|
| Daniel Alejandro Huerta Camberos | IA-001, IA-010, IA-019 |
| Josué Said Delgadillo Gutiérrez | IA-002 a IA-009, IA-011 a IA-018 |
| Juan José Rentería Haro | — |
| Diego Armando Durán Hernández | — |

## Cómo agregar un registro

1. Crear `IA-NNN-tema-corto.md` en `docs/ai-usage/`, con el siguiente número libre y el formato de los registros anteriores: objetivo, entrada proporcionada, resultado recibido, revisión realizada, cambios aplicados (aceptado, modificado o rechazado), limitaciones, verificación y aprendizaje.
2. Agregar su fila a la tabla de este índice y al resumen por integrante en el mismo PR.
3. Al aprobar el PR, quien revisa anota su nombre en el campo «Revisado por» del registro.
