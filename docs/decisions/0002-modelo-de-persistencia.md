\# ADR-0002: Modelo de persistencia del JobRunner



\*\*Estado:\*\* Aceptado

\*\*Fecha:\*\* 01/10/2026

\*\*Responsable(s):\*\* Josué Said Delgadillo Gutiérrez



\## Contexto



El JobRunner necesita almacenar el estado de los jobs (pendiente, en

ejecución, completado, fallido), sus resultados y metadatos de ejecución. Se

requiere un mecanismo de persistencia confiable, simple de desplegar y sin

infraestructura adicional, dado el tiempo disponible del curso.



\## Opciones consideradas



1\. \*\*PostgreSQL\*\* — Motor relacional robusto para producción real, pero

&#x20;  requiere levantar y mantener un servidor de base de datos aparte, lo cual

&#x20;  añade complejidad de infraestructura innecesaria para el alcance del

&#x20;  proyecto y el tiempo disponible.

2\. \*\*SQLite\*\* — Motor relacional embebido, viene incluido en la librería

&#x20;  estándar de Python (`sqlite3`), sin servidor aparte que instalar o

&#x20;  mantener; soporta transacciones y SQL estándar, suficiente para el volumen

&#x20;  de jobs esperado en el proyecto.

3\. \*\*Archivos planos / JSON local\*\* — Simplicidad inicial, pero no garantiza

&#x20;  consistencia ni concurrencia segura entre múltiples jobs.



\## Decisión



Se elige \*\*SQLite\*\* para la persistencia del JobRunner. A diferencia de

PostgreSQL, no requiere un servidor de base de datos independiente: viene

integrado en Python, lo que simplifica el despliegue y reduce el tiempo de

configuración, manteniendo transacciones y consultas SQL estructuradas sobre

el estado de los jobs.



\## Consecuencias



\- \*\*Positivas:\*\* cero infraestructura adicional, despliegue simplificado

&#x20; (un solo archivo de base de datos), consultas SQL estructuradas sobre el

&#x20; historial de jobs, integración directa vía `sqlite3` de Python.

\- \*\*Negativas / trade-offs:\*\* menor capacidad de concurrencia de escritura

&#x20; que un servidor dedicado como PostgreSQL; no apto si el proyecto creciera a

&#x20; múltiples instancias del JobRunner escribiendo simultáneamente.

\- \*\*Impacto en otras áreas:\*\* depende del lenguaje elegido (ADR-0001); el

&#x20; daemon (ADR-0003) es el único proceso que escribe en la base de datos,

&#x20; evitando problemas de concurrencia de SQLite.

