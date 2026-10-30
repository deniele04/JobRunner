# Cronograma

**Versión:** 5 — actualizado el 30/10/2026
**Responsable del documento:** Daniel Alejandro Huerta Camberos

> **Control de cambios (v4 → v5):** Se registra la entrega del Avance 2 (`v0.2.0`), se actualizan las actividades del 29/10 y del 30/10 según la minuta del 29/10/2026, se agrega el estado de cada riesgo con su evidencia y se agrega el riesgo 12.
>
> **Control de cambios (v3 → v4):** Se registra la fecha real de la RT-1 (08/10/2026), se agrega la RT-2 (03/11/2026), se agrega el plan detallado del Hito 2 según la minuta del 20/10/2026 y se actualiza el registro de riesgos.
>
> **Control de cambios (v2 → v3):** Se actualizan los roles del equipo. Los responsables por actividad se registran en las Issues del GitHub Project y ya no en este documento. Se corrige la referencia de persistencia. Se agrega el riesgo por integración con 3 aprobaciones por PR.

## Hitos principales

| Hito | Descripción | Fecha objetivo | Responsable | Estado |
|---|---|---|---|---|
| Hito 0 | Inicio y línea base: repositorio, roles, riesgos, ADR iniciales | 11/09/2026 | Todos | Completado con acciones pendientes |
| Hito 1 — Avance 1 | Núcleo local: enviar, ID, proceso hijo, estados, consultar, listar, cancelar, código de salida | 02/10/2026 | Todos | Completado |
| RT-1 | Revisión técnica presencial (asistencia obligatoria de todos) | 08/10/2026 | Todos | Realizada |
| Hito 2 — Avance 2 | Concurrencia y persistencia: límite, cancelación robusta, persistencia, recuperación, bitácora | 30/10/2026 | Josué Said Delgadillo Gutiérrez | Completado (`v0.2.0`) |
| RT-2 | Revisión técnica presencial (asistencia obligatoria de todos) | 03/11/2026 | Todos | Pendiente |
| Hito 3 | Operación remota privada: protocolo TCP, cliente remoto, restricción LAN/VPN | 13/11/2026 (tentativa) | Juan José Rentería Haro | Pendiente |
| Hito 4 | Candidato de entrega: documentación completa, matriz sin huecos, verificación cruzada | 20/11/2026 (tentativa) | Daniel Alejandro Huerta Camberos  | Pendiente |
| Hito 5 | Aceptación final: versión etiquetada, release notes, resultados finales | 01/12/2026 | Todos | Pendiente |

## Plan detallado — Hito 1 (del 28/09 al 08/10)

| Día | Actividades |
|---|---|
| Lun 28/09 | Reunión de decisiones y minuta; reestructura del repositorio; plantillas, labels y milestone; creación de Issues |
| Mar 29/09 | Reescritura de ADR-001 a 003; construcción reproducible; daemon con socket Unix; modelo de trabajo y ejecución en proceso hijo; borrador de casos TC y matriz |
| Mié 30/09 | Operaciones del protocolo y validación; recolección de código de salida y cancelación; pruebas unitarias; `verify.sh`; formato y análisis estático; arquitectura y modelo de estados |
| Jue 01/10 | Integración de servidor y executor; CLI; cola con límite; primera ejecución completa de `verify.sh`; registros de uso de IA |
| Vie 02/10 | Corrección de defectos; README final; matriz actualizada; verificación formal desde un clon limpio (TC-014); tag `v0.1.0` y release notes; **entrega del Avance 1** |
| Sáb 03/10 – Mié 07/10 | `main` congelada (solo correcciones); guion del recorrido de una solicitud; ensayo en el que cada integrante explica procesos, señales y códigos de salida |
| Jue 08/10 | **RT-1 presencial** |

## Plan detallado — Hito 2 (del 20/10 al 03/11)

Las tareas de cada integrante y sus fechas están en la minuta del 20/10/2026 y en las Issues del Project.

| Día | Actividades |
|---|---|
| Mar 20/10 | Reunión de planeación y minuta: decisiones técnicas del Avance 2 y reparto del trabajo |
| Mié 21/10 – Jue 22/10 | ADR-0004 a ADR-0007 y actualización del ADR-0002; correcciones del servidor, del CLI y de `cancel`; Issues del Avance 2; cronograma y registro de riesgos |
| Vie 23/10 – Sáb 24/10 | Bitácora de eventos; base de pruebas de integración con TC-001 y TC-004; script para identificar zombis y huérfanos |
| Dom 25/10 – Lun 26/10 | Cola con límite configurable y rechazo con cola llena; persistencia con SQLite; **reunión de seguimiento** |
| Mar 27/10 – Mié 28/10 | Recuperación al arrancar y solicitudes duplicadas; cierre controlado; casos de integración y robustez; incidente INC-001; guías técnica y de usuario |
| Jue 29/10 | Persistencia conectada al ejecutor, recuperación al arrancar y `request_id`; correcciones de DEF-003 e INC-001; ADR-0007, guía de usuario e incidente INC-001; **reunión de seguimiento** |
| Vie 30/10 | Cola, límite de concurrencia y cancelación sin bloqueo; cierre controlado; casos de integración y robustez en `verify.sh`; matriz de trazabilidad; AI-LOG; congelamiento de `main` a las 18:00; ejecución formal y evidencia; release notes y tag `v0.2.0`; **entrega del Avance 2** |
| Sáb 31/10 – Lun 02/11 | Ensayo: cada integrante presenta su parte técnica y su evidencia |
| Mar 03/11 | **RT-2 presencial** |

