# ADR-0006: Cancelación sin bloqueo, escalamiento y cierre controlado

**Estado:** Aceptado
**Fecha:** 27/10/2026
**Responsable(s):** Diego Armando Durán Hernández
**Issue relacionado:** #37, #64
**Aprobado en:** PR #46
**Historial:** Propuesto 27/10/2026. Recoge las decisiones 4 y 5 de la minuta del 20/10/2026 (Avance 2). Aceptado (30/10/2026): la cancelación sin bloqueo y el escalamiento se implementaron en el PR #67.

## Contexto

Con el Avance 2 el servicio atiende varios trabajos a la vez (`--max-jobs`) y mantiene una cola (`--queue-size`). Dos comportamientos del código actual (`main`, commit c3e0b08) no son compatibles con eso:

1. **`cancel()` bloquea al servidor.** Envía SIGTERM al grupo de procesos y espera con `proc.wait(timeout=5)`; si el trabajo ignora SIGTERM, escala a SIGKILL. El servidor atiende un cliente a la vez, así que durante ese tiempo no responde a nadie. Medido en `main` con un trabajo que ignora SIGTERM (`trap '' TERM`): `cancel` tardó **5,00 s** y el trabajo terminó con código −9.
2. **`cancel()` no respeta la verdad del trabajo.** Si el proceso ya terminó por sí solo pero nadie lo ha recogido con `poll()`, `cancel` lo marca `CANCELED` conservando `exit_code = 0`. Medido: un `true` terminado con 0 aparece como `CANCELED`. Esto contradice la inmutabilidad de los estados finales.
3. **El servidor no tiene cierre controlado.** Solo captura `KeyboardInterrupt`; no maneja SIGTERM y no hace nada con los trabajos `RUNNING`. Al detenerlo quedan procesos hijos huérfanos ejecutándose sin dueño, y la base de datos (ADR-0002) los seguiría mostrando como `RUNNING`.

Requisitos que obligan a decidir esto (documento de Requisitos Funcionales):
- **RF-10:** cancelar un trabajo en cola o en ejecución y reflejar el resultado.
- **RF-15:** iniciar y detener el servicio de forma controlada, sin aceptar trabajos nuevos durante el cierre.
- **RF-26:** dos cancelaciones concurrentes sobre el mismo trabajo deben dar un estado final coherente y respuestas comprensibles para ambos clientes.
- **RF-29:** si un proceso hijo termina inesperadamente, detectarlo, liberar recursos y registrar un estado terminal con diagnóstico.
- **RF-30:** si un trabajo no termina tras la cancelación normal, aplicar una política de escalamiento documentada y verificable.

Requisitos no funcionales relacionados:
- **RNF-25:** liberar sockets y procesos hijos al cerrar el servicio.
- **RNF-27:** transiciones de estado consistentes ante solicitudes concurrentes, sin combinaciones imposibles ni regresiones de estado.
- **RNF-30:** tras un cierre o falla, no dejar procesos huérfanos bajo responsabilidad del servicio.
- **RNF-33:** las pruebas de estrés deben demostrar liberación de memoria, procesos, archivos y sockets.
- **RNF-34:** toda decisión que afecte consistencia o recuperación incluye análisis de riesgo y prueba asociada (sección Consecuencias).

Además, el documento exige registrar en ADR la «política de cancelación, tiempo de espera y escalamiento». Este es ese ADR.

## Alternativas consideradas

### Cancelación

**A. Mantener `cancel()` bloqueante.**
- A favor: ya existe y está probado (TC-005); no cambia nada.
- En contra: el servidor queda congelado hasta 5 s por cada cancelación; con varios trabajos concurrentes, una cancelación retrasa `status`, `list` y `submit` de todos.

**B. Un hilo por cancelación que haga la espera y el escalamiento.**
- A favor: el servidor sigue respondiendo.
- En contra: introduce concurrencia sobre `_jobs`/`_procs` (candados, condiciones de carrera) y rompe la simplicidad de un solo hilo elegida en ADR-0001; difícil de probar de forma determinista.

**C. Cancelación sin bloqueo; el ciclo del servidor aplica el escalamiento.**
- A favor: sin hilos nuevos; reutiliza el ciclo de 0,5 s que ya revisa procesos (ADR-0004); el estado se modifica en un único lugar; se prueba con un reloj controlable.
- En contra: el SIGKILL puede llegar hasta 0,5 s después de los 5 s; el estado `RUNNING` se mantiene un instante tras pedir la cancelación.

