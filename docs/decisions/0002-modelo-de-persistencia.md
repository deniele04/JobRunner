# ADR-0002: Modelo de persistencia del JobRunner

**Estado:** Aceptado
**Fecha:** 01/10/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez
**Issue relacionado:** #8
**Aprobado en:** PR #14
**Historial:** v1 (11/09/2026): propuesta inicial con base de datos SQL genérica (PostgreSQL). v2 (01/10/2026): corregido a SQLite por decisión del equipo, al no requerir servidor aparte.

## Contexto

El JobRunner necesita almacenar el estado de los jobs (QUEUED, RUNNING, SUCCEEDED, FAILED o CANCELED, los mismos estados que usa el código en `src/jobrunner/jobs.py`), sus resultados y metadatos de ejecución. Se requiere un mecanismo de persistencia confiable, simple de desplegar y sin infraestructura adicional (sin servidor aparte, sin privilegios de administrador), dado el tiempo disponible del curso.

## Alternativas consideradas

1. **PostgreSQL**
   - A favor: motor relacional robusto, pensado para producción real.
   - En contra: requiere levantar y mantener un servidor de base de datos aparte; complejidad de infraestructura innecesaria para el alcance y tiempo del proyecto.
2. **SQLite**
   - A favor: motor relacional embebido, incluido en la librería estándar de Python (sqlite3), sin servidor aparte; soporta transacciones y SQL estándar.
   - En contra: menor capacidad de concurrencia de escritura que un servidor dedicado.
3. **Archivos planos / JSON local**
   - A favor: simplicidad inicial, sin dependencias.
   - En contra: no garantiza consistencia ni concurrencia segura entre jobs.

## Decisión

Se elige **SQLite**.

Razones técnicas:
- No requiere servidor de base de datos independiente, a diferencia de PostgreSQL, lo que simplifica el despliegue dentro del tiempo del curso.
- Viene integrado en la librería estándar de Python (ADR-0001), sin dependencias externas.

## Consecuencias

**Positivas**
- Cero infraestructura adicional; despliegue en un solo archivo de base de datos.
- Consultas SQL estructuradas sobre el historial de jobs.

**Negativas**
- Menor capacidad de concurrencia de escritura frente a un servidor dedicado como PostgreSQL.

**Riesgos**
- Escrituras concurrentes desde múltiples procesos podrían bloquear la base de datos — Mitigación: solo el daemon (ADR-0003) escribe en SQLite, evitando escrituras concurrentes de varios procesos — Prueba: TC-007/TC-022.

## Decisiones abiertas

Esquema de tablas y estado de los trabajos tras reiniciar el daemon (se resolverá en Hito 2).

## Requisitos afectados

RF-07, RF-09, RF-12, RF-13, RNF-02, RNF-06, RNF-10, RNF-11, RNF-28, RNF-31

## Evidencia

python3 -c "import sqlite3; print(sqlite3.sqlite_version)" confirma la disponibilidad de SQLite en el entorno de desarrollo del equipo sin instalación adicional.