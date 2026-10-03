# ADR-0001: Lenguaje y runtime del JobRunner

**Estado:** Aceptado
**Fecha:** 01/10/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez
**Issue relacionado:** #3
**Aprobado en:** PR #14
**Historial:** v1 (11/09/2026): Python con Celery y SQL. v2 (01/10/2026): solo biblioteca estándar.

## Contexto

Es necesario definir el lenguaje de programación y runtime principal en el que se implementará el JobRunner, considerando la experiencia del equipo, el soporte para concurrencia (necesario para ejecutar jobs), el tiempo disponible del curso y la ausencia de infraestructura adicional (sin servidores externos, sin privilegios de administrador en las máquinas del equipo).

## Alternativas consideradas

1. **Python**
   - A favor: curva de aprendizaje baja para el equipo, librería estándar incluye sqlite3 y socket, sin dependencias externas que instalar.
   - En contra: paralelismo real limitado por el GIL en cargas CPU-intensivas.
2. **Node.js**
   - A favor: buen desempeño en operaciones I/O-bound.
   - En contra: el equipo tiene menos experiencia; manejo de procesos de larga duración menos maduro.
3. **Go**
   - A favor: excelente concurrencia real y rendimiento.
   - En contra: curva de aprendizaje alta para el equipo; menor velocidad de desarrollo dado el tiempo del curso.

## Decisión

Se elige **Python**.

Razones técnicas:
- Permite usar sqlite3 y socket de la librería estándar sin dependencias externas, ligado directamente a ADR-0002 y ADR-0003.
- Maximiza la velocidad de desarrollo del equipo dentro del tiempo disponible del curso.

## Consecuencias

**Positivas**
- Desarrollo más rápido con módulos estándar ya probados.
- Sin dependencias externas que instalar en las máquinas del equipo.

**Negativas**
- Rendimiento limitado en tareas CPU-intensivas concurrentes.

**Riesgos**
- El GIL limita el paralelismo real — Mitigación: usar procesos separados (multiprocessing) si el volumen de jobs concurrentes lo exige — Prueba: TC-002.

## Decisiones abiertas

Ninguna.

## Requisitos afectados

RF-04, RF-10, RNF-01, RNF-02, RNF-03, RNF-17, RNF-19

## Evidencia

Ver src/jobrunner/executor.py (Juan José Rentería Haro) como implementación de referencia construida únicamente con la librería estándar de Python.