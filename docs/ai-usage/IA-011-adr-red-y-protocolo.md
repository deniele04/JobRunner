# IA-011 — ADR-0008 y ADR-0009 (red y protocolo v1) y actualización de ADR-0003 y ADR-0007

| Campo | Valor |
|---|---|
| **Fecha** | 19/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josué Said Delgadillo Gutiérrez |
| **Revisado por** | Pendiente de revisión |
| **Hito** | Hito 3 — Operación remota privada |
| **Artefactos afectados** | `docs/decisions/0008-transporte-de-red-y-restriccion-de-acceso.md`, `docs/decisions/0009-protocolo-v1.md`, `docs/decisions/0003-mecanismo-de-comunicacion.md`, `docs/decisions/0007-solicitudes-duplicadas-desconexiones-y-clientes.md` |
| **Clasificación** | En revisión |

## 1. Objetivo

La lista de tareas de la entrega final asigna a Josué la tarea J1: redactar los ADR-0008 (transporte de red y restricción de acceso) y ADR-0009 (protocolo v1) y actualizar los ADR-0003 y ADR-0007. Se usó la IA para redactar los borradores a partir de las decisiones de la lista de tareas, comparando alternativas y relacionando cada riesgo con su prueba (RNF-34).

## 2. Entrada proporcionada

- La lista de tareas de Josué para la entrega final y la ruta crítica del equipo.
- Los ADR-0003 y ADR-0007 vigentes, el formato `template.md` y los requisitos del Hito 3 de la matriz de trazabilidad.
- El código actual del servidor (`server.py`), que atiende una conexión a la vez.

## 3. Resultado recibido

1. ADR-0008: TCP con el mismo JSON de una línea, `--listen` (por defecto `127.0.0.1:7070`), lista `--allow` en CIDR, rechazo de `0.0.0.0`, `::` y direcciones públicas, evento `acceso_rechazado` y Tailscale como VPN. Alternativas comparadas: HTTP, abrir el puerto en el router y token compartido.
2. ADR-0009: campo `v`, búfer hasta `\n`, 64 KiB por mensaje, 30 s de inactividad, varias solicitudes por conexión, `selectors`, y los comandos `output` y `health`.
3. Texto de actualización de los ADR-0003 y ADR-0007, aplicado con un script que falla si no encuentra el texto exacto.

## 4. Revisión realizada

- Se comprobó que cada riesgo tiene una mitigación y una prueba (TC-011, TC-012, TC-017, TC-023).
- Se comprobó el texto exacto que reemplaza el script contra los ADR vigentes.
- Pendiente: revisión del equipo y confirmar con Juan el formato de `output` y `health`, y con Daniel la guía de usuario.

## 5. Cambios aplicados

| Resultado de la IA | Decisión del equipo | Clasificación |
|---|---|---|
| ADR-0008 con TCP restringido por dirección y Tailscale | Pendiente de aprobación en el PR | En revisión |
| Token compartido descartado en este hito y dejado como decisión abierta | Pendiente de aprobación en el PR | En revisión |
| ADR-0009 con `selectors` en un solo hilo | Pendiente de aprobación en el PR | En revisión |
| Actualización de ADR-0003 y ADR-0007 | Pendiente de aprobación en el PR | En revisión |

## 6. Limitaciones del resultado de la IA

- Los ADR describen decisiones de diseño que todavía no están implementadas; su estado pasa a Aceptado cuando se aprueban en su PR.
- La decisión sobre el token compartido es una propuesta y debe confirmarse con el equipo.
- Los códigos RF y RNF se tomaron de la matriz de trazabilidad.
- La configuración de WSL se cerrará con la prueba de conexión entre equipos.

## 7. Prueba o verificación agregada

No se agregó código. Las pruebas que respaldan los ADR (TC-011, TC-012, TC-023) se escriben en la tarea J6.

**Verificó:** Josué Said Delgadillo Gutiérrez (19/11/2026)

## 8. Aprendizaje

- Un ADR de seguridad debe nombrar la restricción por defecto (escuchar solo en loopback) y negarse a arrancar con una configuración insegura.
- Conviene fijar los límites del protocolo (tamaño, inactividad) en el ADR antes de programar el servidor.
