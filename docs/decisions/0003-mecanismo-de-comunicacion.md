# ADR-0003: Mecanismo de comunicación del JobRunner

**Estado:** Aceptado
**Fecha:** 01/10/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez
**Issue relacionado:** #8
**Aprobado en:** PR #14
**Historial:** v1 (11/09/2026): propuesta inicial con API REST sobre HTTP. v2 (01/10/2026): corregido a daemon+CLI por socket Unix por decisión del equipo, al no requerir servidor HTTP para comunicación local.

## Contexto

Los clientes del JobRunner necesitan poder encolar nuevos jobs, consultar su estado y obtener resultados de ejecución. Se requiere definir el mecanismo por el cual un proceso daemon (que ejecuta los jobs y escribe en SQLite) se comunica con un CLI que el usuario invoca, considerando que ambos procesos corren en la misma máquina.

## Alternativas consideradas

1. **API REST sobre HTTP**
   - A favor: estándar ampliamente conocido por el equipo.
   - En contra: implica levantar un servidor HTTP y manejar networking, innecesario cuando el daemon y el cliente corren localmente.
2. **Socket Unix con mensajes JSON de una línea**
   - A favor: comunicación local entre procesos (IPC) sin overhead de red ni servidor HTTP; fácil de depurar con herramientas como socat o nc.
   - En contra: solo funciona para clientes en la misma máquina; requiere definir un protocolo propio de comandos/respuestas.
3. **Colas de mensajes (ej. Redis)**
   - A favor: desacopla productores y consumidores a gran escala.
   - En contra: requiere un servicio externo adicional, complejidad innecesaria para comunicación local entre dos procesos.

## Decisión

Se elige **daemon con socket Unix y mensajes JSON de una línea**, con el que un CLI se comunica enviando y recibiendo comandos.

Razones técnicas:
- Evita el overhead de un servidor HTTP cuando el daemon y el cliente corren localmente en la misma máquina.
- Se implementa con el módulo estándar socket de Python (ADR-0001), sin dependencias externas.

## Consecuencias

**Positivas**
- Comunicación local rápida y simple, sin manejo de puertos de red.
- Formato JSON por línea fácil de depurar manualmente.
- Permite evolucionar en el Hito 3 hacia el mismo protocolo JSON sobre TCP, restringido a LAN/VPN, sin rediseñar el formato de mensajes (RF-18 a RF-22).

**Negativas**
- Solo funciona para clientes en la misma máquina, no es accesible remotamente sin un mecanismo adicional.

**Riesgos**
- Protocolo propio sin estandarización como HTTP podría generar ambigüedad entre comandos — Mitigación: documentar el contrato de mensajes JSON (comandos y respuestas) en docs/ — Prueba: TC-008/TC-023.

## Decisiones abiertas

Transporte TCP restringido a LAN/VPN para acceso remoto (se resolverá en Hito 3).

## Requisitos afectados

RF-02, RF-04, RF-08, RF-09, RF-10, RF-18 a RF-22, RNF-08, RNF-12, RNF-14, RNF-24, RNF-32

## Evidencia

Pendiente: TC-001, TC-004, TC-008.