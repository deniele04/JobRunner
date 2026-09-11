# ADR-0002: Modelo de persistencia de jobs y su estado

**Estado:** Propuesto
**Fecha:** [DD/MM/AAAA]
**Responsable(s):** [Nombre]

## Contexto

El JobRunner necesita almacenar el estado de cada job (encolado, en ejecución,
completado, fallido, reintentando) de forma que sobreviva a reinicios del
proceso y permita consultas de estado por parte de clientes.

## Opciones consideradas

1. **[Opción A, ej. Base de datos relacional (PostgreSQL/SQLite)]**
2. **[Opción B, ej. Almacén clave-valor (Redis)]**
3. **[Opción C, ej. Persistencia en archivo/embedded DB]**

## Decisión

[PENDIENTE — se resolverá en Avance 1]

## Consecuencias

- **Positivas:** [pendiente]
- **Negativas / trade-offs:** [pendiente]
- **Impacto en otras áreas:** afecta el diseño del módulo de verificación
  (pruebas de persistencia) y la estrategia de despliegue.
