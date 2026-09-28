# ADR-0002: Modelo de persistencia del JobRunner

**Estado:** Propuesto
**Fecha:** 11/09/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez

## Contexto

El JobRunner necesita almacenar el estado de los jobs (pendiente, en
ejecución, completado, fallido), sus resultados y metadatos de ejecución. Se
requiere un mecanismo de persistencia confiable que permita consultar el
historial y el estado actual de cada job.

## Opciones consideradas

1. **Base de datos SQL (ej. PostgreSQL/SQLite)** — Modelo relacional claro
   para relacionar jobs, ejecuciones y resultados; transacciones ACID
   garantizan consistencia en cambios de estado; buen soporte en Python.
2. **Base de datos NoSQL (ej. MongoDB)** — Más flexible para metadatos
   variables por tipo de job, pero menos natural para relaciones y consultas
   estructuradas sobre el historial de ejecuciones.
3. **Archivos planos / JSON local** — Simplicidad inicial sin dependencias
   externas, pero no escala ni soporta concurrencia segura entre múltiples
   jobs ejecutándose a la vez.

## Decisión

Se elige una **base de datos SQL** para la persistencia del JobRunner, dado
que el estado y las relaciones entre jobs y ejecuciones se modelan de forma
natural en tablas relacionales, y se necesita consistencia transaccional al
actualizar el estado de un job.

## Consecuencias

- **Positivas:** consultas estructuradas sobre historial y estado, integridad
  garantizada por transacciones, buen soporte de librerías ORM en Python
  (SQLAlchemy).
- **Negativas / trade-offs:** requiere definir y mantener un esquema desde el
  inicio; menor flexibilidad si el formato de metadatos de los jobs varía
  mucho entre tipos.
- **Impacto en otras áreas:** depende del lenguaje elegido (ADR-0001) para la
  librería de acceso a datos; afecta el diseño de la API de consulta de
  estado (ADR-0003).
