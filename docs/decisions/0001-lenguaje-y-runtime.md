# ADR-0001: Lenguaje y runtime del JobRunner

**Estado:** Propuesto
**Fecha:** 11/09/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez

## Contexto

Es necesario definir el lenguaje de programación y runtime principal en el que
se implementará el JobRunner, considerando la experiencia del equipo, el
soporte para concurrencia/paralelismo (necesario para ejecutar jobs), y la
facilidad de despliegue.

## Opciones consideradas

1. **Python** — Curva de aprendizaje baja para el equipo, amplio ecosistema de
   librerías para tareas asíncronas y colas (asyncio, Celery, RQ), buena
   integración con bases de datos SQL. Como desventaja, el paralelismo real
   está limitado por el GIL en cargas CPU-intensivas.
2. **Node.js** — Buen desempeño en operaciones I/O-bound y concurrencia
   asíncrona nativa, pero el equipo tiene menos experiencia y el manejo de
   errores en jobs largos es menos maduro que en Python.
3. **Go** — Excelente concurrencia real y rendimiento, pero curva de
   aprendizaje alta para el equipo y menor velocidad de desarrollo dado el
   tiempo disponible del curso.

## Decisión

Se elige **Python** como lenguaje y runtime principal del JobRunner, por la
experiencia previa del equipo, la velocidad de desarrollo que permite dentro
del tiempo del curso, y su compatibilidad directa con el motor de persistencia
elegido (ver ADR-0002).

## Consecuencias

- **Positivas:** desarrollo más rápido, mejor documentación y soporte de la
  comunidad, integración sencilla con librerías de manejo de jobs y con SQL.
- **Negativas / trade-offs:** rendimiento limitado en tareas CPU-intensivas
  concurrentes; puede requerir procesos separados o librerías externas
  (multiprocessing, Celery) si el volumen de jobs crece.
- **Impacto en otras áreas:** afecta directamente el mecanismo de persistencia
  (ADR-0002) y el modelo de comunicación con clientes (ADR-0003).
