# CR-001 — Token compartido como segunda capa de acceso

| Campo | Valor |
|---|---|
| **Origen** | Equipo: decisión abierta del [ADR-0008](../decisions/0008-transporte-de-red-y-restriccion-de-acceso.md) y limitación «sin autenticación de personas» de la [guía de seguridad](../technical-guide/seguridad.md) |
| **Propuso** | Daniel Alejandro Huerta Camberos (Producto) |
| **Estado** | Analizado y aplazado: no se implementa en `v1.0.0` |

## 1. Cambio solicitado

Además de `--allow`, el servicio puede exigir un token compartido a los clientes remotos:

- El servidor se inicia con `--token-file RUTA`, un archivo con el token que solo puede leer su dueño.
- El cliente lo envía con `--token-file RUTA` o con la variable `JOBRUNNER_TOKEN`.
- Cada solicitud por TCP lleva el campo `"token"`. Si falta o no coincide, el servicio responde un error, no ejecuta nada y registra `acceso_rechazado` con el motivo `token`.
- El socket Unix local no pide token: ya lo protegen los permisos del archivo.

## 2. Motivo

Hoy quien llegue desde una red permitida puede ejecutar comandos en el servidor (ADR-0008, sección de consecuencias). Con Tailscale, eso incluye cualquier equipo de la misma red de Tailscale que esté en `--allow`. El token agrega una segunda condición: estar en la red permitida **y** conocer el token.

## 3. Análisis de impacto

| Área | Impacto |
|---|---|
| Requisitos | RF-20 y RNF-13 (acceso remoto restringido): cambia su criterio de aceptación. RF-19 (misma semántica local y remota): el remoto pide token y el local no, y hay que documentarlo. RNF-12 y RNF-26 no cambian |
| Decisiones | ADR-0008: la decisión abierta pasa a decidida. ADR-0009: campo opcional `"token"` en el protocolo v1 (compatible con los clientes actuales mientras el servidor no exija token) |
| Módulos | `red.py` (validar el token en cada solicitud TCP, con `hmac.compare_digest`), `server.py` (opción `--token-file` y lectura del archivo), `cli.py` (opción y variable de entorno), bitácora (motivo `token`; el token nunca se escribe). `red.py` tiene 332 líneas y el límite de INS-017 es 400 |
| Casos de prueba | TC-011 (acceso por red) y TC-010 (flujo remoto) se amplían. Caso nuevo TC-027: sin token, token incorrecto y token correcto, y que el token no aparezca en la bitácora ni en `health`. Hay que repetir la evidencia entre dos equipos (`verif/results/<run-id>-remoto/`) |
| Documentos | Guía de usuario, instructivo de conexión entre equipos, guía de seguridad (INS-016), guía del protocolo y matriz de trazabilidad |
| Riesgos | En una LAN sin VPN el token viaja sin cifrar, así que solo sirve como segunda capa y no reemplaza a Tailscale. El token puede filtrarse si se pasa en la línea de comandos (se ve en `ps` y en el historial): por eso se lee de un archivo o de una variable. Una comparación que no sea de tiempo constante permitiría adivinarlo |
| Esfuerzo estimado | Un día de una persona para el código y las pruebas, y medio día para la documentación, en tres PR (servidor, cliente y documentos). Después, repetir la ejecución formal y la prueba entre dos equipos |

## 4. Decisión

**Aplazado para después de `v1.0.0`.** Se analizó al cierre de la entrega final. Implementarlo cambiaba el protocolo y obligaba a repetir la ejecución formal y la evidencia entre dos equipos. El control por red con Tailscale ya cumple RF-20, RNF-13 y RNF-26.

Mientras tanto queda como limitación en las release notes de `v1.0.0`: el servicio no autentica personas.
