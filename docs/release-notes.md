# Release Notes — JobRunner

## v0.2.0 — Avance 2: Concurrencia y persistencia

**Fecha:** 30/10/2026
**Equipo:** Seriedad

### Funciones incluidas

- Cola de trabajos FIFO: los trabajos que no caben esperan en `QUEUED` y arrancan en orden de llegada (RF-03, ADR-0004).
- Límite configurable de trabajos simultáneos (`--max-jobs`, por defecto 3) y tamaño de la cola (`--queue-size`, por defecto 10) (RF-05, ADR-0004).
- Rechazo explícito cuando la cola está llena: `{"error": "cola llena (capacidad N); intenta más tarde"}`, sin registrar el trabajo (RF-25).
- Salida estándar y de errores en archivos separados (`data/<id>.out` y `data/<id>.err`) (RF-11).
- Estados y tiempos de cada trabajo: `created_at`, `started_at` (cuando sale de la cola) y `finished_at`, con transiciones validadas (RF-06, RF-07).
- Cancelación de trabajos en cola y en ejecución sin bloquear al servidor: un trabajo en cola pasa a `CANCELED` al instante; uno en ejecución recibe SIGTERM y la respuesta llega de inmediato (RF-10, ADR-0006).
- Política de escalamiento: si el trabajo sigue vivo 5 s después de SIGTERM, se envía SIGKILL a su grupo de procesos (RF-30, ADR-0006).
- Persistencia de los metadatos de cada trabajo en SQLite (`data/jobrunner.db`) (RF-12, ADR-0002).
- Recuperación al reiniciar: el historial se conserva, los `QUEUED` vuelven a la cola y los que estaban en `RUNNING` quedan `FAILED` «interrumpido por reinicio», con su grupo de procesos terminado (RF-13, ADR-0005).
- Bitácora de eventos en `data/jobrunner.log`, correlacionada por ID de trabajo y sin argumentos de los trabajos (RF-14).
- Solicitudes concurrentes o duplicadas: atención secuencial con transiciones validadas, `request_id` opcional para no crear el mismo trabajo dos veces y doble cancelación con un solo estado final (RF-26, RF-27, ADR-0007).
- Liberación de procesos, archivos y sockets: revisión de procesos cada 0,5 s (sin zombis) y cierre controlado con Ctrl+C o SIGTERM que cancela los trabajos en ejecución, conserva la cola y elimina el socket (RF-15, RF-29, RNF-25, RNF-30, RNF-33, ADR-0006).
- Robustez: una desconexión del cliente o un mensaje con bytes inválidos ya no terminan el servicio (RNF-08, INC-001).
- Comando `royito` (`scripts/royito`) para usar el cliente sin configurar `PYTHONPATH`; el comando largo `python3 -m jobrunner.cli` sigue funcionando (RF-17).

### Cómo reproducir

    git clone https://github.com/deniele04/JobRunner.git
    cd JobRunner
    ./scripts/setup.sh
    ./scripts/test.sh                                   # pruebas y evidencia en verif/results/

En una terminal:

    ./scripts/run.sh --max-jobs 2 --queue-size 1

En otra terminal (`export PATH="$PWD/scripts:$PATH"` habilita el comando `royito`):

    royito submit -- sleep 60                           # 1.º y 2.º: RUNNING
    royito submit -- sleep 60
    royito submit -- sleep 60                           # 3.º: QUEUED
    royito submit -- sleep 60                           # 4.º: cola llena
    royito list
    royito cancel <id>                                  # responde RUNNING; pasa a CANCELED
    kill -9 <pid de un trabajo>                         # el trabajo queda FAILED con error SIGKILL
    verif/scripts/procesos.sh revisar --patron 'sleep'  # zombis o huérfanos
    cat data/jobrunner.log

Para la recuperación: detener el servidor con `kill -9`, volver a ejecutar `./scripts/run.sh` y consultar `list`.

### Verificación

- 104 pruebas unitarias y 49 de integración, todas en PASS.
- Casos de prueba del Avance 2 en `verif/test-cases/`: TC-002, TC-005, TC-007, TC-009, TC-016 a TC-022, TC-024 y TC-025.
- Matriz de trazabilidad en `verif/verification-plan/matriz-trazabilidad.md`.
- Ejecución formal: `verif/results/20261030-v0.2.0/` sobre el commit `ab33847`, incluida la revisión de zombis y huérfanos (`procesos.log`).

### Documentación

