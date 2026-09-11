# ADR-0003: Mecanismo de comunicación con clientes del JobRunner

**Estado:** Propuesto
**Fecha:** [DD/MM/AAAA]
**Responsable(s):** [Nombre]

## Contexto

Los clientes del JobRunner necesitan poder enviar (encolar) jobs y consultar
su estado. Es necesario decidir el mecanismo de interacción expuesto por el
servicio.

## Opciones consideradas

1. **[Opción A, ej. API REST/HTTP]**
2. **[Opción B, ej. CLI que interactúa directamente con el proceso]**
3. **[Opción C, ej. Cola de mensajes (ej. RabbitMQ/Kafka) como interfaz]**

## Decisión

[PENDIENTE — se resolverá en Avance 1]

## Consecuencias

- **Positivas:** [pendiente]
- **Negativas / trade-offs:** [pendiente]
- **Impacto en otras áreas:** define el contrato que deberá cubrir la
  verificación (pruebas de integración) y la documentación de uso.
