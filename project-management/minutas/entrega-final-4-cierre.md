# Minuta 4 — Cierre de la entrega final

| Campo | Valor |
|---|---|
| **Medio** | WhatsApp y Discord |
| **Asistentes** | Diego Armando Durán Hernández, Josué Said Delgadillo Gutiérrez, Juan José Rentería Haro y Daniel Alejandro Huerta Camberos |
| **Redactó** | Daniel Alejandro Huerta Camberos |
| **Minuta anterior** | [Minuta 3](entrega-final-3-version-candidata.md) |

## Objetivo

Revisar la ejecución formal, cerrar la versión `v1.0.0` y preparar la demostración final.

## Resultados

| Punto | Resultado |
|---|---|
| Ejecución formal | `verif/results/<<RUN-ID>>/` sobre el commit `<<COMMIT>>`, en WSL |
| Pruebas | <<N UNITARIAS>> unitarias y <<N INTEGRACIÓN>> de integración en PASS |
| Casos e inspecciones | TC-001 a TC-026 e INS-016, INS-017, INS-018 e INS-034 según el `resumen.md` de la ejecución formal |
| Matriz de trazabilidad | Actualizada con la ejecución formal |
| Operación entre dos equipos | `verif/results/20261123-remoto/` |
| Excepciones | Sin verificación cruzada; TC-015 evaluado por un integrante; ningún Change Request (release notes de `v1.0.0`) |
| Defectos abiertos | DEF-008, aceptado (severidad media) |

## Decisiones

| # | Decisión |
|---|---|
| 1 | Se etiqueta `v1.0.0` sobre `main` después de integrar las release notes y se publica la Release en GitHub |
| 2 | La demostración final sigue el reparto de la minuta de planeación; la parte entre dos equipos se hace con Tailscale como en la prueba registrada |
| 3 | Si la red falla durante la demostración, se muestra la evidencia de `verif/results/20261123-remoto/` |

## Acciones

| Acción | Responsable |
|---|---|
| Tag `v1.0.0` y Release | Daniel Alejandro Huerta Camberos |
| Tailscale encendido y probado en los equipos de la demostración | Quienes hagan la parte entre dos equipos |
| Cada integrante repasa su módulo, su ADR, sus requisitos y sus casos (tabla de defensa de la minuta de planeación) | Todos |
