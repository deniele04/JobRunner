# IA-001 — Organización del Avance 1 en Issues

| Campo | Valor |
|---|---|
| **Fecha** | 28/09/2026 |
| **Herramienta** | Claude |
| **Usado por** | Daniel Alejandro Huerta Camberos |
| **Revisado por** | Juan José Rentería Haro |
| **Hito** | Hito 1 — Núcleo local (Avance 1) |
| **Artefactos afectados** | Issues |
| **Clasificación** | Terminado |

## 1. Objetivo

El equipo no tenía claro por dónde empezar el Avance 1 y traducirlo a tareas concretas por lo cual se usó la IA para:

1. Obtener un diagnóstico del repositorio frente a lo que exigen los documentos.
2. Descomponer el Avance 1 en Issues con responsable, requisito asociado y prioridad.
3. Tener un modelo de Issue con criterios de aceptación verificables.

** 2. Entrada proporcionada

- Requisitos funcionales y no funcionales del proyecto.
- El enunciado del Avance 1 (funcionalidad mínima, entregables y dinámica de la RT-1).

Prompts utilizados (textuales):

> 1. "Basado en los documentos y la indiacion proporcionada, danos indicios por dónde iniciar o qué empezar porque no tenemos ni idea qué definir"
> 2. "Centrémonos en los objetivos de hoy y desglósalos"
> 3. "Dame una Issue, por ejemplo, la primera: Daemon acepta conexiones en socket Unix y responde"
> 4. "¿Consideras que esos issues son los necesarios para nuestra entrega de avance 1?"

** 3. Resultado recibido

1. **Plan del día.** Reunión de decisiones, reestructura del repositorio, configuración de GitHub y creación de Issues.
2. **Primera lista de Issues.** 14 Issues repartidos por rol.
3. **Issue de ejemplo** ("Daemon acepta conexiones en socket Unix y responde"), con especificación del protocolo, criterios de aceptación ejecutables como comandos, dependencias y evidencia de cierre.
4. **Segunda lista de Issues (revisada).** 25 Issues agrupados por bloque, con prioridad.


## 4. Revisión realizada

- **Pregunta de verificación:** antes de adoptar la primera lista se le preguntó a la IA si era suficiente. La revisión mostró que estaba incompleta frente al Hito 1: faltaban cola inicial, pruebas unitarias, construcción reproducible, tag con release notes y preparación de la defensa.
- **Contraste con las reglas del profesor:** al recibir el aviso de seguimiento en GitHub, el equipo detectó que la IA había recomendado una rama por Issue y la aprobación de un solo revisor. Ambas cosas se corrigieron.
- **Revisión del equipo:** los cambios a ROLES, cronograma, README y plantillas se integraron en el PR #11, revisado y aprobado por el equipo antes del merge (01/10/2026).
- **Cotejo contra el enunciado del Avance 1:** ver sección 7.

  ## 5. Cambios aplicados

| Resultado de la IA | Decisión del equipo | Clasificación |
|---|---|---|
| Cambiar API REST por socket Unix con JSON por línea, y PostgreSQL por SQLite | Se adoptó tras discutirlo en equipo; registrado en la Issue #8 y en la corrección de ADR-0002/0003 | **Aceptado** |
| Cronograma con responsables y número de Issue por actividad | Se usó como base, pero se quitaron los responsables y los números de Issue: los responsables quedan en las Issues del Project y los números generaban presión y mucha confusión | **Modificado** |
| Lista fija de 25 Issues para todo el Avance 1 | Se descartó: las Issues se crean conforme surge el trabajo, para que correspondan a necesidades reales. | **Rechazado** |

Otros ajustes del equipo:
- Los roles se reasignaron (Verificación: Diego; Ingeniería: Juan José y Josué), distinto al reparto propuesto por la IA.
- Se cambió a una rama por integrante y a 3 aprobaciones por PR.

## 6. Limitaciones del resultado de la IA

- No tuvo acceso certero a las Issues solo a los archivos y commits del repositorio.
- La primera lista de Issues era incompleta.
- Recomendó un flujo de ramas distinto al que después pidió el profesor.
- Propuso fechas tentativas para los Hitos 3 y 4 que deben confirmarse con el profesor.

  ## 7. Prueba o verificación agregada

Como el resultado es organizativo, la verificación es un cotejo de cada entregable del Avance 1 contra la evidencia en el repositorio, realizado el 02/10/2026.

| Entregable del Avance 1 | Evidencia | Estado |
|---|---|---|
| Estructura mínima completa | Carpetas de `docs/`, `project-management/`, `scripts/`, `.github/` | Parcial (falta `verif/`) |
| README con construcción y ejecución | `README.md` | Cumple |
| Arquitectura inicial | Resumen en README; falta `docs/technical-guide/` | Parcial |
| Modelo preliminar de estados | README y minuta del 28/09 | Cumple |
| Issues asociados con el trabajo | Issues #2 a #16 | Cumple |
| Asignación de responsabilidades | `ROLES.md` | Cumple |
| Cronograma actualizado | `CRONOGRAMA.md` v3 | Cumple |
| Al menos tres ADR | ADR-0001 a 0003 | Cumple |
| Primeros casos de prueba | — | Pendiente |
| Script inicial de verificación | `scripts/test.sh`; falta `verify.sh` | Parcial |
| Matriz de trazabilidad | — | Pendiente |
| Registros del uso de IA | Este documento | Cumple |
| Evidencia de la versión demostrada | — | Pendiente |

**Verificó:** [Otro integrante ademas del autor]

## 8. Aprendizaje

- Leer los documentos de requerimientos paso por paso. 
- Una respuesta de la IA que parece completa puede no serlo; preguntar "¿esto cubre todo lo que se pide?" y leer los documentos después reveló los huecos.
- Las reglas del cliente tienen prioridad sobre las sugerencias de la IA, aunque estas parezcan razonables.
- Planear de más también es un riesgo: una lista fija de tareas generó presión innecesaria, y crear Issues conforme surge el trabajo resultó más útil.
