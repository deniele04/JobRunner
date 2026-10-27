# IA-005 — Modulo de persistencia SQLite (store.py)

| Campo | Valor |
|---|---|
| **Fecha** | 27/10/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision (PR #45) |
| **Hito** | Hito 2 - Concurrencia y persistencia (Avance 2) |
| **Artefactos afectados** | src/jobrunner/store.py, src/jobrunner/jobs.py, verif/unit/test_store.py |
| **Clasificacion** | En revision (PR #45) |

## 1. Objetivo

Segun la minuta del 20/10/2026, Josue debe programar el modulo de persistencia SQLite (`store.py`) con transacciones, siguiendo el esquema del ADR-0002. Se uso la IA para:

1. Escribir `store.py` con el esquema aprobado, una transaccion por escritura y busqueda por `request_id`.

2. Agregar los campos `request_id` y `pid` a `Job`, que el esquema necesita.

3. Escribir las pruebas unitarias del modulo.

## 2. Entrada proporcionada

- El esquema de la tabla `jobs` aprobado por Josue en el ADR-0002 v3.

- `src/jobrunner/jobs.py` y `executor.py` reales, para que los campos del modulo coincidieran con la clase `Job`.

- El formato de las pruebas existentes en `verif/unit/` y el script `scripts/test.sh`.

## 3. Resultado recibido

1. `store.py`: clase `Store` con `save` (inserta o actualiza en una transaccion), `get`, `get_by_request_id`, `list` (por estado, en orden de creacion) y `close`.

2. `jobs.py`: dos campos nuevos en `Job` (`request_id` y `pid`), ambos opcionales.

3. `test_store.py`: 10 pruebas unitarias.

## 4. Revision realizada

- Josue ejecuto las 10 pruebas nuevas y las 17 anteriores en WSL: 27 pruebas en OK.

- Una primera ejecucion fallo por un error de formato al pegar el codigo (una comilla escapada); se corrigio y se repitio la prueba.

- Se verifico con `git diff` que el cambio a `jobs.py` fueran solo dos lineas y conservara el fin de linea CRLF del archivo.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Modulo `store.py` con el esquema del ADR-0002 | Adoptado; pendiente de revision del equipo | Aceptado |
| Campos `request_id` y `pid` en `Job` | Adoptados; los necesitan la recuperacion y los duplicados | Aceptado |
| Pruebas unitarias del modulo | Adoptadas | Aceptado |

## 6. Limitaciones del resultado de la IA

- El modulo todavia no esta conectado al `JobManager`: ni el servidor ni el ejecutor lo usan. Eso va en el siguiente PR.

- Las pruebas cubren el modulo aislado. La verificacion de reinicio con el servidor completo (TC-007) y de interrupcion durante una escritura (TC-022) queda pendiente.

- La IA no ejecuto codigo; todas las pruebas las corrio Josue.

## 7. Prueba o verificacion agregada

| Prueba | Que verifica | Resultado |
|---|---|---|
| test_guarda_y_lee_el_mismo_trabajo | Lo guardado es igual a lo leido | Cumple |
| test_guardar_dos_veces_actualiza_sin_duplicar | Guardar de nuevo actualiza la misma fila | Cumple |
| test_request_id_repetido_es_rechazado_y_no_cambia_nada | request_id unico | Cumple |
| test_estado_invalido_es_rechazado | Restriccion CHECK sobre los estados | Cumple |
| test_los_datos_sobreviven_a_cerrar_y_reabrir | Los datos persisten tras reabrir la base | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (27/10/2026)

## 8. Aprendizaje

- Pegar texto con formato en un archivo de codigo puede corromper comillas y barras; compilar antes de hacer el commit lo detecta de inmediato.

- Al editar un archivo con fin de linea CRLF hay que conservarlo para que el diff muestre solo lo que cambio.

- Una restriccion UNIQUE en la base de datos protege contra duplicados aunque falle la logica del servidor.
