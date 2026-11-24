# IA-019 — Planeación de la entrega final, revisión de PR y documentación de usuario, defectos y diagnóstico

| Campo | Valor |
|---|---|
| **Fecha** | 23/11/2026 (uso desde la planeación de la entrega final) |
| **Herramienta** | Claude |
| **Usado por** | Daniel Alejandro Huerta Camberos |
| **Revisado por** | Pendiente de revisión |
| **Hito** | Hitos 3 y 4 — Operación remota y candidato de entrega |
| **Artefactos afectados** | `project-management/minutas/` (minutas 1 a 4 de la entrega final), `project-management/participacion.md`, `docs/release-notes.md` (v1.0.0), `README.md`, `docs/user-guide/guia-de-usuario.md`, `project-management/CRONOGRAMA.md`, `docs/user-guide/conexion-lan-vpn.md`, `docs/user-guide/bitacora.md`, `docs/user-guide/diagnostico.md`, `docs/defectos-y-limitaciones.md`, `docs/incidents/README.md`, `docs/ai-usage/AI-LOG.md` |
| **Clasificación** | Mixto: resultados aceptados y modificados (ver sección 5) |

## 1. Objetivo

La minuta de planeación de la entrega final asigna a Daniel la gestión (Issues, cronograma, riesgos, minutas y CR-001), el instructivo de conexión entre equipos, el README, la guía de usuario, la bitácora de red, los defectos y limitaciones, el índice de incidentes, la guía de diagnóstico y el índice del AI-LOG. Se usó la IA para:

