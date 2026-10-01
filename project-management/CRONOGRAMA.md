# Cronograma

**Versión:** 2 — actualizado el 28/09/2026
**Responsable del documento:** Daniel Alejandro Huerta Camberos

> **Control de cambios (v1 → v2):** La implementación del núcleo se adelanta a la semana del 28/09, porque en el Avance 1 se exige un núcleo local ejecutable. La resolución de los primeros 3 ADR también pasa a esta semana. Se prepara todo para la Revisión Técnica 1 (06/10) y se reorganizan los hitos según el documento propuesto.

## Hitos principales

| Hito | Descripción | Fecha objetivo | Responsable | Estado |
|---|---|---|---|---|
| Hito 0 | Inicio y línea base: repositorio, roles, riesgos, ADR iniciales | 11/09/2026 | Todos | Completado con acciones pendientes |
| Hito 1 — Avance 1 | Núcleo local: enviar, ID, proceso hijo, estados, consultar, listar, cancelar, código de salida | 02/10/2026 | Todos | En progreso |
| RT-1 | Revisión técnica presencial (asistencia obligatoria de todos) | 06/10/2026 | Todos | Pendiente |
| Hito 2 — Avance 2 | Concurrencia y persistencia: límite, cancelación robusta, persistencia, recuperación, bitácora | 30/10/2026 | Josué Said Delgadillo Gutiérrez | Pendiente |
| Hito 3 | Operación remota privada: protocolo TCP, cliente remoto, restricción LAN/VPN | 13/11/2026 (tentativa) | Juan José Rentería Haro | Pendiente |
| Hito 4 | Candidato de entrega: documentación completa, matriz sin huecos, verificación cruzada | 20/11/2026 (tentativa) | Daniel Alejandro Huerta Camberos  | Pendiente |
| Hito 5 | Aceptación final: versión etiquetada, release notes, resultados finales | 01/12/2026 | Todos | Pendiente |

## Plan detallado — Hito 1 (semana del 28/09 al 06/10)

Los números corresponden a los Issues del milestone "Avance 1 — Núcleo local".

| Día | Actividades |
|---|---|
| Lun 28/09 | Reunión de decisiones y minuta; reestructura del repositorio; plantillas, labels y milestone; creación de Issues |
| Mar 29/09 | Reescritura de ADR-001 a 003; construcción reproducible; daemon con socket Unix; modelo de trabajo y ejecución en proceso hijo; borrador de casos TC y matriz |
| Mié 30/09 | Operaciones del protocolo y validación; recolección de código de salida y cancelación; pruebas unitarias; `verify.sh`; formato y análisis estático; arquitectura y modelo de estados |
| Jue 01/10 | Integración de servidor y executor; CLI; cola con límite; primera ejecución completa de `verify.sh`; registros de uso de IA |
| Vie 02/10 | Corrección de defectos; README final; matriz actualizada; verificación formal desde un clon limpio (TC-014); tag `v0.1.0` y release notes; **entrega del Avance 1** |
| Sáb 03/10 – Lun 05/10 | `main` congelada (solo correcciones); guion del recorrido de una solicitud; ensayo en el que cada integrante explica procesos, señales y códigos de salida |
| Mar 06/10 | **RT-1 presencial** |

## Riesgos identificados

| # | Riesgo | Probabilidad | Impacto | Mitigación | Dueño |
|---|---|---|---|---|---|
| 1 | Tiempo insuficiente para el Avance 1 (4 días hábiles) | Alta | Alto | Alcance mínimo fijo; Issues de prioridad media recortables (cola, análisis estático) y documentados como limitación | Daniel Alejandro Huerta Camberos |
| 2 | Falla la integración entre servidor y executor el jueves | Media | Alto | Interfaz entre módulos acordada el lunes; executor probado con pruebas unitarias antes de integrar | Josué Said Delgadillo Gutiérrez |
| 3 | Procesos huérfanos o zombis por mal manejo de señales | Media | Alto | Grupos de procesos (`start_new_session`), `waitpid` sistemático y prueba de cancelación en `verify.sh` | Josué Said Delgadillo Gutiérrez |
| 4 | Un integrante no puede explicar código generado con IA durante la revisión | Media | Alto | Revisión cruzada obligatoria en cada PR; registro en `docs/ai-usage/`; ensayo de defensa individual antes de cada RT | Diego Armando Durán Hernández |
| 5 | Entornos de desarrollo distintos (Windows, macOS, Linux) | Media | Medio | Distribución Linux declarada; uso de WSL o VM; verificación formal siempre desde un clon limpio en Linux | Diego Armando Durán Hernández |
| 6 | Cobertura de pruebas insuficiente antes de cada hito | Media | Alto | Criterios de aceptación ejecutables en cada Issue; `verify.sh` corrido antes de cada integración a `main` | Juan José Rentería Haro |
| 7 | Disponibilidad limitada de algún integrante | Media | Medio | Redistribuir tareas con al menos 3 días de aviso; ningún módulo con un solo conocedor | Diego Armando Durán Hernández |
| 8 | El Change Request del cliente llega en un momento de alta carga | Media | Medio | Reservar capacidad en las semanas 9 y 10; análisis de impacto antes de implementar | Daniel Alejandro Huerta Camberos |

## Dependencias conocidas

- Las operaciones del protocolo dependen del daemon y del modelo de trabajo.
- La cancelación y la cola dependen de la ejecución en proceso hijo.
- El script de verificación (`verify.sh`) depende de que el CLI funcione de extremo a extremo.
- El tag `v0.1.0` depende de una verificación formal PASS desde un clon limpio.
- La persistencia del Hito 2 depende de definir el esquema de datos y la política de recuperación (decisiones abiertas de ADR-002).
- La operación remota del Hito 3 depende de que el protocolo local ya esté versionado y documentado.
