# Cronograma

**Versión:** 8 — entrega final (cierre)
**Responsable del documento:** Daniel Alejandro Huerta Camberos

> **Control de cambios (v7 → v8):** Cierre de la entrega final: Hitos 3, 4 y 5 completados, estado final de los cuatro bloques y de los riesgos 4, 8, 13 y 16. No hubo verificación cruzada; se declara como excepción en las release notes de `v1.0.0`.
>
> **Control de cambios (v6 → v7):** Se actualiza el estado de los bloques con los PR #91, #92 y #101 a #103, y el de los riesgos 14 y 15.
>
> **Control de cambios (v5 → v6):** Se registra la RT-2 como realizada. Los Hitos 3 y 4 se replanifican por bloques según la minuta de planeación de la entrega final y se agrega su plan con el estado de cada parte. Se actualiza el estado de los riesgos 4 y 8, se agregan los riesgos 13 a 17 (red de WSL, exposición del servicio, conflictos de integración, verificación cruzada y bitácora) y las dependencias de la operación remota.
>
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
| RT-2 | Revisión técnica presencial (asistencia obligatoria de todos) | 03/11/2026 | Todos | Realizada |
| Hito 3 | Operación remota privada: protocolo TCP, cliente remoto, restricción LAN/VPN | Bloques 1 y 2 de la minuta de planeación | Josué Said Delgadillo Gutiérrez y Juan José Rentería Haro | Completado |
| Hito 4 | Candidato de entrega: documentación completa, matriz sin huecos, verificación cruzada | Bloques 3 y 4 de la minuta de planeación | Daniel Alejandro Huerta Camberos | Completado con excepciones (sin verificación cruzada; ver release notes de `v1.0.0`) |
| Hito 5 | Aceptación final: versión etiquetada, release notes, resultados finales | 01/12/2026 | Todos | Completado (`v1.0.0`) |

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
| Vie 30/10 | Cola, límite de concurrencia y cancelación sin bloqueo; cierre controlado; casos de integración y robustez en `verify.sh`; matriz de trazabilidad; AI-LOG; ejecución formal y evidencia; release notes y tag `v0.2.0`; **entrega del Avance 2** |
| Sáb 31/10 – Lun 02/11 | Ensayo: cada integrante presenta su parte técnica y su evidencia |
| Mar 03/11 | **RT-2 presencial** |

Por acuerdo de la minuta del 29/10/2026, la integración de la cola, la cancelación sin bloqueo, el cierre controlado y los casos de robustez, junto con la ejecución formal de `verify.sh`, se concentró el 30/10.

## Plan — Hitos 3 y 4 (entrega final)

El trabajo se organiza en cuatro bloques, según la minuta de planeación de la entrega final. Cada bloque se cierra con una minuta. Los responsables de cada acción están en esa minuta y en las Issues del milestone «Entrega final».

