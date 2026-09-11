# Cronograma inicial

## Hitos principales

| Hito | Fecha objetivo | Responsable | Estado |
|---|---|---|---|
| Arranque del proyecto (este entregable) | 11/09/2026 | Todos | En progreso |
| Avance 1 | 02/10/2026 | Josué Said Delgadillo Gutiérrez, Juan José Rentería Haro | Pendiente |
| Primeros 3 ADR resueltos | 09/10/2026 | Daniel Alejandro Huerta Camberos | Pendiente |
| Primera verificación / pruebas automatizadas | 16/10/2026 | Diego Armando Durán Hernández | Pendiente |
| Avance 2 | 30/10/2026 | Josué Said Delgadillo Gutiérrez, Daniel Alejandro Huerta Camberos | Pendiente |
| Entrega final | 01/12/2026 | Todos | Pendiente |

## Distribución de trabajo por semana (provisional)

| Semana | Foco principal | Integrantes involucrados |
|---|---|---|
| Semana 1 (11–17 sep) | Organización del equipo, repositorio, ADRs iniciales | Todos |
| Semana 2 (18–24 sep) | Definición de alcance y criterios de aceptación | Daniel Alejandro Huerta Camberos, Josué Said Delgadillo Gutiérrez |
| Semana 3 (25 sep–1 oct) | Diseño de arquitectura base (rumbo a Avance 1) | Josué Said Delgadillo Gutiérrez, Juan José Rentería Haro |
| Semana 4 (2–8 oct) | Resolución de los primeros 3 ADR | Daniel Alejandro Huerta Camberos, Josué Said Delgadillo Gutiérrez |
| Semana 5 (9–15 oct) | Preparación de verificación y pruebas automatizadas | Juan José Rentería Haro, Diego Armando Durán Hernández |
| Semana 6 (16–22 oct) | Ejecución de la primera verificación / pruebas automatizadas | Diego Armando Durán Hernández, Juan José Rentería Haro |
| Semana 7 (23–29 oct) | Implementación del núcleo del JobRunner (rumbo a Avance 2) | Josué Said Delgadillo Gutiérrez, Daniel Alejandro Huerta Camberos |
| Semana 8 (30 oct–5 nov) | Cierre de Avance 2 y ajustes de producto | Daniel Alejandro Huerta Camberos, Josué Said Delgadillo Gutiérrez |
| Semana 9 (6–12 nov) | Continuación de implementación e integración | Josué Said Delgadillo Gutiérrez, Diego Armando Durán Hernández |
| Semana 10 (13–19 nov) | Verificación final y pruebas de regresión | Juan José Rentería Haro, Diego Armando Durán Hernández |
| Semana 11 (20–26 nov) | Revisión general, documentación y criterios de aceptación finales | Daniel Alejandro Huerta Camberos, Diego Armando Durán Hernández |
| Semana 12 (27 nov–1 dic) | Cierre y entrega final | Todos |

## Riesgos identificados

| # | Riesgo | Probabilidad | Impacto | Mitigación | Dueño |
|---|---|---|---|---|---|
| 1 | Falta de experiencia previa con el stack elegido | Media | Alto | Capacitación inicial y prueba de concepto temprana en la Semana 1 | Josué Said Delgadillo Gutiérrez |
| 2 | Dependencia de una librería externa poco documentada | Media | Medio | Evaluar alternativas antes de comprometerse; documentar decisión en un ADR | Josué Said Delgadillo Gutiérrez |
| 3 | Disponibilidad limitada de algún integrante en ciertas fechas | Media | Medio | Redistribuir tareas con anticipación y avisar con al menos 3 días de margen | Diego Armando Durán Hernández |
| 4 | Criterios de aceptación ambiguos o cambiantes | Baja | Alto | Validar alcance y criterios de "hecho" con el responsable de producto antes de iniciar cada hito | Daniel Alejandro Huerta Camberos |
| 5 | Cobertura de pruebas insuficiente antes de la entrega | Media | Alto | Definir criterios de "hecho" desde el inicio y correr verificación incremental por semana | Juan José Rentería Haro |

## Dependencias conocidas

- El módulo de ejecución de jobs depende de que se resuelva el ADR sobre el modelo de persistencia.
- La API pública depende de que se defina el mecanismo de autenticación.
- La primera verificación (Semana 6) depende de que el diseño de arquitectura (Semana 3) y los ADR (Semana 4) estén resueltos.
- El Avance 2 depende de que la implementación del núcleo (Semana 7) esté funcionalmente completa.
- Agregar más según se identifiquen.
- La primera verificación (Semana 6) depende de que el diseño de arquitectura (Semana 3) y los ADR (Semana 4) estén resueltos.
- El Avance 2 depende de que la implementación del núcleo (Semana 7) esté funcionalmente completa.
- Agregar más según se identifiquen.
