# ADR-0004: Cola, límite de concurrencia y saturación

**Estado:** Propuesto
**Fecha:** 29/10/2026
**Responsable(s):** Juan José Rentería Haro
**Issue relacionado:** #por asignar
**Aprobado en:** PR pendiente
**Historial:** Propuesto 29/10/2026. Recoge las decisiones 1, 2 y 3 de la minuta del 20/10/2026 (Avance 2). La cancelación sin bloqueo y el escalamiento que usan este ciclo se deciden en el [ADR-0006](0006-cancelacion-escalamiento-y-cierre-controlado.md).

## Contexto

Hoy `JobManager.submit()` lanza cada trabajo en cuanto llega: no hay límite de procesos simultáneos ni cola. Un cliente que envíe cientos de `submit` puede agotar procesos y memoria del sistema (RNF de saturación), y ningún trabajo aceptado tiene garantía de orden.

Además, el servidor atiende una solicitud a la vez y solo revisa los procesos cuando alguien consulta `status` o `list`. Un trabajo terminado no libera su lugar hasta entonces, y uno en cola nunca arrancaría solo.

Requisitos que obligan a decidir esto: RF-03 (varios trabajos en paralelo), RF-05 (cola de espera), RF-07 (registrar el inicio de cada trabajo), RF-25 (comportamiento ante saturación), RNF-04, RNF-07 y RNF-29.

## Alternativas consideradas

1. **Sin límite (comportamiento actual).**
   - A favor: cero código.
   - En contra: sin protección ante saturación; el orden de arranque depende del sistema operativo.
2. **Límite de concurrencia con cola FIFO acotada; si la cola se llena se rechaza.**
   - A favor: uso de recursos acotado y predecible; orden de arranque justo; el cliente se entera de inmediato si no hay lugar.
   - En contra: el cliente debe reintentar cuando se rechaza.
3. **Límite de concurrencia con cola ilimitada.**
   - A favor: nunca se rechaza una solicitud.
   - En contra: la memoria y la base de datos crecen sin tope; una avalancha de solicitudes degrada todo el servicio.
4. **Bloquear el `submit` hasta que haya lugar.**
   - A favor: el cliente no tiene que reintentar.
   - En contra: el servidor atiende un cliente a la vez; bloquearía a todos los demás.
5. **Un hilo por trabajo (o un hilo supervisor) que gestione la cola.**
   - A favor: el arranque del siguiente trabajo sería inmediato.
   - En contra: introduce concurrencia sobre `_jobs`, `_procs` y la cola (candados y condiciones de carrera) y rompe la simplicidad de un solo hilo del ADR-0001; es difícil de probar de forma determinista.

## Decisión

Se elige la **alternativa 2**.

1. **Cola FIFO.** Los trabajos esperan en orden de llegada y arrancan en ese orden.
2. **Concurrencia configurable.** `--max-jobs` (por defecto 3) es el máximo de trabajos en `RUNNING` a la vez.
3. **Cola acotada.** `--queue-size` (por defecto 10) es el máximo de trabajos en `QUEUED`. Con `max_jobs` ocupados y la cola llena, `submit` se rechaza **de inmediato** con un mensaje de error, se registra el evento `rechazado` en la bitácora y **no se crea ningún trabajo**. Nunca se bloquea ni se pierde un trabajo ya aceptado.
4. **Inicio.** `started_at` se registra cuando el trabajo sale de la cola, no cuando llega.
5. **Ciclo del servidor.** El servidor sigue atendiendo una solicitud a la vez, pero ninguna operación espera: `accept()` tiene un tiempo de espera de 0,5 s y, en cada vuelta del ciclo (por timeout o antes de atender cada solicitud), el servidor llama a `JobManager.tick()`, que, en este orden, (a) recoge con `poll()` los procesos terminados, (b) aplica el escalamiento de cancelación (ADR-0006) y (c) arranca trabajos de la cola mientras haya lugar.
6. **Invariante.** Si la cola no está vacía, hay exactamente `max_jobs` procesos en ejecución. `submit` primero arranca lo que esté esperando, de modo que un trabajo nuevo nunca se salta a los que ya esperan, y el rechazo se decide con una sola condición: no hay lugar para correr **y** la cola está llena.
7. **Cancelar en cola.** Un trabajo `QUEUED` cancelado pasa a `CANCELED`, sale de la cola y libera su lugar.
8. **Recuperación.** Al reiniciar, los `QUEUED` guardados (ADR-0005) vuelven a la cola en su orden original y arrancan según el mismo límite.

## Consecuencias

**Positivas**
- El consumo de procesos y memoria tiene un tope configurable.
- El orden de ejecución es predecible y verificable.
- El cliente recibe una respuesta inmediata aun con el servicio saturado.

**Negativas**
- Un trabajo en cola puede tardar hasta 0,5 s en arrancar tras liberarse un lugar.
- El cliente debe reintentar cuando se le rechaza.

**Riesgos**
- Un trabajo aceptado se pierde por una condición de carrera entre cola y procesos — Mitigación: un solo hilo modifica `_cola` y `_procs`; la cola solo se vacía en `_despachar()` — Prueba: TC-002 y TC-016.
- La cola y el límite se desbordan al reanudar `QUEUED` tras un reinicio — Mitigación: `recuperar()` mete los `QUEUED` a la misma cola y llama a `tick()`, que respeta `max_jobs` — Prueba: `RecuperacionColaTest` en `verif/unit/test_cola.py`.
- Un trabajo cancelado en cola arranca igualmente — Mitigación: se saca de la cola al cancelarlo y `_despachar()` ignora los que ya no están en `QUEUED` — Prueba: TC-005 (cancelar en cola).

## Decisiones abiertas

Si el tiempo de espera del escalamiento (5 s) será configurable (se trata en ADR-0006). Prioridades entre trabajos: fuera del alcance del Hito 2.

## Requisitos afectados

RF-03, RF-05, RF-10, RF-25, RF-26, RF-30.

## Evidencia

Pruebas unitarias en `verif/unit/test_cola.py` y `verif/unit/test_servidor_cola.py`, y casos TC-002 y TC-016 en `verif/test-cases/`. Prueba manual de extremo a extremo (29/10/2026): con `--max-jobs 2 --queue-size 1`, tres `submit` dejan 2 trabajos `RUNNING` y 1 `QUEUED`, y el cuarto responde `cola llena (capacidad 1); intenta más tarde`; la bitácora registra `en_cola` y `rechazado`. La ejecución formal queda en `verif/results/<run-id>/`.
