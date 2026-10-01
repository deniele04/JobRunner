#  Seriedad TaskOps — JobRunner

## Propósito

Seriedad TaskOps  es la implementación de un JobRunner (motor de ejecución y
orquestación de tareas/jobs) desarrollada por el equipo **[Seriedad]**
como proveedor de este servicio dentro del curso **[Sistemas Avanzados]**.

El objetivo del producto es permitir a clientes encolar, programar y monitorear la
ejecución de tareas asíncronas mediante una API HTTP".

## Integrantes

| Integrante | Rol | GitHub |
|---|---|---|
| Daniel Alejandro Huerta Camberos | Producto | [@deniele04](https://github.com/deniele04) |
| Diego Armando Durán Hernández | Verificación | [@DiegoDuran07](https://github.com/DiegoDuran07) |
| Juan José Rentería Haro | Ingeniería | [@JJRNTH](https://github.com/JJRNTH) |
| Josué Said Delgadillo Gutiérrez | Ingeniería | [@josuesdg7105](https://github.com/josuesdg7105) |

Detalle de responsabilidades en [`project-management/ROLES.md`](project-management/ROLES.md).

## Arquitectura (resumen)

- **Servicio (`jobrunner.server`)**: proceso que recibe solicitudes, valida, asigna un ID a cada trabajo, lo ejecuta como proceso hijo y controla su ciclo de vida.
- **Cliente (`jobrunner.cli`)**: comandos `submit`, `status`, `list` y `cancel`.
- **Comunicación**: socket Unix con mensajes JSON de una línea ([ADR-0003](docs/decisions/0003-mecanismo-de-comunicacion.md)).
- **Estados de un trabajo**: `QUEUED → RUNNING → SUCCEEDED | FAILED | CANCELED`.
- **Persistencia**: SQLite, a partir del Hito 2 ([ADR-0002](docs/decisions/0002-modelo-de-persistencia.md)).

## Requisitos del entorno

- Linux (Ubuntu 22.04 / 24.04) o WSL2.
- Python 3.10 o superior.
- Sin dependencias externas: solo la biblioteca estándar de Python ([ADR-0001](docs/decisions/0001-lenguaje-y-runtime.md)).
- No requiere privilegios de root.

## Alcance actual

**Avance 1 — Núcleo local (en progreso):**
- [x] Repositorio, estructura, roles y cronograma
- [x] Plantillas de ADR e Issues
- [ ] ADR 0001–0003 aceptados
- [ ] Enviar un trabajo y obtener ID único
- [ ] Ejecutar como proceso separado
- [ ] Consultar estado, listar y cancelar
- [ ] Obtener código de salida
- [ ] Manejo de comandos inválidos sin terminar el servicio
- [ ] Pruebas y script de verificación

**Próximos hitos:** concurrencia, persistencia y recuperación (Hito 2); operación remota en LAN/VPN (Hito 3).
**Fuera de alcance:** interfaz web, acceso por Internet público y ejecución distribuida (ver Project Brief).

## Estructura del repositorio

```
.
├── README.md
├── src/                      # Código de producción
├── scripts/                  # setup.sh, run.sh, test.sh
├── docs/
│   ├── user-guide/           # Instalación y operación
│   ├── technical-guide/      # Arquitectura, protocolo, estados
│   ├── decisions/            # ADR (registros de decisiones)
│   ├── ai-usage/             # Registros de uso de IA
│   ├── change-requests/      # Solicitudes de cambio del cliente
│   └── incidents/            # Incidentes y su resolución
├── verif/
│   ├── verification-plan/    # Plan y matriz de trazabilidad
│   ├── test-cases/           # Casos TC-XXX
│   ├── scripts/              # Automatización de pruebas
│   ├── test-data/            # Datos controlados
│   └── results/              # Evidencia por ejecución
├── project-management/       # Roles, cronograma y minutas
└── .github/ISSUE_TEMPLATE/   # Plantillas de Issues
```

## Flujo de trabajo

- Cada integrante trabaja en su propia rama (`rama-<nombre>`).
- Todo cambio a `main` entra por Pull Request aprobado por los otros 3 integrantes.
- El trabajo se organiza en Issues conectados al GitHub Project del repositorio.

## Documentación

- Roles: [`project-management/ROLES.md`](project-management/ROLES.md)
- Cronograma y riesgos: [`project-management/CRONOGRAMA.md`](project-management/CRONOGRAMA.md)
- Decisiones de arquitectura: [`docs/decisions/`](docs/decisions/)
- Uso de IA: [`docs/ai-usage/`](docs/ai-usage/)

## Uso académico

Proyecto desarrollado con fines académicos para Programación de Sistemas Avanzados, Centro Universitario de Ciencias Exactas e Ingenierías (CUCEI), Universidad de Guadalajara.
