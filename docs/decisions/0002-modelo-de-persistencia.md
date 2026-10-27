# ADR-0002: Modelo de persistencia del JobRunner

**Estado:** Propuesto
**Fecha:** 27/10/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez
**Issue relacionado:** #8
**Aprobado en:** PR pendiente
**Historial:** v1 (11/09/2026): propuesta inicial con base de datos SQL genérica (PostgreSQL). v2 (01/10/2026): corregido a SQLite por decisión del equipo, al no requerir servidor aparte. v3 (27/10/2026): se define el esquema de la tabla, las transacciones y la retención, según la minuta del 20/10/2026.

## Contexto

El JobRunner necesita almacenar el estado de los jobs (QUEUED, RUNNING, SUCCEEDED, FAILED o CANCELED, los mismos estados que usa el código en `src/jobrunner/jobs.py`), sus resultados y metadatos de ejecución, de modo que sobrevivan a un reinicio del servidor. Se requiere un mecanismo de persistencia confiable, simple de desplegar y sin infraestructura adicional (sin servidor aparte, sin privilegios de administrador), dado el tiempo disponible del curso. Hasta el Avance 1 el estado vivía solo en memoria y se perdía al detener el servidor.

## Alternativas consideradas

1. **PostgreSQL**
   - A favor: motor relacional robusto, pensado para producción real.
   - En contra: requiere levantar y mantener un servidor de base de datos aparte; complejidad de infraestructura innecesaria para el alcance y tiempo del proyecto.
2. **SQLite**
   - A favor: motor relacional embebido, incluido en la librería estándar de Python (sqlite3), sin servidor aparte; soporta transacciones y SQL estándar.
   - En contra: menor capacidad de concurrencia de escritura que un servidor dedicado.
3. **Archivos planos / JSON local**
   - A favor: simplicidad inicial, sin dependencias.
   - En contra: no garantiza consistencia ante una interrupción a mitad de una escritura ni evita duplicados de forma natural.

## Decisión

Se elige **SQLite**, en el archivo `data/jobrunner.db`, con una fila por trabajo.

Razones técnicas:
- No requiere servidor de base de datos independiente, a diferencia de PostgreSQL, lo que simplifica el despliegue dentro del tiempo del curso.
- Viene integrado en la librería estándar de Python (ADR-0001), sin dependencias externas.
- Sus transacciones permiten que un cambio de estado se guarde completo o no se guarde, incluso si el servidor muere a mitad de la escritura.

**Esquema.** Una sola tabla:

```sql
CREATE TABLE IF NOT EXISTS jobs (
  id           TEXT PRIMARY KEY,
  request_id   TEXT UNIQUE,
  argv         TEXT NOT NULL,
  state        TEXT NOT NULL CHECK (state IN
               ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELED')),
  exit_code    INTEGER,
  error        TEXT,
  pid          INTEGER,
  created_at   TEXT NOT NULL,
  started_at   TEXT,
  finished_at  TEXT,
  stdout_path  TEXT,
  stderr_path  TEXT
);
```

- `id` es el identificador único del trabajo (UUID).
- `request_id` es el identificador opcional que manda el cliente. `UNIQUE` hace que la propia base de datos impida crear dos trabajos con el mismo `request_id`. Los trabajos enviados sin él quedan con NULL, y SQLite no considera iguales dos NULL.
- `argv` se guarda como texto JSON.
- `pid` es el proceso líder del grupo del trabajo, y sirve para terminar el grupo durante la recuperación (ADR-0005).
- Las fechas se guardan en ISO 8601 UTC, igual que en `jobs.py`.

**Transacciones.** Solo el servidor escribe en la base. Cada cambio de estado (alta, inicio, fin, cancelación y recuperación) se ejecuta en su propia transacción (`with conn:`), de modo que nunca queda guardado un estado a medias.

**Retención.** Se conservan todos los registros de la tabla y todos los archivos de salida (`.out` y `.err`). No hay borrado automático en el Hito 2.

## Consecuencias

**Positivas**
- Cero infraestructura adicional; despliegue en un solo archivo de base de datos.
- Consultas SQL estructuradas sobre el historial de jobs.
- Los duplicados por `request_id` los garantiza la base de datos, no solo el código.

**Negativas**
- Menor capacidad de concurrencia de escritura frente a un servidor dedicado como PostgreSQL.
- Sin borrado automático, el historial y los archivos de salida crecen sin límite.

**Riesgos**
- Escrituras concurrentes desde múltiples procesos podrían bloquear la base de datos — Mitigación: solo el servidor (ADR-0003) escribe en SQLite, evitando escrituras concurrentes de varios procesos — Prueba: TC-007/TC-022.
- Una interrupción a mitad de una escritura podría dejar un estado inconsistente — Mitigación: cada cambio va en una transacción de SQLite, que es atómica — Prueba: TC-022.
- El crecimiento del historial puede llenar el disco — Mitigación: se acepta en el Hito 2; el borrado queda como mejora futura — Prueba: ninguna en este hito.

## Decisiones abiertas

Cómo verificar TC-022 (interrupción durante una escritura) de forma repetible; se resuelve en la minuta 2 del Avance 2.

## Requisitos afectados

RF-07, RF-09, RF-12, RF-13, RF-27, RF-28, RNF-02, RNF-06, RNF-10, RNF-11, RNF-28, RNF-31

## Evidencia

`python3 -c "import sqlite3; print(sqlite3.sqlite_version)"` confirma la disponibilidad de SQLite en el entorno de desarrollo del equipo sin instalación adicional. La verificación del esquema y de las transacciones será TC-007 y TC-022.
