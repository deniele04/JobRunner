\# ADR-0003: Mecanismo de comunicación del JobRunner



\*\*Estado:\*\* Aceptado

\*\*Fecha:\*\* 01/10/2026

\*\*Responsable(s):\*\* Josué Said Delgadillo Gutiérrez



\## Contexto



Los clientes del JobRunner necesitan poder encolar nuevos jobs, consultar su

estado y obtener resultados de ejecución. Se requiere definir el mecanismo por

el cual un proceso daemon (que ejecuta los jobs y escribe en SQLite) se

comunica con un CLI que el usuario invoca.



\## Opciones consideradas



1\. \*\*API REST sobre HTTP\*\* — Estándar conocido, pero implica levantar un

&#x20;  servidor HTTP y manejar networking, lo cual es innecesario cuando el daemon

&#x20;  y el cliente corren en la misma máquina.

2\. \*\*Socket Unix con mensajes JSON de una línea\*\* — Comunicación local entre

&#x20;  procesos (IPC) mediante un archivo de socket; sin overhead de red ni

&#x20;  servidor HTTP; cada mensaje es una línea JSON que el daemon interpreta y

&#x20;  responde.

3\. \*\*Colas de mensajes (ej. Redis)\*\* — Requiere un servicio externo adicional,

&#x20;  complejidad innecesaria para comunicación local entre dos procesos.



\## Decisión



Se elige un \*\*daemon que expone un socket Unix\*\*, con el que un \*\*CLI\*\* se

comunica enviando y recibiendo \*\*mensajes JSON de una línea\*\* (un objeto JSON

por línea, terminado en salto de línea). El daemon escucha en el socket,

procesa comandos (encolar job, consultar estado) y responde por el mismo

canal. Se prefiere sobre API REST porque el daemon y el cliente corren

localmente en la misma máquina, evitando el overhead de un servidor HTTP.



\## Consecuencias



\- \*\*Positivas:\*\* comunicación local rápida y simple, sin dependencias de

&#x20; librerías HTTP ni manejo de puertos de red; el formato JSON por línea es

&#x20; fácil de depurar (se puede probar con herramientas como `socat` o `nc`).

\- \*\*Negativas / trade-offs:\*\* solo funciona para clientes en la misma

&#x20; máquina (no es accesible remotamente sin un mecanismo adicional); requiere

&#x20; definir un protocolo propio de comandos/respuestas JSON en vez de usar

&#x20; convenciones HTTP ya estandarizadas.

\- \*\*Impacto en otras áreas:\*\* depende del lenguaje elegido (ADR-0001, módulo

&#x20; `socket` de Python); el daemon es el único proceso que accede a SQLite

&#x20; (ADR-0002), evitando problemas de concurrencia de escritura.