### Cierre del servicio

**D. No hacer nada (dejar los hijos vivos).**
- A favor: cero código.
- En contra: procesos huérfanos, estado inconsistente, socket obsoleto que bloquea el siguiente arranque.

**E. Esperar a que terminen los trabajos en ejecución.**
- A favor: no se pierde trabajo.
- En contra: Ctrl+C puede tardar de forma indefinida; el operador no tiene forma de forzar el cierre.

**F. Cancelar los `RUNNING`, conservar los `QUEUED` y limpiar.**
- A favor: cierre acotado en tiempo; sin huérfanos; la cola sobrevive al reinicio y se reanuda según ADR-0005.
- En contra: se pierde el avance de los trabajos que estaban corriendo (quedan `CANCELED`).

## Decisión

Se elige **C** para la cancelación y **F** para el cierre.

**Cancelación (minuta, decisión 4):**

1. Cancelar un trabajo `QUEUED` lo pasa directamente a `CANCELED` (no hay proceso) y lo saca de la cola.
2. Cancelar un trabajo `RUNNING` envía **SIGTERM de inmediato al grupo de procesos** (`os.killpg`) y **regresa sin esperar**. Se registra el instante de la solicitud.
3. El trabajo **permanece `RUNNING`** hasta que el ciclo del servidor recoge su salida; entonces pasa a `CANCELED` con `exit_code` negativo (−15 o −9) y `finished_at`.
4. Si pasan **5 s** desde la solicitud y el proceso sigue vivo, el ciclo del servidor envía **SIGKILL** al grupo.
5. Una **segunda cancelación** sobre un trabajo ya en proceso de cancelación o ya terminado **devuelve su estado real sin modificarlo** ni reenviar señales. Un trabajo que terminó por sí solo antes de ser recogido se recoge primero con su resultado real (`SUCCEEDED`/`FAILED`); nunca se reescribe como `CANCELED`.
6. Cancelar un id inexistente devuelve error sin afectar a otros trabajos.

**Cierre controlado (minuta, decisión 5), al recibir Ctrl+C (SIGINT) o SIGTERM:**

1. Dejar de aceptar solicitudes nuevas.
2. Cancelar los trabajos `RUNNING` con el mismo mecanismo (SIGTERM al grupo, SIGKILL a los 5 s) y esperar su recolección, con ese límite como tope del cierre.
3. **Conservar los `QUEUED`** sin cambiar su estado ni su orden (`created_at`), para el siguiente arranque.
4. Registrar `servicio_detenido` en la bitácora y eliminar el socket Unix.
5. Un segundo Ctrl+C durante el cierre no se ignora: fuerza SIGKILL inmediato a los grupos pendientes.

Razones técnicas:
- Un solo hilo y un único lugar que cambia estados evita condiciones de carrera y facilita la verificación.
- Señalar al **grupo** de procesos (los trabajos se lanzan con `start_new_session=True`) evita dejar nietos huérfanos y permite liberar todos los recursos del trabajo (RF-29, RNF-33).
- Al ejecutarse todo en un solo hilo, dos cancelaciones simultáneas (RF-26) se atienden una tras otra: la primera envía la señal y la segunda recibe el estado real, así que ambos clientes obtienen una respuesta coherente y el estado final es único.
- Conservar `QUEUED` es coherente con ADR-0005: al arrancar, un `RUNNING` residual se marca `FAILED` ("interrumpido por reinicio") y los `QUEUED` vuelven a la cola. Con este cierre, un apagado ordenado casi nunca deja `RUNNING` residuales; solo un fallo duro (kill -9 al servidor, corte de energía) cae en ADR-0005.

## Consecuencias

**Positivas**
- `cancel`, `status`, `list` y `submit` responden en tiempo acotado aunque un trabajo ignore SIGTERM.
- Los estados finales dejan de poder reescribirse.
- Ctrl+C deja el sistema limpio: sin hijos huérfanos y sin socket obsoleto.

**Negativas**
- La respuesta de `cancel` ya no trae `CANCELED` en el acto; el cliente debe consultar `status` (o el CLI debe indicar "cancelación solicitada").
- El SIGKILL puede retrasarse hasta un ciclo (0,5 s) respecto a los 5 s nominales.
- Los trabajos en ejecución al apagar se pierden como `CANCELED`.
- El cierre controlado no cubre una falla dura del servicio (kill -9, corte de energía): ahí los hijos pueden sobrevivir. Para RNF-30 («tras un cierre **o falla**») esa parte la cubre la recuperación al arrancar de ADR-0005, que termina el grupo de procesos residual.

