# Seriedad TaskOps — JobRunner

## Propósito

JobRunner es una plataforma ligera para **enviar, ejecutar, supervisar y controlar trabajos del sistema operativo en Linux**. Cada trabajo (un comando o programa con sus argumentos) se ejecuta como un proceso separado, controlado por un servicio, y el usuario lo opera desde un cliente de línea de comandos, en la misma computadora o desde otro equipo de una red privada o VPN.

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

- **Servicio (`jobrunner.server`)**: recibe solicitudes, valida, asigna un ID a cada trabajo, lo ejecuta como proceso hijo con cola y límite de concurrencia, y controla su ciclo de vida (`executor.py`).
- **Red (`red.py`)**: atiende varias conexiones a la vez en un solo hilo con `selectors`, por el socket Unix local y, con `--listen`, por TCP restringido a redes privadas o a la VPN ([ADR-0008](docs/decisions/0008-transporte-de-red-y-restriccion-de-acceso.md)).
- **Protocolo v1**: un objeto JSON por línea, con el campo de versión `"v": 1`, máximo 64 KiB por mensaje y cierre por 30 s de inactividad ([ADR-0009](docs/decisions/0009-protocolo-v1.md)).
- **Cliente (`royito`, módulo `jobrunner.cli`)**: comandos `submit`, `status`, `list`, `cancel`, `output` y `health`, por el socket Unix local o por TCP con `--host` y `--port`.
- **Estados de un trabajo**: `QUEUED → RUNNING → SUCCEEDED | FAILED | CANCELED`.
- **Persistencia**: SQLite en `data/jobrunner.db`, con recuperación al arrancar ([ADR-0002](docs/decisions/0002-modelo-de-persistencia.md), [ADR-0005](docs/decisions/0005-recuperacion-al-arrancar.md)).
- **Bitácora**: un evento por línea en `data/jobrunner.log` ([bitacora.md](docs/user-guide/bitacora.md)).

Detalle en la [guía técnica](docs/technical-guide/).

## Requisitos del entorno

- Linux (Ubuntu 22.04 / 24.04) o WSL2.
- Python 3.10 o superior.
- Sin dependencias externas: solo la biblioteca estándar de Python ([ADR-0001](docs/decisions/0001-lenguaje-y-runtime.md)).
- No requiere privilegios de root.
- Para la operación entre equipos: Tailscale o una LAN privada.

## Construcción

```bash
python3 --version                 # 3.10 o superior
git clone https://github.com/deniele04/JobRunner.git
cd JobRunner
./scripts/setup.sh                # verifica Python y compila el código; termina con "Construcción OK"
```

En WSL, clona el repositorio dentro de tu carpeta personal (`~`), no en `/mnt/c/...`.

## Ejecución

### En la misma computadora

En una terminal, iniciar el servicio:

```bash
./scripts/run.sh                          # 3 trabajos a la vez y 10 en cola
./scripts/run.sh --max-jobs 2 --queue-size 5
```

En otra terminal, desde la raíz del repositorio, usar el cliente `royito` (se prepara una sola vez por terminal):

```bash
export PATH="$PWD/scripts:$PATH"
royito submit -- sleep 10
royito status <id>
royito list
royito cancel <id>
royito output <id>
royito health
royito --help
```

`royito` es un lanzador de `scripts/royito`; equivale a `PYTHONPATH=src python3 -m jobrunner.cli`.

### Desde otro equipo (LAN privada o VPN)

En el servidor, con su IP de Tailscale y la IP del cliente:

```bash
./scripts/run.sh --listen 100.101.102.103:7070 --allow 100.90.80.70/32
```

En el cliente:

```bash
royito --host 100.101.102.103 --port 7070 list
```

También se pueden usar las variables `JOBRUNNER_HOST` y `JOBRUNNER_PORT`. El servicio se niega a escuchar en `0.0.0.0` o en direcciones públicas, solo atiende por TCP a las redes de `--allow` y cierra las demás conexiones. Pasos completos en [conexion-lan-vpn.md](docs/user-guide/conexion-lan-vpn.md).

### Detener

`Ctrl+C` o `SIGTERM`. El cierre es controlado: deja de aceptar conexiones, cierra las abiertas y libera el puerto, cancela los trabajos en ejecución, conserva la cola para el siguiente arranque y elimina el socket. Un segundo `Ctrl+C` fuerza el cierre inmediato.

## Pruebas

```bash
./scripts/test.sh
```

Ejecuta las pruebas unitarias (`verif/unit/`), las de integración con servidor, red y CLI reales (`verif/integration/`), ambas con `unittest`, y el script de verificación (`verif/scripts/verify.sh`). La evidencia de cada ejecución se guarda en `verif/results/<run-id>/`.

Para buscar procesos zombis y huérfanos tras una prueba: `verif/scripts/procesos.sh` (ver el [Plan de Verificación](verif/verification-plan/plan-de-verificacion.md)).

## Alcance

