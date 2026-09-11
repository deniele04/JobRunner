# ADR-0001: Lenguaje y runtime del JobRunner

**Estado:** Propuesto
**Fecha:** [DD/MM/AAAA]
**Responsable(s):** [Nombre]

## Contexto

Es necesario definir el lenguaje de programación y runtime principal en el que
se implementará el JobRunner, considerando la experiencia del equipo, el
soporte para concurrencia/paralelismo (necesario para ejecutar jobs), y la
facilidad de despliegue.

## Opciones consideradas

1. **[Opción A, ej. Python + asyncio]** — [ventajas/desventajas]
2. **[Opción B, ej. Node.js]** — [ventajas/desventajas]
3. **[Opción C, ej. Go]** — [ventajas/desventajas]

## Decisión

[PENDIENTE — se resolverá en Avance 1]

## Consecuencias

- **Positivas:** [pendiente]
- **Negativas / trade-offs:** [pendiente]
- **Impacto en otras áreas:** afecta directamente el mecanismo de persistencia
  (ADR-0002) y el modelo de comunicación con clientes (ADR-0003).
