# IA-002 — Correccion de ADRs, documentacion tecnica y Servidor+CLI

| Campo | Valor |
|---|---|
| **Fecha** | 02/10/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Aprobado (PR #14, fusionado) / Pendiente de revision (PR #32) |
| **Hito** | Hito 1 - Nucleo local (Avance 1) |
| **Artefactos afectados** | docs/decisions/0001-lenguaje-y-runtime.md, docs/decisions/0002-modelo-de-persistencia.md, docs/decisions/0003-mecanismo-de-comunicacion.md, docs/technical-guide/arquitectura.md, docs/technical-guide/modelo-estados.md, src/jobrunner/server.py, src/jobrunner/cli.py |
| **Clasificacion** | Parcial (ADR fusionado en PR #14; documentacion y Servidor/CLI en revision en PR #32) |

## 1. Objetivo

El issue #3 pedia aprobar o corregir las 3 ADR del equipo (lenguaje/runtime, persistencia, mecanismo de comunicacion) y el issue #20 pedia construir un Servidor y un CLI sobre el JobManager ya existente, ademas de su documentacion tecnica. Se uso la IA para:

1. Redactar y corregir el contenido de las 3 ADR, incorporando dos rondas de retroalimentacion de revision (formato, campos faltantes del template, codificacion de caracteres).

2. Disenar y escribir server.py (daemon sobre socket Unix) y cli.py (cliente con subcomandos submit/status/list/cancel), consumiendo el JobManager de executor.py sin modificarlo.

3. Redactar la documentacion tecnica (arquitectura.md y modelo-estados.md) a partir del codigo fuente real del proyecto.

## 2. Entrada proporcionada

- El template de ADR del equipo (docs/decisions/template.md), leido directamente del repositorio tras el cambio de estructura de docs/adr/ a docs/decisions/.

- Los comentarios de revision de Pull Requests anteriores (PR #13 y PR #14), con observaciones especificas sobre formato y campos faltantes.

- El codigo fuente real de jobs.py y executor.py (de Juan Jose Renteria Haro), leido antes de disenar el servidor y el cliente.

Prompts utilizados (resumen):

> "Tengo que corregir esto en base a lo que tenemos, Juan dejo errores a proposito para hacer correcciones"

> "Dime que hacer comando por comando para asegurarnos, tengo que hacerlo con pull request"

> Pegado directo de los comentarios de revision de GitHub para cada ronda de correcciones

> "Veamos" / confirmaciones paso a paso durante la construccion de server.py y cli.py

## 3. Resultado recibido

1. Las 3 ADR corregidas con todos los campos del template: Estado, Fecha, Responsable(s), Issue relacionado, Aprobado en, Historial, Contexto, Alternativas consideradas, Decision, Consecuencias (Positivas/Negativas/Riesgos con referencias a casos de prueba), Decisiones abiertas, Requisitos afectados, Evidencia.

2. server.py: daemon que escucha en un socket Unix (AF_UNIX), recibe una linea JSON por peticion, la despacha al JobManager y devuelve la respuesta como linea JSON; maneja JSON invalido y errores internos sin caerse.

3. cli.py: cliente con subcomandos submit, status, list y cancel (mas --help), que se conecta al socket y traduce cada comando en una peticion JSON.

4. arquitectura.md: documenta los 3 componentes (CLI, Servidor, Executor) y el recorrido completo de una solicitud submit, de extremo a extremo.

5. modelo-estados.md: documenta los 5 estados del Job, la tabla de transiciones validas (VALID_TRANSITIONS) y el escalamiento de senales usado en la cancelacion (SIGTERM, espera, SIGKILL).

## 4. Revision realizada

- Cada ronda de correccion de las ADR se verifico releyendo linea por linea el archivo contra los comentarios de revision especificos, antes de subir.

- server.py y cli.py se probaron de extremo a extremo en WSL (Ubuntu-24.04): arranque del servidor, y los 4 comandos del CLI (submit, status, list, cancel) contra trabajos reales (sleep, etc.), incluyendo la cancelacion de un proceso en ejecucion.

- La documentacion tecnica se contrasto contra el codigo fuente real (jobs.py, executor.py) para que cada afirmacion sea verificable en el codigo.

- Se revisaron ambos documentos tecnicos para detectar artefactos de copiado y pegado (texto con escapes de markdown, caracteres mal codificados, tablas con lineas en blanco que rompen su renderizado), corrigiendolos antes de subir.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Contenido inicial de las 3 ADR | Se corrigio en 2 rondas segun comentarios de revision especificos (campos de template, formato, codificacion) | Aceptado (PR #14, fusionado) |
| Diseno de server.py sobre socket Unix con protocolo de una linea JSON por peticion | Se adopto tal cual, verificado con pruebas manuales end-to-end | En revision (PR #32) |
| Diseno de cli.py con subcomandos via argparse | Se adopto tal cual | En revision (PR #32) |
| Documentacion tecnica (arquitectura.md, modelo-estados.md) | Se adopto, corrigiendo artefactos de formato antes de subir | En revision (PR #32) |

## 6. Limitaciones del resultado de la IA

- La IA no tuvo acceso directo al entorno de ejecucion; todas las pruebas de server.py y cli.py las corrio Josue en WSL y reporto los resultados de vuelta.

- El servidor y el cliente se probaron manualmente, no con una suite formal de pytest; esa es tarea separada del equipo (issue #4).

- El socket Unix no es compatible con rutas dentro de /mnt/c (sistema de archivos DrvFs de WSL), por lo que las pruebas se corrieron usando una ruta nativa de Linux (/tmp); esta limitacion de entorno no afecta el codigo en si, pero debe tenerse en cuenta al documentar como correr el proyecto.

- No se evaluo el comportamiento del servidor bajo carga concurrente alta ni con multiples clientes simultaneos.

## 7. Prueba o verificacion agregada

| Caso | Prueba ejecutada | Resultado |
|---|---|---|
| ADR corregidas | Relectura linea por linea contra cada comentario de revision | Cumple (PR #14 aprobado y fusionado) |
| server.py arranca y escucha | ./scripts/run.sh con JOBRUNNER_SOCKET en /tmp | Cumple |
| cli.py submit | jobrunner submit -- sleep 5 | Cumple (devuelve Job en estado RUNNING) |
| cli.py status | jobrunner status <id> | Cumple (refleja el estado actual) |
| cli.py list | jobrunner list --state RUNNING | Cumple |
| cli.py cancel | jobrunner cancel <id> sobre un trabajo en ejecucion | Cumple (trabajo termina en CANCELED) |
| Documentacion tecnica | Contraste manual contra jobs.py y executor.py | Cumple (sin afirmaciones no verificables en el codigo) |

**Verifico:** Josue Said Delgadillo Gutierrez (02/10/2026)

## 8. Aprendizaje

- Cuando el equipo cambia la estructura del repositorio (como el paso de docs/adr/ a docs/decisions/) o el template, conviene releer directamente el archivo mas reciente del repositorio antes de continuar, en vez de asumir que el formato previo sigue vigente.

- Separar la correccion de documentos (ADR) de la construccion de codigo nuevo (Servidor/CLI) en Pull Requests distintos facilita que cada revisor se enfoque en un tipo de cambio a la vez.

- Probar el servidor y el cliente de extremo a extremo (no solo revisar el codigo) fue necesario para descubrir limitaciones del entorno (sockets Unix no soportados en rutas de Windows montadas) que no eran evidentes solo leyendo el codigo.

