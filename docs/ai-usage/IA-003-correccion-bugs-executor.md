# IA-003 — Correccion de 7 bugs plantados en el executor

| Campo | Valor |
|---|---|
| **Fecha** | 02/10/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision (PR #34) |
| **Hito** | Hito 1 - Nucleo local (Avance 1) |
| **Artefactos afectados** | src/jobrunner/jobs.py, src/jobrunner/executor.py |
| **Clasificacion** | En revision (PR #34) |

## 1. Objetivo

El profesor plante 7 errores intencionales en el codigo del equipo (issues #22 a #28), cada uno con titulo, pasos de reproduccion y una pista, sin revelar la causa exacta. Se uso la IA para:

1. Redactar los 7 Issues en GitHub con el formato pedido (titulo, como reproducirlo, pista).

2. Diagnosticar y corregir cada bug en jobs.py y executor.py.

3. Escribir pruebas de humo que reprodujeran exactamente los pasos de cada issue, para confirmar la correccion antes de subir.

## 2. Entrada proporcionada

- Lista original de 7 errores con titulo, "Como reproducirlo" y "Pista" (entregada por el profesor).

- El codigo fuente real de jobs.py y executor.py (de Juan Jose Renteria Haro), leido linea por linea antes de proponer cualquier correccion.

Prompts utilizados (resumen):

> "Issues que tenemos que hacer" (con la lista de los 7 errores)

> "Ahora vamos a solucionarlos"

> Confirmaciones paso a paso de cada comando de prueba ejecutado en WSL

## 3. Resultado recibido

1. Los 7 Issues creados en GitHub (#22-#28) con gh issue create, cada uno con el formato exacto solicitado.

2. jobs.py corregido: Job.new() usa uuid4() completo (antes truncado a 4 caracteres, causaba colisiones); now_iso() usa datetime.now(timezone.utc) (antes sin zona horaria).

3. executor.py corregido:

   - submit() cierra los descriptores de archivo stdout/stderr con un bloque with (antes quedaban abiertos indefinidamente, causando fuga de descriptores).

   - submit() valida que argv sea una lista/tupla de strings no vacios (antes aceptaba cualquier tipo, incluido un string suelto).

   - poll() registra el nombre de la senal (signal.Signals(-code).name) cuando un proceso termina por senal (antes dejaba error en None).

   - cancel() usa os.killpg() en vez de os.kill() para el SIGKILL de escalamiento (antes solo mataba el proceso principal, dejando huerfanos en el grupo).

   - list() normaliza el estado con .upper() y valida contra los estados conocidos, lanzando ValueError si no existe (antes era sensible a mayusculas y no validaba).

## 4. Revision realizada

- Cada correccion se probo reproduciendo exactamente los pasos de "Como reproducirlo" de su Issue correspondiente, en un entorno WSL (no en Windows puro, por las limitaciones de sockets y senales de Unix).

- Se escribieron 3 scripts de prueba ad hoc: uno para IDs/timestamps/validaciones/senal, uno con ulimit -n 256 para la fuga de descriptores, y uno con trap '' TERM; sleep 100 & wait para confirmar que no quedan procesos huerfanos tras cancel().

- py_compile confirmo que ambos archivos compilan sin errores de sintaxis antes de subir.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Las 7 correcciones propuestas (ver seccion 3) | Se adoptaron tal cual, cada una verificada con su propio caso de prueba antes de subir | Aceptado |
| Mensaje de error corregido en Job.transition() (codificacion de caracteres rota en el codigo original) | Se corrigio de paso al editar el archivo, no era parte de los 7 bugs reportados | Aceptado (fuera de alcance original) |

## 6. Limitaciones del resultado de la IA

- La IA no tuvo acceso directo al entorno de ejecucion; todas las pruebas las corrio Josue y reporto los resultados de vuelta.

- Las pruebas de humo son ad hoc, no sustituyen la suite formal de pytest que corresponde a otra tarea del equipo (verif/unit/test_executor.py).

- No se investigo si existen bugs adicionales no incluidos en la lista original de 7; el alcance se limito estrictamente a los issues reportados.

## 7. Prueba o verificacion agregada

| Bug (Issue) | Prueba ejecutada | Resultado |
|---|---|---|
| #22 IDs colisionan | 500 submits, verificar IDs unicos | Cumple (500/500 unicos) |
| #23 Timestamps sin tz | created_at termina en +00:00 | Cumple |
| #24 Fuga de descriptores | 200 submits con ulimit -n 256 | Cumple (sin OSError) |
| #25 Muerte por senal sin diagnostico | SIGTERM a un job, poll(), revisar error | Cumple (error: SIGTERM) |
| #26 SIGKILL no mata grupo | trap TERM + sleep 100 & wait, cancel(), pgrep | Cumple (sin huerfanos) |
| #27 submit acepta argv invalido | submit("sleep 5") | Cumple (ValueError) |
| #28 list sensible a mayusculas | list(state="running"), list(state="no_existe") | Cumple (filtra y valida) |

**Verifico:** Josue Said Delgadillo Gutierrez (02/10/2026)

## 8. Aprendizaje

- Reproducir el bug exactamente como lo describe el reporte, antes y despues del cambio, es la unica forma confiable de confirmar que una correccion realmente funciona.

- Los errores plantados a proposito suelen ser sutiles (un metodo equivocado, un caracter de indice) y faciles de pasar por alto en una revision superficial del codigo.

- Separar el trabajo de correccion de bugs del trabajo de features nuevas en PRs distintos deja un historial mas claro de que se arreglo y por que.

