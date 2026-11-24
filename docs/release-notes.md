# Release Notes — JobRunner

## v1.0.0 — Entrega final: operación remota privada

**Fecha:** 23/11/2026
**Equipo:** Seriedad

### Funciones incluidas

- Servicio accesible por TCP además del socket Unix local, con el mismo protocolo y los mismos comandos (`--listen HOST:PUERTO`; sin `--listen` no se abre ningún puerto) (RF-18, RF-19, ADR-0008).
- Varios clientes a la vez en un solo hilo con `selectors`: mensajes fragmentados, varias solicitudes por conexión, límite de 64 KiB por mensaje y cierre por 30 s de inactividad; un cliente lento no detiene a los demás (RF-21, RF-22, RNF-14, RNF-24, ADR-0009).
- Restricción de acceso: el servicio se niega a escuchar en `0.0.0.0`, `::` o direcciones públicas; `--allow RED` (CIDR, repetible) define los orígenes permitidos; una conexión no autorizada se cierra y queda `acceso_rechazado` en la bitácora (RF-20, RNF-12, RNF-13, ADR-0008).
- Versión del protocolo: toda respuesta lleva `"v": 1` y una versión distinta recibe un error claro (RNF-32, ADR-0009).
- Cliente remoto: `royito --host --port` o las variables `JOBRUNNER_HOST` y `JOBRUNNER_PORT`, con mensajes claros si no conecta o si la IP no está permitida (RF-18, RF-19, RF-17).
- `royito output <id>`: la salida de un trabajo (últimos 64 KiB, `--stderr`, `--raw`) (ADR-0009).
- `royito health`: versión, tiempo activo, trabajos por estado, límites, base de datos, clientes conectados y accesos rechazados (RF-16, RF-24).
- Mensajes de error del cliente con operación, causa y qué hacer (RF-17, RNF-21).
- `request_id` según el ADR-0007: el mismo comando devuelve el trabajo existente con `"duplicado": true`; otro comando con el mismo `request_id` se rechaza (RF-27).
- Cierre controlado con TCP: deja de aceptar conexiones, cierra las abiertas, libera el puerto y cancela los trabajos en ejecución (RF-15, RNF-25, ADR-0006).
- Un solo servicio por carpeta de datos: un segundo servicio sobre la misma carpeta se niega a arrancar (candado `jobrunner.lock`) (RF-15, RNF-08).

### Cómo reproducir

    git clone https://github.com/deniele04/JobRunner.git
    cd JobRunner
    ./scripts/setup.sh
    ./scripts/test.sh                                   # pruebas y evidencia en verif/results/

En el equipo servidor (IP de Tailscale o privada):

    ./scripts/run.sh --listen <IP del servidor>:7070 --allow <IP del cliente>/32

En el equipo cliente (`export PATH="$PWD/scripts:$PATH"` habilita `royito`):

    export JOBRUNNER_HOST=<IP del servidor>
    export JOBRUNNER_PORT=7070
    royito health
    royito submit -- sh -c 'echo hola'
    royito list
    royito output <id>
    royito cancel <id>

Pasos completos de la red en `docs/user-guide/conexion-lan-vpn.md`.

### Verificación

- Ejecución formal: `verif/results/<<RUN-ID>>/` sobre el commit `<<COMMIT>>`, con `verify.sh` en WSL.
- <<N UNITARIAS>> pruebas unitarias y <<N INTEGRACIÓN>> de integración, todas en PASS.
- Casos de prueba TC-001 a TC-026 e inspecciones INS-016, INS-017, INS-018 e INS-034 (RNF-16, RNF-17, RNF-18 y RNF-34), todos en `PASS` salvo TC-015, que queda `BLOCKED` (ver Excepciones); el estado de cada uno está en el `resumen.md` de la ejecución formal.
- Matriz de trazabilidad completa en `verif/verification-plan/matriz-trazabilidad.md`: los 30 RF y los 34 RNF con su caso o inspección.
- Operación entre dos equipos por la VPN Tailscale en `verif/results/20261123-remoto/` (servidor y cliente en computadoras distintas; pruebas P1 a P6 en PASS, salvo P4, que no aplicó por haber un solo cliente). La evidencia se revisa con `verif/scripts/revisar_evidencia_remota.py 20261123` (`verif/revision-cruzada/EVIDENCIA-REMOTA.md`).
- Revisión de zombis y huérfanos al final de las pruebas (`procesos.log`), también válida en WSL (DEF-005).

### Documentación

- ADR-0008 (transporte de red y restricción de acceso) y ADR-0009 (protocolo v1), y actualización de ADR-0003 y ADR-0007.
- Guía técnica: arquitectura, modelo de estados, protocolo v1 y persistencia, y seguridad (modelo de amenazas).
- Guía de usuario con la operación remota, instructivo de conexión entre equipos (`conexion-lan-vpn.md`), bitácora con los eventos de red y guía de diagnóstico.
- Defectos y limitaciones (`docs/defectos-y-limitaciones.md`) e índice de incidentes (`docs/incidents/`).
- Plan de verificación final, inspecciones y registro manual de TC-015.
- AI-LOG, cronograma y riesgos, minutas de la entrega final y participación del equipo (`project-management/participacion.md`).

### Resuelto en esta versión

- DEF-005: `procesos.sh` no detectaba huérfanos en WSL (PR #101).
- DEF-006: el mensaje de cancelar un ID inexistente salía entre comillas (PR #110).
- DEF-007: un estado inválido en `list --state` respondía «error interno» (PR #110).
- DEF-008: un segundo servidor con la misma carpeta `data/` tomaba el socket del primero y marcaba sus trabajos como interrumpidos; ahora se niega a arrancar (PR #117).
- Limitaciones de la v0.2.0: ya hay operación remota en LAN/VPN, y un cliente que se conecta sin enviar nada ya no retrasa a los demás.

### Excepciones

| Excepción | Motivo | Qué se hizo en su lugar |
|---|---|---|
| TC-015 queda `BLOCKED` (RF-17, RNF-21 y RNF-23): falta la evaluación manual de la guía por una persona ajena a ella | No se coordinó a tiempo una persona de otro equipo para evaluarla | Su parte automática pasa (ayuda, códigos de salida y mensajes de error). Diego coordina la evaluación con otro equipo después de la entrega (`verif/manual/TC-015.md`) |
| El Change Request [CR-001](change-requests/CR-001-token-compartido.md) (token compartido) no se implementó | Se analizó al cierre: cambiaba el protocolo y obligaba a repetir la ejecución formal y la prueba entre dos equipos | Análisis de impacto en el CR-001; queda aplazado y como limitación |

### Limitaciones conocidas

- El servicio no autentica personas ni cifra los mensajes: el acceso se limita por red de origen y el cifrado entre equipos lo da Tailscale (ADR-0008). El token compartido está analizado y aplazado ([CR-001](change-requests/CR-001-token-compartido.md)).
- Solo se aceptan direcciones IPv4 de Tailscale (`100.x`); las IPv6 de Tailscale no están permitidas.
- Un trabajo que terminó justo antes de una caída del servicio queda `FAILED` «interrumpido por reinicio» (ADR-0005).
- La lista completa, con su justificación, está en `docs/defectos-y-limitaciones.md`.

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
