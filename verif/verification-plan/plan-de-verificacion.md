# Plan de Verificación — JobRunner

**Alcance de esta versión:** Avance 1 — Núcleo local
**Responsable:** Diego Armando Durán Hernández (Verificación)
**Documentos relacionados:** [Matriz de trazabilidad](matriz-trazabilidad.md) · [ADR](../../docs/decisions/) · [README](../../README.md)

## 1. Propósito

Definir cómo se comprueba que el núcleo local de JobRunner cumple los criterios del Avance 1 (README, sección "Alcance actual"), con qué casos de prueba, en qué entorno y dónde queda la evidencia.

## 2. Qué se verifica

Los criterios del Avance 1:

1. Enviar un trabajo y obtener un ID único.
2. Ejecutar el trabajo como proceso separado.
3. Consultar estado y listar trabajos.
4. Cancelar un trabajo.
5. Obtener el código de salida.
6. Manejar comandos inválidos sin terminar el servicio.
7. Respetar los estados y transiciones del modelo (`QUEUED → RUNNING → SUCCEEDED | FAILED | CANCELED`).
8. Construcción reproducible desde un clon limpio (requisito para el tag `v0.1.0`, ver cronograma).

Fuera del alcance de esta versión: concurrencia, persistencia con SQLite y operación remota (Hitos 2 y 3).

## 3. Estrategia

| Nivel | Qué cubre | Cómo |
|---|---|---|
| Unitario | `Job` y `JobManager` (estados, transiciones, ejecución, cancelación, entradas inválidas, unicidad de IDs) | `unittest` en `verif/unit/` |
| Clon limpio | Que un externo pueda clonar y construir siguiendo el README | `verif/scripts/verify.sh` clona el repositorio y ejecuta `./scripts/setup.sh` |
| Extremo a extremo | Servidor y CLI comunicándose por socket Unix | Casos TC-001 y TC-004. Quedan BLOCKED hasta que el servidor y el CLI estén integrados en `main` (hoy existen en la rama `feature/docs-server-cli`) |

## 4. Entorno de verificación

- Linux (Ubuntu 22.04 / 24.04) o WSL2.
- Python 3.10 o superior, solo biblioteca estándar (ADR-0001).
- Sin privilegios de root.

La verificación formal se hace siempre desde un clon limpio en Linux (riesgo 5 del cronograma).

## 5. Formato de un caso de prueba

Cada caso vive en `verif/test-cases/TC-XXX.md` y tiene estos campos:

| Campo | Contenido |
|---|---|
| Identificador | `TC-XXX` |
| Requisitos cubiertos | Criterio del Avance 1 y, cuando se asigne, el RF/RNF correspondiente |
| Objetivo | Qué comportamiento se comprueba |
| Precondiciones | Estado inicial, datos y configuración |
| Pasos | Acciones numeradas, reproducibles |
| Resultado esperado | Resultado medible que satisface el requisito |
| Resultado observado | Lo que realmente ocurrió, con el `run-id` de la ejecución |
| Evidencia | Ruta en `verif/results/<run-id>/` |
| Estado | `PASS`, `FAIL` o `BLOCKED` |

**Estados**

- **PASS:** el resultado observado coincide con el esperado y existe evidencia.
- **FAIL:** el caso se ejecutó y el resultado difiere del esperado. Todo FAIL debe quedar registrado como defecto (sección 8).
- **BLOCKED:** no se puede ejecutar porque falta una dependencia (por ejemplo, el CLI). Se indica cuál.

## 6. Ejecución y evidencia

```bash
./scripts/test.sh                      # pruebas unitarias + verify.sh
verif/scripts/verify.sh [run-id]       # solo la verificación y su evidencia
```

Cada ejecución de `verify.sh` crea `verif/results/<run-id>/` con:

| Archivo | Contenido |
|---|---|
| `entorno.txt` | Fecha, commit, versión de Python y sistema |
| `unittest.log` | Salida completa de las pruebas unitarias |
| `unit-resultados.tsv` | Resultado (`PASS`/`FAIL`) de cada prueba |
| `tc-014-clon-limpio.log` | Clonado y construcción desde un clon limpio |
| `resumen.md` | Estado de cada TC en esa ejecución |

Sin `run-id` se usa la fecha y hora (`AAAAMMDD-HHMMSS`). Para una ejecución formal conviene un nombre explícito, por ejemplo `20261002-avance1`, y confirmar los cambios antes de correrla, porque el clon limpio parte del último commit. Solo las ejecuciones formales se agregan al repositorio.

## 7. Casos de prueba del Avance 1

| TC | Título | Nivel | Automatización |
|---|---|---|---|
| [TC-001](../test-cases/TC-001.md) | Enviar un trabajo y obtener un ID único | Extremo a extremo | Pendiente (requiere CLI). Verificación unitaria complementaria: `test_ids_unicos.py` (falla, DEF-001) |
| [TC-003](../test-cases/TC-003.md) | Estados y transiciones de un trabajo | Unitario | `test_ciclo_vida.py` |
| [TC-004](../test-cases/TC-004.md) | Consultar estado y listar trabajos desde el CLI | Extremo a extremo | Pendiente (requiere CLI) |
| [TC-005](../test-cases/TC-005.md) | Ejecución como proceso separado y código de salida | Unitario | `test_ciclo_vida.py` |
| [TC-006](../test-cases/TC-006.md) | Cancelación de un trabajo | Unitario | `test_ciclo_vida.py` |
| [TC-008](../test-cases/TC-008.md) | Entradas inválidas sin tumbar el gestor | Unitario | `test_ciclo_vida.py` |
| [TC-014](../test-cases/TC-014.md) | Construcción desde un clon limpio | Clon limpio | `verify.sh` |

## 8. Defectos

Un FAIL se registra con la plantilla de Issue "defecto" (`.github/ISSUE_TEMPLATE/defecto.md`) y se lista en la sección "Defectos abiertos" de la [matriz de trazabilidad](matriz-trazabilidad.md) hasta que se corrija y el caso vuelva a pasar.

## 9. Criterios de salida del Avance 1

- Todos los TC del catálogo están en PASS, o en BLOCKED con la dependencia indicada.
- No hay TC en FAIL sin defecto registrado.
- TC-014 en PASS desde un clon limpio (condición del tag `v0.1.0`).

## 10. Pendientes por confirmar con el equipo

- **Requisitos RF/RNF:** el repositorio no contiene el texto de los requisitos, solo sus códigos en los ADR. La columna RF/RNF de la matriz queda por asignar con el Project Brief.
- **Otros TC citados en los ADR:** TC-002 (ADR-0001, concurrencia), TC-007 y TC-022 (ADR-0002, escrituras en SQLite) y TC-023 (ADR-0003). Corresponden a los Hitos 2 y 3 y no se definen aquí.
- **TC-008:** el ADR-0003 lo cita como prueba del contrato de mensajes JSON; en este plan cubre las entradas inválidas. Hay que reasignar el contrato a otro TC (por ejemplo TC-023) o ajustar el ADR.
