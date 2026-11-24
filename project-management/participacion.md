# Participación del equipo

Resumen de lo que aportó cada integrante a JobRunner, desde el Avance 1 hasta la versión `v1.0.0`. Los números salen del repositorio y de GitHub al cierre de la entrega final; el detalle de cada aporte está en sus Pull Requests, en las Issues y en los registros de uso de IA (`docs/ai-usage/`).

## Roles

| Integrante | Rol | GitHub |
|---|---|---|
| Daniel Alejandro Huerta Camberos | Producto | @deniele04 |
| Josué Said Delgadillo Gutiérrez | Ingeniería | @josuesdg7105 |
| Juan José Rentería Haro | Ingeniería | @JJRNTH |
| Diego Armando Durán Hernández | Verificación | @DiegoDuran07 |

## Números

| Integrante | PR integrados (total) | PR integrados (entrega final) | Aprobaciones dadas a PR de otros | Registros de uso de IA |
|---|---|---|---|---|
| Daniel Alejandro Huerta Camberos | 13 | 4 | 42 | IA-001, IA-010, IA-019 |
| Josué Said Delgadillo Gutiérrez | 21 | 12 | 32 | IA-002 a IA-009, IA-011 a IA-018, IA-020 a IA-022 |
| Juan José Rentería Haro | 7 | 1 | 46 | — |
| Diego Armando Durán Hernández | 14 | 8 | 38 | — |

Cada PR necesitó la aprobación de los otros tres integrantes. Los números de PR no miden el tamaño del trabajo: un PR puede ser un documento corto o un módulo completo.

## Aportes

### Daniel Alejandro Huerta Camberos — Producto

- Gestión: organización en Issues, roles, cronograma y registro de riesgos, minutas, CR-001 y su análisis de impacto, AI-LOG, release notes, y etiquetas y Releases `v0.2.0` y `v1.0.0`.
- Código: módulo de bitácora de eventos (`bitacora.py`).
- Decisiones: ADR-0007 (solicitudes duplicadas y desconexiones) y ajustes a ADR-0002, ADR-0004, ADR-0005 y ADR-0006.
- Incidente INC-001 (caída del servidor por desconexión) y su análisis.
- Documentación de usuario: README, guía de usuario, instructivo de conexión entre equipos, bitácora, guía de diagnóstico, defectos y limitaciones e índice de incidentes.
- Ejecución formal de la verificación del Avance 2 y de la versión final en WSL, y cliente en la prueba entre equipos por VPN.

### Josué Said Delgadillo Gutiérrez — Ingeniería

- Decisiones: ADR-0001 a ADR-0003, ADR-0005, ADR-0008 (red y restricción de acceso) y ADR-0009 (protocolo v1).
- Código: servidor y cliente iniciales, persistencia en SQLite y recuperación al arrancar, `request_id`, robustez del servidor ante desconexiones (corrección de INC-001), servidor TCP con `selectors`, restricción de acceso (`--allow`), versión del protocolo, cierre controlado con TCP y un solo servicio por carpeta de datos (corrección de DEF-008) (`server.py`, `red.py`, `store.py`).
- Casos de prueba: TC-007, TC-011, TC-012, TC-018, TC-019, TC-020, TC-022, TC-023 y TC-024.
- Guía técnica del protocolo v1 y de seguridad (modelo de amenazas).
- Servidor en la prueba entre equipos por VPN y su evidencia.

### Juan José Rentería Haro — Ingeniería

- Decisiones: ADR-0004 (cola, concurrencia y saturación).
- Código: cola y límite de concurrencia (PR #66), cancelación sin bloqueo (PR #67) y revisión periódica de procesos (corrección de DEF-004) en `executor.py`; cliente remoto (`--host`, `--port`), `output` y `health` en `cli.py`, con la corrección de DEF-006 y DEF-007.
- Casos de prueba: TC-005, TC-010, TC-013, TC-015 y TC-017, y las pruebas de la cola (TC-002).
- Guía técnica: arquitectura y modelo de estados de la versión final; guía de usuario con los comandos remotos.

### Diego Armando Durán Hernández — Verificación

- Plan de verificación (Avance 1 y versión final), matriz de trazabilidad y casos de prueba documentados.
- Herramientas: `verify.sh`, `procesos.sh` (zombis y huérfanos), `ejecutar_pruebas.py`, `actualizar_matriz.py` e `inspecciones.py`.
- Corrección de DEF-005 (huérfanos en WSL), TC-026 (500 registros) e inspecciones de RNF-16, RNF-17, RNF-18 y RNF-34.
- Guía de la ejecución final, revisión de la versión candidata (`candidata.sh`), revisor de la evidencia entre dos equipos (`revisar_evidencia_remota.py`) y carpeta de la revisión cruzada.
- Ejecución `20261123` (en Linux, previa a la formal) y matriz de trazabilidad.
