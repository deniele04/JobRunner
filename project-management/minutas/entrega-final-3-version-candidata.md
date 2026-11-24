# Minuta 3 — Versión candidata

| Campo | Valor |
|---|---|
| **Medio** | WhatsApp y Discord |
| **Asistentes** | Diego Armando Durán Hernández, Josué Said Delgadillo Gutiérrez, Juan José Rentería Haro y Daniel Alejandro Huerta Camberos |
| **Redactó** | Daniel Alejandro Huerta Camberos |
| **Minuta anterior** | [Minuta 2](entrega-final-2-integracion.md) |

## Objetivo

Revisar los bloques 3 y 4, decidir cómo se cierran los puntos que no se pueden cumplir como estaban planeados y congelar la versión candidata para la ejecución formal.

## Revisión de lo integrado

| Parte | PR | Estado |
|---|---|---|
| TC-026 (500 registros) e inspecciones de RNF-16, RNF-17, RNF-18 y RNF-34 | #109 | Integrado |
| Cliente remoto, `output` y `health`; TC-010, TC-013 y TC-015; arquitectura; DEF-006 y DEF-007 cerrados | #110 | Integrado |
| README, guía de usuario y diagnóstico de la versión final | #111 | Integrado |
| `verify.sh` final y matriz sin requisitos sin caso | #112 | Integrado |
| Plan de verificación final | #113 | Integrado |
| Evidencia de la prueba entre equipos por VPN (Josué, servidor; Daniel, cliente): P1, P2, P3, P5 y P6 en PASS; P4 no aplica por haber un solo cliente | #114 | Integrado |
| Corrección de la descripción de `cancel` en la guía del protocolo | #115 | Integrado |
| Carpeta y plantilla de la revisión cruzada | #116 | Integrado |
| DEF-008: un solo servicio por carpeta de datos (candado `jobrunner.lock`) | #117 | Integrado |
| Revisor y guía de la evidencia entre dos equipos | #122 | Integrado |

## Decisiones

| # | Decisión | Detalle |
|---|---|---|
| 1 | Modo de red de WSL | Tailscale instalado dentro de WSL. Funcionó en la prueba entre equipos (`verif/results/20261123-remoto/configuracion.txt`) |
| 2 | Verificación cruzada | No se realiza con otro equipo en `v1.0.0`. Se declara como excepción en las release notes y en `docs/defectos-y-limitaciones.md`; la versión se respalda con la ejecución formal, la prueba entre equipos y la evaluación de la guía |
| 3 | Evaluación de la guía de usuario (TC-015, RNF-23) | La hace un integrante que no participó en la guía de usuario ni en el README, sin ayuda de los demás, y la registra en `verif/manual/TC-015.md`. Se declara en las release notes que no fue una persona externa |
| 4 | DEF-008 | Se corrige antes de la ejecución formal (PR #117), para que la corrección y su prueba de regresión entren en la evidencia final |
| 5 | Versión candidata | Es el commit de `main` después de integrar el registro de TC-015. Sobre ese commit se hace la ejecución formal en WSL |

## Acciones

| Acción | Responsable |
|---|---|
| Evaluación de la guía de usuario y registro en `verif/manual/TC-015.md` | Integrante que no escribió la guía ni el README |
| Ejecución formal de `verify.sh` en WSL sobre la versión candidata | Diego Armando Durán Hernández |
| Release notes `v1.0.0`, participación, cronograma final, tag `v1.0.0` y Release | Daniel Alejandro Huerta Camberos |
| Ensayo de la demostración final | Todos |