| Bloque | Contenido | Estado |
|---|---|---|
| 1 — Base | ADR-0008 y ADR-0009, y actualización de ADR-0003 y ADR-0007 | Integrado (PR #85) |
| | Servidor TCP con `selectors` (`--listen`, varios clientes, mensajes fragmentados, 64 KiB, 30 s de inactividad) | Integrado (PR #87) |
| | `request_id` según el ADR-0007 y compatibilidad con Python 3.12 | Integrado (PR #89 y PR #86) |
| | Cliente remoto (`--host`, `--port` y variables de entorno) | Integrado (PR #110) |
| | Prueba de conexión entre dos equipos con Tailscale e instructivo | Integrado (PR #100 y PR #114) |
| | DEF-005 y plan de verificación para la versión final | Integrado (PR #101 y PR #113) |
| | Issues, cronograma y riesgos | Integrado. No se implementó ningún Change Request |
| 2 — Funciones | Lista de acceso (`--allow`) y rechazo de interfaces públicas | Integrado (PR #90) |
| | Versión del protocolo (`v`) | Integrado (PR #91) |
| | Cierre controlado con TCP | Integrado (PR #92) |
| | Comandos `output` y `health` | Integrado (PR #110) |
| 3 — Casos y documentos | TC-011, TC-012 y TC-023 | Integrado (PR #102) |
| | TC-010, TC-013 y TC-015 | Integrado (PR #110) |
| | TC-026 (RNF-06) e inspecciones de RNF-16, RNF-17, RNF-18 y RNF-34 | Integrado (PR #109) |
| | `verify.sh` final y matriz de trazabilidad completa | Integrado (PR #112) |
| | Guía técnica del protocolo v1 y guía de seguridad | Integrado (PR #103) |
| | Conexión LAN/VPN, defectos y limitaciones, índice de incidentes y diagnóstico | Integrado (PR #100) |
| | Bitácora de red y AI-LOG | Integrado (PR #108) |
| | README y guía de usuario | Integrado (PR #110 y PR #111) |
| 4 — Entrega | Evidencia entre dos equipos | Integrado (PR #114) |
| | Evaluación de la guía (TC-015), ejecución formal, release notes, participación y `v1.0.0` | Integrado con esta versión del cronograma |
| | Verificación cruzada | No realizada (excepción en las release notes) |

## Riesgos identificados

| # | Riesgo | Probabilidad | Impacto | Mitigación | Dueño | Estado |
|---|---|---|---|---|---|---|
| 1 | Tiempo insuficiente para el Avance 2, con más alcance que el Avance 1 | Alta | Alto | Decisiones registradas en ADR al inicio; cada integrante con una parte técnica y una evidencia; reuniones de seguimiento el 26/10 y el 29/10; orden de integración acordado en la minuta del 29/10 | Daniel Alejandro Huerta Camberos | Mitigado |
| 2 | Falla la integración entre ejecutor, servidor, persistencia y bitácora | Media | Alto | PR pequeños integrados en el orden de la minuta del 20/10; piezas nuevas en módulos propios (`store.py`, `bitacora.py`); cada pieza con su prueba antes de integrar | Josué Said Delgadillo Gutiérrez | Mitigado: `test.sh` sobre `main` con todas las piezas integradas |
| 3 | Procesos huérfanos o zombis por mal manejo de señales | Media | Alto | Grupos de procesos (`start_new_session`); revisión de procesos cada 0,5 s (ADR-0004); cierre controlado (ADR-0006); `procesos.sh` para detectarlos | Juan José Rentería Haro | Mitigado: TC-009, TC-020 y TC-024; DEF-004 cerrado |
| 4 | Un integrante no puede explicar código generado con IA durante la revisión | Media | Alto | Revisión cruzada obligatoria en cada PR; registro en `docs/ai-usage/` y AI-LOG; ensayo de defensa individual antes de cada RT | Diego Armando Durán Hernández | En seguimiento: cada integrante explica su módulo, su ADR y sus casos en la demostración final |
| 5 | Entornos de desarrollo distintos (Windows, macOS, Linux) | Media | Medio | Distribución Linux declarada; uso de WSL o VM; verificación formal siempre desde un clon limpio en Linux; clonar el repositorio dentro de la carpeta personal de WSL (`~`) y no en `/mnt/c`, donde el socket Unix no funciona | Diego Armando Durán Hernández | Mitigado: TC-014 desde un clon limpio |
| 6 | Cobertura de pruebas insuficiente antes de cada hito | Media | Alto | Criterios de aceptación ejecutables en cada Issue; `verify.sh` con los casos del Avance 2 corrido antes de cada integración a `main` | Diego Armando Durán Hernández | Mitigado: matriz de trazabilidad del Avance 2 |
| 7 | Disponibilidad limitada de algún integrante | Media | Medio | Redistribuir tareas con al menos 3 días de aviso; ningún módulo con un solo conocedor | Diego Armando Durán Hernández | En seguimiento |
| 8 | El Change Request del cliente llega en un momento de alta carga | Media | Medio | Reservar capacidad en las semanas 9 y 10; análisis de impacto antes de implementar | Daniel Alejandro Huerta Camberos | Cerrado: no se implementó ningún Change Request en `v1.0.0` |
| 9 | El servidor termina ante una desconexión del cliente o un mensaje inválido | Media | Alto | Atrapar los errores de cada conexión; regla de desconexión del ADR-0007; prueba de robustez TC-019 | Josué Said Delgadillo Gutiérrez | Cerrado: INC-001 corregido en el PR #51; TC-019 |
| 10 | Estados incoherentes por solicitudes concurrentes, duplicadas o cancelaciones | Media | Alto | Atención secuencial y transiciones validadas (ADR-0006 y ADR-0007); revisar el estado real antes de cancelar; pruebas TC-017 y TC-018 | Juan José Rentería Haro | Mitigado: TC-017 y TC-018 |
| 11 | Pérdida o corrupción de trabajos al reiniciar o ante una falla | Media | Alto | Transacciones de SQLite; al arrancar, los trabajos interrumpidos se marcan y su grupo de procesos se termina (ADR-0005); pruebas TC-007 y TC-022 | Josué Said Delgadillo Gutiérrez | Mitigado: TC-007 y TC-022 |
| 12 | Pruebas que dependen de tiempos (señales, procesos que terminan rápido) dan resultados distintos entre ejecuciones | Media | Medio | Usar procesos que ignoran SIGTERM cuando la prueba necesita un trabajo vivo; esperas con límite en lugar de pausas fijas; correr `verify.sh` más de una vez antes de la ejecución formal | Diego Armando Durán Hernández | En seguimiento |
| 13 | La red de WSL no es alcanzable desde otro equipo | Media | Alto | Tailscale dentro de WSL o modo de red `mirrored` (ADR-0008); prueba de conexión entre dos equipos sin JobRunner antes de la demostración; instructivo `docs/user-guide/conexion-lan-vpn.md` | Daniel Alejandro Huerta Camberos | Mitigado: Tailscale dentro de WSL; prueba entre dos equipos en `verif/results/20261123-remoto/` (PR #114) |
| 14 | El servicio queda expuesto a una red no autorizada o a Internet | Baja | Alto | El servidor se niega a arrancar con `0.0.0.0`, `::` o direcciones públicas en `--listen` y `--allow`; conexiones de orígenes no permitidos se cierran y se registran (`acceso_rechazado`); no se abren puertos en el router (ADR-0008) | Josué Said Delgadillo Gutiérrez | Mitigado: código (PR #90) y TC-011 (PR #102) |
| 15 | Conflictos de integración por varios PR en paralelo sobre `server.py`, `red.py` y `AI-LOG.md` | Alta | Medio | `git pull origin main` antes de abrir cada PR; declarar en la descripción si un PR depende de otro; integrar en el orden de la minuta; correr `./scripts/test.sh` sobre la combinación antes de aprobar | Daniel Alejandro Huerta Camberos | En seguimiento: conflictos de los PR #87, #89, #90, #91, #92, #102 y #103 resueltos sin pérdida de cambios |
| 16 | Defectos reportados en la verificación cruzada | Media | Alto | Congelar la versión candidata en la minuta 3; cada defecto como Issue `[Defecto] VC-NN` con responsable del módulo; corrección con prueba de regresión o justificación documentada | Diego Armando Durán Hernández | No aplica: no se realizó verificación cruzada (excepción en las release notes) |
| 17 | Muchas conexiones rechazadas llenan la bitácora | Baja | Bajo | El servicio solo escucha en loopback, redes privadas o la VPN; límite de 64 KiB por mensaje y cierre por inactividad (ADR-0009); se documenta como limitación | Josué Said Delgadillo Gutiérrez | Aceptado: limitación documentada en `docs/defectos-y-limitaciones.md` |

## Dependencias conocidas

- Las operaciones del protocolo dependen del daemon y del modelo de trabajo.
- La cancelación y la cola dependen de la ejecución en proceso hijo.
- El script de verificación (`verify.sh`) depende de que el CLI funcione de extremo a extremo.
- El tag `v0.1.0` depende de una verificación formal PASS desde un clon limpio.
- La persistencia del Hito 2 depende de definir el esquema de datos y la política de recuperación (ADR-0002 y ADR-0005).
- La cola, el límite de concurrencia y la cancelación que no espera dependen de la revisión periódica de procesos en el servidor (ADR-0004 y ADR-0006).
- La recuperación y el `request_id` de las solicitudes duplicadas dependen del módulo de persistencia con SQLite (ADR-0005 y ADR-0007).
- Los eventos de la bitácora de cada parte dependen de que `bitacora.py` esté integrado primero.
- La evidencia de concurrencia y recuperación depende de que todas las piezas estén en `main` antes de la ejecución formal del 30/10.
- El tag `v0.2.0` depende de la ejecución formal de `verify.sh` sobre el commit candidato.
- La operación remota del Hito 3 depende de que el protocolo local ya esté versionado y documentado.
- El cliente remoto depende del servidor TCP (PR #87) y de la versión del protocolo (PR #91).
- `health` depende del servidor TCP y del contador de accesos rechazados de la lista de acceso (PR #90).
- TC-010, TC-011, TC-012, TC-013 y TC-023 dependen de que las funciones de red estén integradas.
- La evidencia entre dos equipos depende de la prueba de conexión con Tailscale y del cliente remoto.
- La guía de usuario y el README finales dependen de los comandos del cliente remoto, `output` y `health`.
- El tag `v1.0.0` depende de la ejecución formal final y de la respuesta a la verificación cruzada.
