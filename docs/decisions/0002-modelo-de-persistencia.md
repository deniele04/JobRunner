# ADR-0002: Modelo de persistencia del JobRunner



**Estado:** Aceptado

**Fecha:** 01/10/2026

**Responsable(s):** Josué Said Delgadillo Gutiérrez

**Issue relacionado:** #8

**Aprobado en:** PR #13

**Historial:** v1 (10/09/2026): propuesta inicial con base de datos SQL genérica (PostgreSQL). v2 (01/10/2026): corregido a SQLite por decisión del equipo, al no requerir servidor aparte.



## Contexto



El JobRunner necesita almacenar el estado de los jobs (pendiente, en ejecución, completado, fallido), sus resultados y metadatos de ejecución. Se requiere un mecanismo de persistencia confiable, simple de desplegar y sin infraestructura adicional (sin servidor aparte, sin privilegios de administrador), dado el tiempo disponible del curso.



## Alternativas consideradas



1\. **PostgreSQL**

&#x20;  - A favor: motor relacional robusto, pensado para producción real.

&#x20;  - En contra: requiere levantar y mantener un servidor de base de datos aparte; complejidad de infraestructura innecesaria para el alcance y tiempo del proyecto.

2\. **SQLite**

&#x20;  - A favor: motor relacional embebido, incluido en la librería estándar de Python (`sqlite3`), sin servidor aparte; soporta transacciones y SQL estándar.

&#x20;  - En contra: menor capacidad de concurrencia de escritura que un servidor dedicado.

3\. **Archivos planos / JSON local**

&#x20;  - A favor: simplicidad inicial, sin dependencias.

&#x20;  - En contra: no garantiza consistencia ni concurrencia segura entre jobs.



## Decisión



Se elige **SQLite**.



Razones técnicas:

\- No requiere servidor de base de datos independiente, a diferencia de PostgreSQL, lo que simplifica el despliegue dentro del tiempo del curso.

\- Viene integrado en la librería estándar de Python (ADR-0001), sin dependencias externas.



## Consecuencias



**Positivas**

\- Cero infraestructura adicional; despliegue en un solo archivo de base de datos.

\- Consultas SQL estructuradas sobre el historial de jobs.



**Negativas**

\- Menor capacidad de concurrencia de escritura frente a un servidor dedicado como PostgreSQL.



**Riesgos**

\- Escrituras concurrentes desde múltiples procesos podrían bloquear la base de datos — Mitigación: solo el daemon (ADR-0003) escribe en SQLite, evitando escrituras concurrentes de varios procesos — Prueba: TC-002 (pendiente de definir en Avance 1).



## Decisiones abiertas



Ninguna.



## Requisitos afectados



\[Pendiente — completar con los códigos RF-XX/RNF-XX del documento de requisitos del equipo]



## Evidencia



\[Pendiente — se documentará con el resultado de `verif/results/` una vez exista código ejecutable en Avance 1]

