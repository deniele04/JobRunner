# Seriedad TaskOps — JobRunner

## Propósito

JobRunner es una plataforma ligera para **enviar, ejecutar, supervisar y controlar trabajos del sistema operativo en Linux**. Cada trabajo (un comando o programa con sus argumentos) se ejecuta como un proceso separado, controlado por un servicio local, y el usuario lo opera desde un cliente de línea de comandos.

Proyecto del equipo **Seriedad** para la materia **Programación de Sistemas Avanzados 2026B** (CUCEI, Universidad de Guadalajara).

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

## Construcción

Requiere Linux (o WSL2) y Python 3.10 o superior. El proyecto usa solo la biblioteca estándar de Python, por lo que **no hay `requirements.txt` ni paquetes que instalar con `pip`** ([ADR-0001](docs/decisions/0001-lenguaje-y-runtime.md)).

1. Verificar la versión de Python (debe ser 3.10 o superior):

   ```bash
   python3 --version
   ```

2. Clonar el repositorio:

   ```bash
   git clone https://github.com/deniele04/JobRunner.git
   cd JobRunner
   ```

3. *(Opcional)* Crear y activar un entorno virtual para aislar el intérprete. No es necesario para ejecutar el proyecto:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   En Ubuntu puede hacer falta instalar antes `python3-venv` (`sudo apt install python3-venv`).

4. Preparar el proyecto:

   ```bash
   ./scripts/setup.sh
   ```

   `setup.sh` verifica la versión de Python y compila el código para detectar errores.

Los scripts `setup.sh`, `run.sh` y `test.sh` reemplazan a los antiguos comandos `make build / make run / make test`, que ya no se usan.

## Ejecución

El servicio es un proceso propio de JobRunner (`jobrunner.server`), no un servidor web: no se usa `uvicorn` ni `flask run`. Se comunica con el cliente por un socket Unix ([ADR-0003](docs/decisions/0003-mecanismo-de-comunicacion.md)).

En una terminal (con el entorno virtual activado, si lo creaste), iniciar el servicio:

```bash
./scripts/run.sh
```

En otra terminal (activando también el entorno virtual, si lo usas), desde la raíz del repositorio, usar el cliente:

```bash
export PYTHONPATH=src
python3 -m jobrunner.cli submit -- sleep 10
python3 -m jobrunner.cli status <id>
python3 -m jobrunner.cli list
python3 -m jobrunner.cli cancel <id>
python3 -m jobrunner.cli --help
```

Para detener el servicio: `Ctrl+C`.

> El servicio y el cliente están en desarrollo; los comandos se confirmarán al integrar su código.

## Pruebas

```bash
./scripts/test.sh
```

Ejecuta las pruebas unitarias (`verif/unit/`, con `unittest` de la biblioteca estándar; no se usa `pytest`) y el script de verificación (`verif/scripts/verify.sh`). La evidencia de cada ejecución se guarda en `verif/results/<run-id>/`.

## Alcance actual

**Avance 1 — Núcleo local (en progreso):**
- [x] Repositorio, estructura, roles y cronograma
- [x] Plantillas de ADR e Issues
- [x] ADR 0001–0003 aceptados
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