1. Analizar la asignación de la entrega final contra el estado del repositorio y redactar la minuta de planeación con las decisiones del equipo.
2. Preparar la lista de tareas de cada integrante, con las dependencias entre ellas.
3. Revisar los PR de la entrega final (#85 a #103), probar su combinación y preparar observaciones para los siguientes PR.
4. Redactar los documentos de usuario, de defectos y de gestión con el comportamiento real del código integrado.

## 2. Entrada proporcionada

- La asignación de la entrega final, la minuta de planeación y los documentos del repositorio (ADR, guías, matriz, release notes, minutas anteriores).
- El código de `main` y de los PR #85 a #103.

Prompts utilizados (textuales, algunos):

> 1. "Analiza a detalle y dame por ejemplo minutas de lo que se decidió"
> 2. "Dame los pdfs de lo que tiene que hacer cada uno"
> 3. "Revisa los pr de josue y dame las cosas ha revisar para tenerlo en cuenta en los siguientes pr"
> 4. "revisa los ultimos prs de yousu y dame mis archivos de paso"
> 5. "analiza los pr que hay, dame los documentos que puedo suibir y dime como vamos a hacer las pruebas de lo de la vpn"
> 6. "dame un pdf para hacer todo eso de la prueba de vpn, incluye tambien lo que se debe de hacer en tailscale"
> 7. "ok me gusta eso de la persona externa, dame los documentos necesarios para subir y acabar con el proyecto"

## 3. Resultado recibido

1. Minuta de planeación: análisis de lo que pide la entrega contra lo que existe, 16 decisiones, decisiones abiertas, reparto de la demostración y acciones por bloques.
2. Un PDF de tareas por integrante, con lo que necesita de otros y quién espera su trabajo.
3. Revisión de los PR #85 a #103: orden de integración, resolución de conflictos en `AI-LOG.md` y `server.py`, pruebas manuales con el servidor real y una lista de puntos para los siguientes PR.
4. Cronograma v6 y v7 (plan por bloques, estado y riesgos 13 a 17), instructivo de conexión con Tailscale y LAN privada, bitácora con los eventos de red, documento de defectos y limitaciones, índice de incidentes, guía de diagnóstico y AI-LOG con el PR de revisión de cada registro.
5. Plan de la prueba entre equipos con Tailscale (un servidor y uno o más clientes) y de su evidencia.
6. Documentos de cierre: release notes de `v1.0.0` con sus excepciones, participación del equipo, minutas 2 a 4, cronograma v8, README y defectos y limitaciones.

## 4. Revisión realizada

- La combinación de `main` con los PR #91 y #92 se probó con `./scripts/test.sh`: 142 pruebas unitarias y 99 de integración en OK, y los 19 TC del resumen en PASS. La de los PR #101 a #103: 143 y 121 en OK.
- Al integrarse el PR #102, `--allow` pasó a reemplazar la lista por defecto; el instructivo de conexión y la guía de diagnóstico se corrigieron con la salida real del servidor.
- Las respuestas de versión del protocolo, el rechazo de direcciones y el cierre con clientes TCP abiertos se probaron con el servidor real.
- Cada mensaje de error de la guía de usuario y del instructivo se obtuvo ejecutando el comando correspondiente.
- La tabla de eventos de `bitacora.md` se armó con las llamadas reales a la bitácora en `executor.py`, `server.py` y `red.py`.
- Los pasos de Tailscale y del modo `mirrored` de WSL se compararon con la documentación oficial de Tailscale y de Microsoft.
- Los defectos DEF-006, DEF-007 y DEF-008 se reprodujeron sobre `main` antes de registrarlos.

## 5. Cambios aplicados

| Resultado de la IA | Decisión del equipo | Clasificación |
|---|---|---|
| Minuta de planeación de la entrega final | Revisada por Daniel; se integra en el PR de este registro | **Aceptado** |
| Reparto del trabajo | Se asignó más carga a Josué, a petición suya | **Modificado** |
| PDF de tareas por integrante con dependencias | Repartidos al equipo | **Aceptado** |
| Sugerencia para probar el rechazo de TC-011 conectándose desde `127.0.0.1` con `--allow 10.0.0.0/8` | Era incorrecta: `127.0.0.1` siempre está permitido. Se corrigió a conectarse desde `127.0.0.2`, como hacen las pruebas de Josué | **Modificado** |
| Observaciones a los PR de Josué (permiso de ejecución de `red.py`, regla de código de salida del CLI con el campo `v`, orden de integración) | Los dos primeros puntos quedaron resueltos en el PR #91 | **Aceptado** |
| Instructivo de conexión, defectos y limitaciones, índice de incidentes, diagnóstico y cronograma v6 | Integrados en el PR #100 | **Aceptado** |
| Bitácora, AI-LOG, cronograma v7 y correcciones por el cambio de `--allow` | En revisión en el PR de este registro | **Aceptado** (pendiente de aprobación) |
| README, guía de usuario y diagnóstico | Integrados en el PR #111, sobre la guía de Juan | **Aceptado** |
| Documentos de cierre (release notes, participación, minutas 2 a 4, cronograma v8) | En revisión en el PR de cierre; los números de la ejecución formal los llena Daniel con su `resumen.md` | **Aceptado** (pendiente de aprobación) |
| Proponer una persona externa para TC-015 | El equipo no la tuvo; se decidió que evalúe un integrante que no escribió la guía, y se declara como excepción | **Modificado** |
| Documentar `output` y `health` antes de que existan | No se documentan hasta integrar el código de Juan (U2) | **Rechazado** |

## 6. Limitaciones del resultado de la IA

- La IA no tiene acceso a la API de GitHub: no pudo comprobar las aprobaciones de los PR ni el `Closes #N` de cada uno.
- El cliente remoto (`--host`, `--port`) se documentó con la interfaz acordada en la minuta (decisión 10), antes de que existiera el código; se confirma al integrar el PR de Juan (U1).
- El contenido del Change Request no se conocía al redactar los documentos.
- La IA no tiene acceso de escritura al repositorio: todos los cambios los sube Daniel desde su rama.

## 7. Prueba o verificación agregada

| Artefacto | Prueba | Resultado |
|---|---|---|
| Guía de usuario, instructivo de conexión y diagnóstico | Comandos y mensajes comparados con el servidor real | Cumple |
| `bitacora.md` | Eventos comparados con las llamadas a `bitacora.evento()` y `bitacora.error()` del código | Cumple |
| Revisión de los PR #91, #92 y #101 a #103 | `./scripts/test.sh` sobre la combinación con `main` | Cumple |
| DEF-006, DEF-007 y DEF-008 | Reproducidos con el servidor real | Defectos confirmados y registrados |

**Verificó:** Daniel Alejandro Huerta Camberos

## 8. Aprendizaje

- Revisar los PR combinados, y no solo uno por uno, detecta conflictos y dependencias que cada PR por separado no muestra.
- Sacar los mensajes de error ejecutando los comandos evita documentar textos que el programa no produce.
- Probar casos fuera del flujo normal (dos servidores a la vez, servidor detenido con `SIGSTOP`) encontró un defecto que las pruebas no cubrían.
