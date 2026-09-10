#  Seriedad TaskOps — JobRunner

## Propósito

Seriedad TaskOps  es la implementación de un JobRunner (motor de ejecución y
orquestación de tareas/jobs) desarrollada por el equipo **[Seriedad]**
como proveedor de este servicio dentro del curso **[Sistemas Avanzados]**.

El objetivo del producto es permitir a clientes encolar, programar y monitorear la
ejecución de tareas asíncronas mediante una API HTTP".

## Integrantes

* Josue Said Delgadillo Gutierrez - josue.delgadillo6668@alumnos.udg.mx
* Diego Armando Duran Hernandez - diego.duran5597@alumnos.udg.mx
* Juan Jose Renteria Haro - juan.renteria6723@alumnos.udg.mx
* Daniel Alejandro Huerta Camberos - daniel.huerta7939@alumnos.udg.mx

Ver matriz completa de responsabilidades en [`docs/ROLES.md`](docs/ROLES.md).

## Estado del proyecto

**Fase actual:** Arranque / Avance 0 — organización del equipo y del repositorio.

- [x] Repositorio creado
- [x] Estructura mínima de carpetas
- [ ] Primer ADR resuelto
- [ ] Primer endpoint / módulo funcional
- [ ] Primera verificación (tests) ejecutándose en CI

## Construcción provisional

Dado que el proyecto se encuentra en la Fase de Arranque, el código fuente definitivo aún no ha sido implementado. 
Sin embargo, al ser un sistema diseñado para entornos Linux, la construcción y ejecución del proyecto se gestionará a través de herramientas estándar de terminal (como `make`).

**Comandos previstos para el flujo de trabajo:**
* **Compilación:** `make build` (para generar los binarios o preparar el entorno).
* **Ejecución:** `make run` (para levantar el proceso del JobRunner).
* **Pruebas:** `make test` (para ejecutar los casos de verificación).
* **Limpieza:** `make clean` (para eliminar archivos temporales).

*(Nota: Las tecnologias y herrmaientas pueden cambiar y formalizarse mas adelante en los ADRs del proyecto).*


## Estructura del repositorio (sujeto a cambios)

```
.
├── README.md
├── docs/
│   ├── ROLES.md            # Matriz de responsables/revisores
│   ├── CRONOGRAMA.md       # Cronograma inicial y riesgos/dependencias
│   └── adr/                # Architectural Decision Records
├── src/                    # Código fuente del JobRunner
├── tests/                  # Pruebas de verificación
├── scripts/                # Scripts de utilidad, build, despliegue
└── .github/ISSUE_TEMPLATE/ # Plantillas de Issues
```

## Documentación relacionada

- Matriz de roles: [`docs/ROLES.md`](docs/ROLES.md)
- Cronograma y riesgos: [`docs/CRONOGRAMA.md`](docs/CRONOGRAMA.md)
- Decisiones de arquitectura: [`docs/adr/`](docs/adr/)

## Licencia / Uso académico

Proyecto desarrollado con fines académicos para [Sistemas Avanzados / Centro Universitario de Ciencias Exactas e Ingenierías].