**Riesgos**
- Un trabajo ignora SIGTERM y la cancelación no termina nunca — Mitigación: escalamiento a SIGKILL a los 5 s dentro del ciclo — Prueba: TC-021 (escalamiento de cancelación, RF-30): con un trabajo que ignora SIGTERM, `cancel` regresa en < 1 s y el trabajo termina con −9 en ≤ 6 s.
- Dos solicitudes concurrentes producen una transición imposible o una regresión de estado (RNF-27) — Mitigación: un solo hilo modifica estados y los finales son inmutables — Prueba: TC-017.
- Cancelación en cola y en ejecución no refleja el resultado — Mitigación: reglas 1 a 3 — Prueba: TC-005 (RF-10).
- Doble cancelación concurrente o cancelación de un trabajo ya terminado altera un estado final — Mitigación: regla 5, se recoge antes de decidir — Prueba: TC-017 (cancelaciones concurrentes, RF-26) y TC-005 con cancelación tras terminar con código 0 (estado y `exit_code` no cambian).
- El cierre acepta trabajos nuevos o deja la cola/estados inconsistentes — Mitigación: pasos 1 a 4 del cierre — Prueba: TC-009 (cierre controlado, RF-15, RNF-25).
- El cierre deja procesos huérfanos, recursos sin liberar o el socket obsoleto — Mitigación: pasos 2 y 4 del cierre, `killpg` sobre el grupo — Prueba: TC-009 y TC-024 (liberación de recursos bajo carga, RNF-33).
- Cierre colgado por un trabajo que no muere — Mitigación: tope de 5 s y segundo Ctrl+C forzado — Prueba: TC-009 con un trabajo que ignora SIGTERM.
- Tras una falla dura del servicio quedan hijos vivos (RNF-30) — Mitigación: ADR-0005 envía SIGTERM/SIGKILL al grupo residual en el siguiente arranque y marca `FAILED`; el hijo huérfano vive hasta entonces — Prueba: TC-007 y TC-020 (verificar que tras el reinicio no queda ningún proceso del trabajo anterior). Es un riesgo residual aceptado, no eliminado.
- Un hijo muere por una señal ajena (no por cancelación) y se confunde con una cancelación — Mitigación: solo se marca `CANCELED` si hubo solicitud de cancelación registrada; en otro caso `FAILED` con la señal como diagnóstico — Prueba: TC-020 (terminación inesperada del proceso hijo, RF-29, RNF-30).
- Pérdida de la cola en el cierre — Mitigación: los `QUEUED` no se tocan y ADR-0005 los reencola — Prueba: TC-007 (reinicio y recuperación, RF-12, RF-13).

## Decisiones abiertas

- ¿El límite de 5 s para escalar a SIGKILL debe ser configurable (opción del servicio) o fijo? (también planteada en ADR-0005).
- ¿La respuesta de `cancel` debe incluir un indicador explícito de "cancelación en curso"? Afecta el contrato JSON de ADR-0003 y debe acordarse con Ingeniería.
- ¿Los `QUEUED` cancelados durante el cierre deben ser siempre conservados, o el operador puede pedir descartarlos?

## Requisitos afectados

RF-10, RF-15, RF-26, RF-29, RF-30 y RNF-25, RNF-27, RNF-30, RNF-33, RNF-34. RF-15, RF-29, RNF-25, RNF-30 y RNF-33 son los asignados a Verificación en la minuta del 20/10/2026. Vinculación con TC según el Plan de Verificación: TC-005 (RF-10), TC-009 (RF-15, RNF-25), TC-017 (RF-26, RNF-27), TC-020 (RF-29, RNF-30), TC-021 (RF-30) y TC-024 (RNF-33). Cobertura por TC en la [matriz](../../verif/verification-plan/matriz-trazabilidad.md).

## Evidencia

- Medición previa a la decisión (27/10/2026, `main` c3e0b08): `cancel` bloquea 5,00 s con SIGTERM ignorado y deja `CANCELED` con `exit_code = 0` a un trabajo que ya había terminado solo.
- Pendiente tras implementar: ejecución de `./scripts/test.sh` con evidencia en `verif/results/<run-id>/` para TC-005, TC-009, TC-017, TC-020, TC-021 y TC-024.