Por acuerdo de la minuta del 29/10/2026, el congelamiento de `main` pasó del 29/10 al 30/10 a las 18:00, para integrar en ese día la cola, la cancelación sin bloqueo, el cierre controlado y los casos de robustez.

## Riesgos identificados

| # | Riesgo | Probabilidad | Impacto | Mitigación | Dueño | Estado |
|---|---|---|---|---|---|---|
| 1 | Tiempo insuficiente para el Avance 2, con más alcance que el Avance 1 | Alta | Alto | Decisiones registradas en ADR al inicio; cada integrante con una parte técnica y una evidencia; reuniones de seguimiento el 26/10 y el 29/10; congelamiento acordado el 30/10 a las 18:00 | Daniel Alejandro Huerta Camberos | Mitigado |
| 2 | Falla la integración entre ejecutor, servidor, persistencia y bitácora | Media | Alto | PR pequeños integrados en el orden de la minuta del 20/10; piezas nuevas en módulos propios (`store.py`, `bitacora.py`); cada pieza con su prueba antes de integrar | Josué Said Delgadillo Gutiérrez | Mitigado: `test.sh` sobre `main` con todas las piezas integradas |
| 3 | Procesos huérfanos o zombis por mal manejo de señales | Media | Alto | Grupos de procesos (`start_new_session`); revisión de procesos cada 0,5 s (ADR-0004); cierre controlado (ADR-0006); `procesos.sh` para detectarlos | Juan José Rentería Haro | Mitigado: TC-009, TC-020 y TC-024; DEF-004 cerrado |
| 4 | Un integrante no puede explicar código generado con IA durante la revisión | Media | Alto | Revisión cruzada obligatoria en cada PR; registro en `docs/ai-usage/` y AI-LOG; ensayo de defensa individual antes de cada RT | Diego Armando Durán Hernández | En seguimiento: ensayo de la RT-2 el 02/11 |
| 5 | Entornos de desarrollo distintos (Windows, macOS, Linux) | Media | Medio | Distribución Linux declarada; uso de WSL o VM; verificación formal siempre desde un clon limpio en Linux; clonar el repositorio dentro de la carpeta personal de WSL (`~`) y no en `/mnt/c`, donde el socket Unix no funciona | Diego Armando Durán Hernández | Mitigado: TC-014 desde un clon limpio |
| 6 | Cobertura de pruebas insuficiente antes de cada hito | Media | Alto | Criterios de aceptación ejecutables en cada Issue; `verify.sh` con los casos del Avance 2 corrido antes de cada integración a `main` | Diego Armando Durán Hernández | Mitigado: matriz de trazabilidad del Avance 2 |
| 7 | Disponibilidad limitada de algún integrante | Media | Medio | Redistribuir tareas con al menos 3 días de aviso; ningún módulo con un solo conocedor | Diego Armando Durán Hernández | En seguimiento |
| 8 | El Change Request del cliente llega en un momento de alta carga | Media | Medio | Reservar capacidad en las semanas 9 y 10; análisis de impacto antes de implementar | Daniel Alejandro Huerta Camberos | Pendiente (Hito 3) |
| 9 | El servidor termina ante una desconexión del cliente o un mensaje inválido | Media | Alto | Atrapar los errores de cada conexión; regla de desconexión del ADR-0007; prueba de robustez TC-019 | Josué Said Delgadillo Gutiérrez | Cerrado: INC-001 corregido en el PR #51; TC-019 |
| 10 | Estados incoherentes por solicitudes concurrentes, duplicadas o cancelaciones | Media | Alto | Atención secuencial y transiciones validadas (ADR-0006 y ADR-0007); revisar el estado real antes de cancelar; pruebas TC-017 y TC-018 | Juan José Rentería Haro | Mitigado: TC-017 y TC-018 |
| 11 | Pérdida o corrupción de trabajos al reiniciar o ante una falla | Media | Alto | Transacciones de SQLite; al arrancar, los trabajos interrumpidos se marcan y su grupo de procesos se termina (ADR-0005); pruebas TC-007 y TC-022 | Josué Said Delgadillo Gutiérrez | Mitigado: TC-007 y TC-022 |
| 12 | Pruebas que dependen de tiempos (señales, procesos que terminan rápido) dan resultados distintos entre ejecuciones | Media | Medio | Usar procesos que ignoran SIGTERM cuando la prueba necesita un trabajo vivo; esperas con límite en lugar de pausas fijas; correr `verify.sh` más de una vez antes del congelamiento | Diego Armando Durán Hernández | En seguimiento |

## Dependencias conocidas

- Las operaciones del protocolo dependen del daemon y del modelo de trabajo.
- La cancelación y la cola dependen de la ejecución en proceso hijo.
- El script de verificación (`verify.sh`) depende de que el CLI funcione de extremo a extremo.
- El tag `v0.1.0` depende de una verificación formal PASS desde un clon limpio.
- La persistencia del Hito 2 depende de definir el esquema de datos y la política de recuperación (ADR-0002 y ADR-0005).
- La cola, el límite de concurrencia y la cancelación que no espera dependen de la revisión periódica de procesos en el servidor (ADR-0004 y ADR-0006).
- La recuperación y el `request_id` de las solicitudes duplicadas dependen del módulo de persistencia con SQLite (ADR-0005 y ADR-0007).
- Los eventos de la bitácora de cada parte dependen de que `bitacora.py` esté integrado primero.
- La evidencia de concurrencia y recuperación depende de que todas las piezas estén en `main` antes del congelamiento del 30/10 a las 18:00.
- El tag `v0.2.0` depende de la ejecución formal de `verify.sh` sobre el commit congelado.
- La operación remota del Hito 3 depende de que el protocolo local ya esté versionado y documentado.
