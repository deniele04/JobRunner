# Release Notes — JobRunner

## Avance 1 — Nucleo local

### Resuelto

- Un cliente conectado al socket sin enviar datos ya no bloquea el servidor indefinidamente: la lectura tiene un tiempo limite de 5 segundos (ver issue #35).

- El CLI ahora termina con codigo de salida 1 cuando la respuesta del servidor contiene un error, y con 0 cuando la operacion fue exitosa (RF-17, ver issue #36).

### Limitaciones conocidas

- **Cancelacion de un trabajo que ignora SIGTERM:** JobManager.cancel() envia SIGTERM y espera hasta 5 segundos antes de escalar a SIGKILL. Durante esa espera, el servidor (de un solo hilo en este avance) no atiende otras solicitudes. El impacto es una demora temporal de hasta 5s en ese caso puntual; no se resuelve en este avance y queda como deuda para el Hito 2, donde se evaluara junto con el manejo de concurrencia (ver issue #37).

