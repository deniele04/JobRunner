# Minuta 2 — Integración de los bloques 1 y 2

| Campo | Valor |
|---|---|
| **Medio** | WhatsApp y Discord |
| **Asistentes** | Diego Armando Durán Hernández, Josué Said Delgadillo Gutiérrez, Juan José Rentería Haro y Daniel Alejandro Huerta Camberos |
| **Redactó** | Daniel Alejandro Huerta Camberos |
| **Minuta anterior** | [Planeación de la entrega final](entrega-final-1-planeacion.md) |

## Objetivo

Revisar lo integrado de los bloques 1 y 2, resolver las decisiones abiertas de la minuta de planeación y acordar lo que falta para la versión candidata.

## Revisión de lo integrado

| Parte | PR | Estado |
|---|---|---|
| ADR-0008 y ADR-0009; actualización de ADR-0003 y ADR-0007 | #85 | Integrado |
| Compatibilidad con Python 3.12 en `ejecutar_pruebas.py` | #86 | Integrado |
| Servidor TCP con `selectors` | #87 | Integrado |
| `request_id` según el ADR-0007 | #89 | Integrado |
| Restricción de acceso (`--allow`) y rechazo de interfaces públicas | #90 | Integrado |
| Versión del protocolo (`v`) | #91 | Integrado |
| Cierre controlado con TCP | #92 | Integrado |
| Minuta de planeación, cronograma, instructivo de conexión, defectos y limitaciones, índice de incidentes y diagnóstico | #100 | Integrado |
| DEF-005 (`procesos.sh` en WSL) | #101 | Integrado |
| TC-011, TC-012 y TC-023 | #102 | Integrado |
| Guía técnica del protocolo v1 y de seguridad | #103 | Integrado |
| Bitácora de red, AI-LOG y cronograma v7 | #108 | Integrado |
| Cliente remoto, `output` y `health` | — | En desarrollo (Juan) |

## Decisiones

| # | Decisión | Detalle |
|---|---|---|
| 1 | Token compartido | No se adopta. El acceso se limita con `--listen`, `--allow` y la VPN (ADR-0008) |
| 2 | Comportamiento de `--allow` | `--allow` reemplaza la lista por defecto: con `--allow`, solo entran las redes indicadas. El código se alinea con el texto del ADR-0008 (PR #102) |
| 3 | Change Request | No se implementa ningún Change Request en `v1.0.0` |
| 4 | Modo de red de WSL | Se decide con la prueba entre equipos por VPN (minuta 3) |
| 5 | Defectos nuevos | DEF-006, DEF-007 y DEF-008 se registran como Issues (#105 a #107): DEF-006 y DEF-007 los corrige Juan con el cliente remoto; DEF-008 queda a cargo de Josué |
| 6 | Numeración de los registros de IA | Cada registro toma el siguiente número libre en el momento de su PR |

## Acuerdos de trabajo

- Antes de abrir un PR se actualiza la rama con `git pull origin main`, y se avisa en la descripción si depende de otro PR.
- Al resolver conflictos en `AI-LOG.md` se conservan las filas de ambos PR, en orden.
- Se mantienen los acuerdos anteriores: rama propia, 3 aprobaciones por PR y `Closes #N`.

## Acciones

| Acción | Responsable |
|---|---|
| Cliente remoto, `output` y `health`, TC-010, TC-013 y TC-015, arquitectura y modelo de estados | Juan José Rentería Haro |
| TC-026, inspecciones de RNF-16, RNF-17, RNF-18 y RNF-34, `verify.sh` final, matriz y plan de verificación final | Diego Armando Durán Hernández |
| Prueba entre equipos por VPN y su evidencia | Josué Said Delgadillo Gutiérrez y Daniel Alejandro Huerta Camberos |
| README, guía de usuario y diagnóstico con los comandos remotos | Daniel Alejandro Huerta Camberos |
