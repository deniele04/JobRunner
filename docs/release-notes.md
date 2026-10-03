# Release Notes — JobRunner

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
