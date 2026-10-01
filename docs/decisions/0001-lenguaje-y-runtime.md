\# ADR-0001: Lenguaje y runtime del JobRunner



\*\*Estado:\*\* Aceptado

\*\*Fecha:\*\* 01/10/2026

\*\*Responsable(s):\*\* Josué Said Delgadillo Gutiérrez



\## Contexto



Es necesario definir el lenguaje de programación y runtime principal en el que

se implementará el JobRunner, considerando la experiencia del equipo, el

soporte para concurrencia/paralelismo (necesario para ejecutar jobs), y la

facilidad de despliegue.



\## Opciones consideradas



1\. \*\*Python\*\* — Curva de aprendizaje baja para el equipo, amplio ecosistema de

&#x20;  librerías para tareas asíncronas y concurrencia (asyncio, threading,

&#x20;  multiprocessing), integración nativa con SQLite. Como desventaja, el

&#x20;  paralelismo real está limitado por el GIL en cargas CPU-intensivas.

2\. \*\*Node.js\*\* — Buen desempeño en operaciones I/O-bound, pero el equipo tiene

&#x20;  menos experiencia y el manejo de procesos de larga duración es menos

&#x20;  maduro que en Python.

3\. \*\*Go\*\* — Excelente concurrencia real, pero curva de aprendizaje alta para

&#x20;  el equipo y menor velocidad de desarrollo dado el tiempo disponible.



\## Decisión



Se elige \*\*Python\*\* como lenguaje y runtime principal del JobRunner, por la

experiencia previa del equipo, la velocidad de desarrollo que permite dentro

del tiempo del curso, y su integración directa con SQLite (ver ADR-0002) y con

sockets Unix (ver ADR-0003) a través de su librería estándar.



\## Consecuencias



\- \*\*Positivas:\*\* desarrollo más rápido, módulos estándar (`sqlite3`, `socket`)

&#x20; cubren persistencia y comunicación sin dependencias externas.

\- \*\*Negativas / trade-offs:\*\* rendimiento limitado en tareas CPU-intensivas

&#x20; concurrentes; mitigable usando procesos separados si el volumen de jobs

&#x20; crece.

\- \*\*Impacto en otras áreas:\*\* habilita directamente las decisiones de

&#x20; persistencia (ADR-0002) y comunicación (ADR-0003).