- ADR-0004 (cola y concurrencia), ADR-0002 (persistencia), ADR-0005 (recuperación), ADR-0006 (cancelación, escalamiento y cierre) y ADR-0007 (solicitudes duplicadas y desconexiones).
- Guía técnica (`docs/technical-guide/`): arquitectura, modelo de estados, protocolo y persistencia.
- Guía de usuario (`docs/user-guide/`) y bitácora de eventos.
- Incidente técnico INC-001 (`docs/incidents/`).
- AI-LOG (`docs/ai-usage/AI-LOG.md`), cronograma y registro de riesgos (`project-management/CRONOGRAMA.md`).

### Resuelto en esta versión

- DEF-003: el CLI terminaba con código 1 en operaciones exitosas (PR #51).
- DEF-004: los trabajos terminados quedaban como zombis hasta la siguiente consulta (PR #66).
- INC-001: el servidor terminaba si un cliente se desconectaba o enviaba bytes inválidos (PR #51).
- Issue #37: `cancel()` bloqueaba al servidor hasta 5 s con un trabajo que ignora SIGTERM (PR #67).
- Limitaciones de la v0.1.0: ahora hay persistencia, cola y límite de concurrencia.

### Limitaciones conocidas

- Solo operación local; el acceso remoto en LAN/VPN se implementa en el Hito 3 (ADR-0003).
- Un trabajo que terminó justo antes de una caída del servicio queda `FAILED` «interrumpido por reinicio», porque su resultado no alcanzó a guardarse (ADR-0005).
- El servicio atiende a un cliente a la vez (ADR-0007): un cliente que se conecta y no envía nada retrasa a los demás hasta 5 s.

## v0.1.0 — Avance 1: Núcleo local

**Fecha:** 02/10/2026
**Equipo:** Seriedad

### Funciones incluidas

- Enviar un trabajo (comando con argumentos) y obtener un identificador único (RF-01).
- Validar y rechazar entradas vacías o mal formadas con un mensaje claro (RF-02).
- Ejecutar cada trabajo como un proceso separado, en su propio grupo de procesos (RF-04).
- Estados QUEUED, RUNNING, SUCCEEDED, FAILED y CANCELED, con transiciones validadas (RF-06).
- Registro de tiempos de inicio y fin, y del código de salida (RF-07).
- Consultar el estado de un trabajo por ID (RF-08) y listar trabajos con filtro por estado (RF-09).
- Cancelar un trabajo: SIGTERM al grupo de procesos y, si no termina en 5 s, SIGKILL (RF-10, RF-30).
- Salida estándar y de errores guardadas en archivos separados (RF-11).
- Cliente de línea de comandos con ayuda y códigos de salida para éxito y error (RF-17).
- Un comando inválido o un mensaje mal formado no terminan el servicio (RNF-08).

### Cómo reproducir

    git clone https://github.com/deniele04/JobRunner.git
    cd JobRunner
    ./scripts/setup.sh
    ./scripts/run.sh                    # en una terminal
    export PYTHONPATH=src               # en otra terminal
    python3 -m jobrunner.cli submit -- sleep 10
    python3 -m jobrunner.cli list
    ./scripts/test.sh                   # pruebas y evidencia en verif/results/

### Verificación

- 12 pruebas unitarias en `verif/unit/`, todas en PASS.
- Casos de prueba en `verif/test-cases/` y matriz en `verif/verification-plan/`.
- Evidencia de ejecución en `verif/results/`.

### Resuelto en esta versión

- IDs de trabajo que podían repetirse: ahora se usa el UUID completo.
- La cancelación forzada (SIGKILL) ahora se envía a todo el grupo de procesos, sin dejar procesos huérfanos.
- Validación de argumentos que no son texto.
- Un cliente conectado al socket sin enviar datos ya no bloquea el servidor: la lectura tiene un tiempo límite de 5 segundos (issue #35).
- El CLI termina con código de salida 1 cuando la respuesta es un error, y 0 cuando la operación fue exitosa (RF-17, issue #36).

### Limitaciones conocidas

- **Cancelación de un trabajo que ignora SIGTERM:** el servidor, de un solo hilo, deja de atender otras solicitudes hasta 5 s mientras espera para enviar SIGKILL. Queda como deuda para el Hito 2 (issue #37).
- **Sin persistencia:** los trabajos se pierden al reiniciar el servicio. SQLite se implementa en el Hito 2 (ADR-0002).
- **Sin cola ni límite de concurrencia:** todos los trabajos se ejecutan de inmediato. Se implementa en el Hito 2.
- **Solo operación local:** el acceso remoto en LAN/VPN se implementa en el Hito 3 (ADR-0003).
