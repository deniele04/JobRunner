# IA-004 — ADR-0002 (esquema y retencion) y ADR-0005 (recuperacion)

| Campo | Valor |
|---|---|
| **Fecha** | 27/10/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 2 - Concurrencia y persistencia (Avance 2) |
| **Artefactos afectados** | docs/decisions/0002-modelo-de-persistencia.md, docs/decisions/0005-recuperacion-al-arrancar.md |
| **Clasificacion** | En revision |

## 1. Objetivo

Segun la minuta del 20/10/2026, Josue debe actualizar el ADR-0002 con el esquema de la tabla de SQLite y la retencion, y escribir el ADR-0005 de recuperacion al arrancar. Se uso la IA para:

1. Leer la minuta, el ADR-0002 vigente, la plantilla de ADR y `jobs.py` para identificar que decisiones ya estaban tomadas y cuales faltaban.

2. Proponer el esquema de la tabla `jobs` y las reglas de recuperacion, para que Josue las aprobara o cambiara.

3. Redactar ambos ADR con la plantilla del repositorio.

## 2. Entrada proporcionada

- La minuta del 20/10/2026 (decisiones 6, 7 y 10, y las decisiones abiertas).

- El ADR-0002 vigente (v2) y `docs/decisions/template.md`.

- `src/jobrunner/jobs.py` y `executor.py`, para que el esquema coincidiera con los campos de la clase `Job`.

## 3. Resultado recibido

1. Esquema de la tabla `jobs`: los campos de `Job` mas `request_id` (UNIQUE, opcional) y `pid`, con una restriccion CHECK sobre los cinco estados.

2. Texto del ADR-0002 v3: esquema, transacciones por cambio de estado y retencion sin borrado automatico.

3. Texto del ADR-0005: los trabajos QUEUED vuelven a la cola, los RUNNING pasan a FAILED con el motivo "interrumpido por reinicio" y se termina su grupo de procesos si sigue vivo.

## 4. Revision realizada

- Josue reviso el esquema propuesto y lo aprobo antes de escribirlo en el ADR.

- Josue corrigio el formato del texto pegado (escapes de markdown y saltos de linea duplicados) y verifico el resultado en el archivo antes del commit.

- Ambos ADR se contrastaron con las decisiones 6, 7 y 10 de la minuta del 20/10/2026.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Esquema de la tabla `jobs` con `request_id` UNIQUE y `pid` | Aprobado por Josue; pendiente de revision del equipo | Aceptado |
| Recuperacion: QUEUED a la cola, RUNNING a FAILED | Coincide con la decision 7 de la minuta; pendiente de revision del equipo | Aceptado |
| Descripcion del riesgo de reutilizacion de PID y su mitigacion | Se incluyo en el ADR-0005 | Aceptado |

## 6. Limitaciones del resultado de la IA

- La IA no ejecuto codigo ni probo el esquema; es una propuesta de diseno. Su verificacion queda en TC-007 y TC-022.

- La IA no tuvo acceso a las Issues ni a los PR del repositorio, por lo que los campos "Issue relacionado" y "Aprobado en" quedaron pendientes.

- Las decisiones abiertas (tiempo de escalamiento configurable y como verificar TC-022) no se resuelven en estos ADR.

## 7. Prueba o verificacion agregada

Ninguna en este PR, son documentos de diseno. La evidencia que respaldara las decisiones sera TC-007 (reinicio sin perder trabajos) y TC-022 (interrupcion durante una escritura).

**Verifico:** Josue Said Delgadillo Gutierrez (27/10/2026)

## 8. Aprendizaje

- Revisar la minuta antes de proponer un diseno evita contradecir decisiones que el equipo ya tomo.

- Un campo UNIQUE en la base de datos hace que la garantia contra duplicados no dependa solo del codigo del servidor.

- Decidir de antemano que pasa con los trabajos RUNNING tras un reinicio evita estados que no corresponden a la realidad.