**Avance 1 — Núcleo local (`v0.1.0`):** enviar un trabajo con ID único, ejecutarlo como proceso separado, consultar, listar, cancelar, código de salida y manejo de comandos inválidos sin terminar el servicio.

**Avance 2 — Concurrencia y persistencia (`v0.2.0`):** cola con límite configurable y rechazo con cola llena, cancelación sin bloqueo con escalamiento a SIGKILL, persistencia en SQLite, recuperación al arrancar, solicitudes duplicadas, cierre controlado y bitácora de eventos.

**Entrega final — Operación remota privada (`v1.0.0`):**
- [x] Servidor TCP con varios clientes a la vez, mensajes fragmentados, límite de 64 KiB e inactividad de 30 s
- [x] Restricción de acceso: `--listen` solo en direcciones privadas o de la VPN, `--allow` y evento `acceso_rechazado`
- [x] `request_id` con aviso de duplicado y rechazo de otro comando (ADR-0007)
- [x] Versión del protocolo (`"v": 1`) y error de versión no soportada
- [x] Cierre controlado con TCP: conexiones cerradas y puerto liberado
- [x] Cliente remoto (`--host`, `--port`, `JOBRUNNER_HOST`, `JOBRUNNER_PORT`)
- [x] Comandos `output` (salida de un trabajo) y `health` (resumen de salud)
- [x] Operación verificada entre dos equipos por VPN (`verif/results/20261123-remoto/`)

No se implementó ningún Change Request ni se hizo verificación cruzada con otro equipo; las excepciones de `v1.0.0` están en las [release notes](docs/release-notes.md).

**Fuera de alcance:** interfaz web, acceso por Internet público, autenticación de usuarios y ejecución distribuida (ver Project Brief).

## Estructura del repositorio

```
.
├── README.md
├── src/jobrunner/            # Código: server, red, executor, store, jobs, bitacora, cli
├── scripts/                  # setup.sh, run.sh, test.sh, royito
├── docs/
│   ├── user-guide/           # Guía de usuario, conexión LAN/VPN, bitácora y diagnóstico
│   ├── technical-guide/      # Arquitectura, protocolo, estados
│   ├── decisions/            # ADR (registros de decisiones)
│   ├── ai-usage/             # Registros de uso de IA y AI-LOG
│   ├── change-requests/      # Solicitudes de cambio del cliente
│   ├── incidents/            # Incidentes y su resolución
│   ├── defectos-y-limitaciones.md
│   └── release-notes.md
├── verif/
│   ├── verification-plan/    # Plan y matriz de trazabilidad
│   ├── test-cases/           # Casos TC-XXX
│   ├── scripts/              # verify.sh, procesos.sh, inspecciones.py y automatización
│   ├── inspecciones/         # Inspecciones de RNF-16, RNF-17, RNF-18 y RNF-34
│   ├── manual/               # Registro manual de TC-015
│   ├── unit/, integration/   # Pruebas automatizadas
│   └── results/              # Evidencia por ejecución (incluida la remota)
├── project-management/       # Roles, cronograma, minutas y participación
└── .github/ISSUE_TEMPLATE/   # Plantillas de Issues
```

## Flujo de trabajo

- Cada integrante trabaja en su propia rama (`rama-<nombre>`).
- Todo cambio a `main` entra por Pull Request aprobado por los otros 3 integrantes, con `Closes #N`.
- Antes de abrir un PR se actualiza la rama con `main` y se corre `./scripts/test.sh`.
- El trabajo se organiza en Issues conectados al GitHub Project del repositorio.

## Documentación

| Documento | Ubicación |
|---|---|
| Guía de usuario | [`docs/user-guide/guia-de-usuario.md`](docs/user-guide/guia-de-usuario.md) |
| Conexión entre dos equipos | [`docs/user-guide/conexion-lan-vpn.md`](docs/user-guide/conexion-lan-vpn.md) |
| Bitácora de eventos | [`docs/user-guide/bitacora.md`](docs/user-guide/bitacora.md) |
| Guía de diagnóstico | [`docs/user-guide/diagnostico.md`](docs/user-guide/diagnostico.md) |
| Guía técnica | [`docs/technical-guide/`](docs/technical-guide/) |
| Decisiones de arquitectura (ADR) | [`docs/decisions/`](docs/decisions/) |
| Defectos y limitaciones | [`docs/defectos-y-limitaciones.md`](docs/defectos-y-limitaciones.md) |
| Incidentes | [`docs/incidents/`](docs/incidents/README.md) |
| Release notes | [`docs/release-notes.md`](docs/release-notes.md) |
| Plan de verificación y matriz | [`verif/verification-plan/`](verif/verification-plan/) |
| Uso de IA | [`docs/ai-usage/AI-LOG.md`](docs/ai-usage/AI-LOG.md) |
| Roles, cronograma y riesgos | [`project-management/`](project-management/) |

## Uso académico

Proyecto desarrollado con fines académicos para Programación de Sistemas Avanzados, Centro Universitario de Ciencias Exactas e Ingenierías (CUCEI), Universidad de Guadalajara.
