# ADR-0003: Mecanismo de comunicación del JobRunner



**Estado:** Aceptado

**Fecha:** 01/10/2026

**Responsable(s):** Josué Said Delgadillo Gutiérrez

**Issue relacionado:** #8

**Aprobado en:** PR #13

**Historial:** v1 (10/09/2026): propuesta inicial con API REST sobre HTTP. v2 (01/10/2026): corregido a daemon+CLI por socket Unix por decisión del equipo, al no requerir servidor HTTP para comunicación local.



## Contexto



Los clientes del JobRunner necesitan poder encolar nuevos jobs, consultar su estado y obtener resultados de ejecución. Se requiere definir el mecanismo por el cual un proceso daemon (que ejecuta los jobs y escribe en SQLite) se comunica con un CLI que el usuario invoca, considerando que ambos procesos corren en la misma máquina.



## Alternativas consideradas



1\. **API REST sobre HTTP**

&#x20;  - A favor: estándar ampliamente conocido por el equipo.

&#x20;  - En contra: implica levantar un servidor HTTP y manejar networking, innecesario cuando el daemon y el cliente corren localmente.

2\. **Socket Unix con mensajes JSON de una línea**

&#x20;  - A favor: comunicación local entre procesos (IPC) sin overhead de red ni servidor HTTP; fácil de depurar con herramientas como `socat` o `nc`.

&#x20;  - En contra: solo funciona para clientes en la misma máquina; requiere definir un protocolo propio de comandos/respuestas.

3\. **Colas de mensajes (ej. Redis)**

&#x20;  - A favor: desacopla productores y consumidores a gran escala.

&#x20;  - En contra: requiere un servicio externo adicional, complejidad innecesaria para comunicación local entre dos procesos.



## Decisión



Se elige **daemon con socket Unix y mensajes JSON de una línea**, con el que un CLI se comunica enviando y recibiendo comandos.



Razones técnicas:

\- Evita el overhead de un servidor HTTP cuando el daemon y el cliente corren localmente en la misma máquina.

\- Se implementa con el módulo estándar `socket` de Python (ADR-0001), sin dependencias externas.



## Consecuencias



**Positivas**

\- Comunicación local rápida y simple, sin manejo de puertos de red.

\- Formato JSON por línea fácil de depurar manualmente.



**Negativas**

\- Solo funciona para clientes en la misma máquina, no es accesible remotamente sin un mecanismo adicional.



**Riesgos**

\- Protocolo propio sin estandarización como HTTP podría generar ambigüedad entre comandos — Mitigación: documentar el contrato de mensajes JSON (comandos y respuestas) en `docs/` — Prueba: TC-003 (pendiente de definir en Avance 1).



## Decisiones abiertas



Ninguna.



## Requisitos afectados



\[Pendiente — completar con los códigos RF-XX/RNF-XX del documento de requisitos del equipo]



## Evidencia



\[Pendiente — se documentará con el resultado de `verif/results/` una vez exista código ejecutable en Avance 1]

