# ADR-0005: Recuperación del estado al arrancar el servidor

**Estado:** Propuesto
**Fecha:** 27/10/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez
**Issue relacionado:** #por asignar
**Aprobado en:** PR pendiente

## Contexto

Con la persistencia en SQLite (ADR-0002), el servidor puede detenerse, por una caída o por un cierre, mientras hay trabajos en cola o en ejecución. Al volver a arrancar debe decidir qué hacer con ellos. Si no se decide, un trabajo RUNNING quedaría para siempre en ese estado sin proceso real, y los trabajos en cola se perderían, incumpliendo RF-12 y RF-13. Restricción: el servidor no tiene forma de volver a vigilar un proceso que arrancó una instancia anterior, porque ya no es su proceso hijo.

## Alternativas consideradas

1. **Marcar los RUNNING como FAILED y reponer los QUEUED**
   - A favor: simple y honesto; el servidor no pretende saber el resultado de un proceso que ya no controla.
   - En contra: se pierde el resultado de un trabajo que pudo terminar bien mientras el servidor estaba caído.
2. **Volver a ejecutar los RUNNING**
   - A favor: no se pierde el trabajo.
   - En contra: puede repetir efectos secundarios (escribir archivos, enviar datos), y no hay garantía de que el trabajo sea repetible.
3. **Intentar adoptar el proceso por su PID**
   - A favor: conserva el resultado real.
   - En contra: el servidor no puede hacer `wait` de un proceso que no es su hijo, así que no obtendría el código de salida; además el PID podría haberse reutilizado.

## Decisión

Se elige la **alternativa 1**. Al arrancar, antes de aceptar solicitudes, el servidor lee la tabla `jobs` y aplica estas reglas:

- Los trabajos en **QUEUED** vuelven a la cola, en su orden original (`created_at`).
- Los trabajos en **RUNNING** pasan a **FAILED** con `error = "interrumpido por reinicio"` y `finished_at` con la hora de la recuperación. Si su grupo de procesos sigue vivo, se le envía SIGTERM al grupo, y SIGKILL si no termina.
- Los trabajos en estado final (SUCCEEDED, FAILED, CANCELED) no se tocan.
- Cada trabajo recuperado se registra en la bitácora con el evento `recuperado`.

Razones técnicas:
- Es la única opción que no repite efectos secundarios ni depende de un PID que pudo reutilizarse.
- Mantiene el modelo de estados existente: FAILED ya cubre un fallo, sin añadir estados nuevos.
- Cada actualización de estado va en una transacción (ADR-0002), así que la recuperación misma es segura si el servidor vuelve a caer mientras recupera.

## Consecuencias

**Positivas**
- Tras cualquier reinicio, ningún trabajo queda en un estado que no corresponde a la realidad.
- Los trabajos en cola no se pierden (RF-12).
- No se agregan estados nuevos al modelo.

**Negativas**
- Un trabajo que sí terminó bien durante la caída aparece como FAILED.
- Con `start_new_session=True`, el grupo de procesos puede seguir vivo tras la caída; hay que terminarlo explícitamente.

**Riesgos**
- El PID guardado pudo ser reutilizado por otro proceso y se terminaría un proceso ajeno — Mitigación: se envía la señal al grupo de procesos (`os.killpg`) solo si el grupo sigue existiendo, y se registra el evento en la bitácora — Prueba: TC-007.
- Una caída durante la propia recuperación — Mitigación: la recuperación es idempotente; repetirla da el mismo resultado porque los estados ya cambiados no se vuelven a tocar — Prueba: TC-022.

## Decisiones abiertas

Si el tiempo de espera del escalamiento (5 s) será configurable; se resuelve en la minuta 2 del Avance 2.

## Requisitos afectados

RF-12, RF-13, RF-27, RF-28

## Evidencia

Pendiente de la ejecución de TC-007 (reinicio del servicio sin perder trabajos) y TC-022 (interrupción durante una escritura) sobre el commit candidato, con la evidencia en `verif/results/`.
