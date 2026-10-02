# ADR-0001: Lenguaje y runtime del JobRunner



**Estado:** Aceptado

**Fecha:** 01/10/2026

**Responsable(s):** Josué Said Delgadillo Gutiérrez

**Issue relacionado:** #3

**Aprobado en:** PR #13

**Historial:** Omitir, es la primera versión aprobada.



## Contexto



Es necesario definir el lenguaje de programación y runtime principal en el que se implementará el JobRunner, considerando la experiencia del equipo, el soporte para concurrencia (necesario para ejecutar jobs), el tiempo disponible del curso y la ausencia de infraestructura adicional (sin servidores externos, sin privilegios de administrador en las máquinas del equipo).



## Alternativas consideradas



1\. **Python**

&#x20;  - A favor: curva de aprendizaje baja para el equipo, librería estándar incluye `sqlite3` y `socket`, sin dependencias externas que instalar.

&#x20;  - En contra: paralelismo real limitado por el GIL en cargas CPU-intensivas.

2\. **Node.js**

&#x20;  - A favor: buen desempeño en operaciones I/O-bound.

&#x20;  - En contra: el equipo tiene menos experiencia; manejo de procesos de larga duración menos maduro.

3\. **Go**

&#x20;  - A favor: excelente concurrencia real y rendimiento.

&#x20;  - En contra: curva de aprendizaje alta para el equipo; menor velocidad de desarrollo dado el tiempo del curso.



## Decisión



Se elige **Python**.



Razones técnicas:

\- Permite usar `sqlite3` y `socket` de la librería estándar sin dependencias externas, ligado directamente a ADR-0002 y ADR-0003.

\- Maximiza la velocidad de desarrollo del equipo dentro del tiempo disponible del curso.



## Consecuencias



**Positivas**

\- Desarrollo más rápido con módulos estándar ya probados.

\- Sin dependencias externas que instalar en las máquinas del equipo.



**Negativas**

\- Rendimiento limitado en tareas CPU-intensivas concurrentes.



**Riesgos**

\- El GIL limita el paralelismo real — Mitigación: usar procesos separados (`multiprocessing`) si el volumen de jobs concurrentes lo exige — Prueba: TC-001 (pendiente de definir en Avance 1).



## Decisiones abiertas



Ninguna.



## Requisitos afectados



\[Pendiente — completar con los códigos RF-XX/RNF-XX del documento de requisitos del equipo]



## Evidencia



\[Pendiente — se documentará con el resultado de `verif/results/` una vez exista código ejecutable en Avance 1]

