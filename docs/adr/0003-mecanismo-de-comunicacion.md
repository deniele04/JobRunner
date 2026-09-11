# ADR-0003: Mecanismo de comunicación del JobRunner

**Estado:** Propuesto
**Fecha:** 11/09/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez

## Contexto

Los clientes del JobRunner necesitan poder encolar nuevos jobs, consultar su
estado y obtener resultados de ejecución. Se requiere definir el mecanismo por
el cual el sistema expone estas operaciones hacia el exterior.

## Opciones consideradas

1. **API REST sobre HTTP** — Estándar ampliamente conocido por el equipo,
   fácil de documentar y probar (Postman, curl), buen soporte en Python
   (FastAPI/Flask), y encaja de forma natural con operaciones CRUD sobre
   jobs (crear, consultar, cancelar).
2. **Colas de mensajes (ej. RabbitMQ/Redis)** — Mejor para desacoplar
   productores y consumidores a gran escala, pero agrega complejidad de
   infraestructura innecesaria para el alcance del curso.
3. **gRPC** — Alto rendimiento y contratos tipados, pero curva de aprendizaje
   más alta para el equipo y menos práctico para pruebas manuales rápidas
   durante el desarrollo.

## Decisión

Se elige una **API REST sobre HTTP** como mecanismo de comunicación principal
del JobRunner, por la familiaridad del equipo con el estándar, la facilidad
para documentar y probar los endpoints, y su compatibilidad directa con
Python (ADR-0001) y el modelo de persistencia SQL (ADR-0002).

## Consecuencias

- **Positivas:** fácil de consumir por cualquier cliente HTTP, buena curva de
  aprendizaje para el equipo, ecosistema maduro de herramientas de prueba y
  documentación (Swagger/OpenAPI).
- **Negativas / trade-offs:** menos eficiente que alternativas binarias
  (gRPC) para volúmenes muy altos de jobs; el manejo de operaciones de larga
  duración requiere diseño adicional (polling o webhooks) ya que HTTP es
  request/response.
- **Impacto en otras áreas:** depende del lenguaje elegido (ADR-0001);
  define cómo se exponen las consultas de estado almacenadas en la base de
  datos (ADR-0002).