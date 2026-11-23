# Plan de Verificación — JobRunner

**Alcance de esta versión:** Entrega final (`v1.0.0`): operación local y remota en red privada
**Responsable:** Diego Armando Durán Hernández (Verificación)
**Documentos relacionados:** [Matriz de trazabilidad](matriz-trazabilidad.md) · [Casos de prueba](../test-cases/) · [Inspecciones](../inspecciones/) · [Revisión cruzada](../revision-cruzada/) · [ADR](../../docs/decisions/) · [README](../../README.md)

> **Control de cambios:** esta versión reemplaza al plan del Avance 1, que solo cubría el núcleo local. Cambian el alcance (secciones 1 y 2), la estrategia (3), el entorno (4), el formato de los casos (5), la ejecución y la evidencia (6), el catálogo de casos (7), los defectos (8), los criterios de aceptación (9) y los pendientes (10); se agregan las secciones 11 (pruebas de robustez e inyección de fallas) y 12 (verificación cruzada).

## 1. Propósito

Definir cómo se comprueba que JobRunner `v1.0.0` cumple los 30 requisitos funcionales (RF) y los 34 no funcionales (RNF) y los criterios de aceptación de la entrega final: operación local y remota entre dos equipos en LAN privada o VPN, concurrencia con cola, persistencia y recuperación, cancelación con escalamiento, cierre controlado y robustez ante fallas.

El plan responde cinco preguntas: qué se verifica (sección 2), con qué métodos y casos (3 y 7), en qué entorno (4), dónde queda la evidencia y cómo se calcula (6), y cómo se atiende lo que encuentre quien verifica desde fuera (12). Toda afirmación de «cumple» sale de una ejecución de `verify.sh` o de una ejecución remota registrada; no se prepara evidencia a mano.

## 2. Qué se verifica

### 2.1 En alcance

| Capacidad | Requisitos | Casos |
|---|---|---|
| Enviar un trabajo, ID único y rechazo de entradas inválidas | RF-01, RF-02 | TC-001 |
| Cola FIFO, límite de concurrencia y rechazo explícito con la cola llena | RF-03, RF-04, RF-05, RF-23, RF-25, RNF-04, RNF-07, RNF-29 | TC-002, TC-016 |
| Estados, tiempos, consulta y listado | RF-06 a RF-09, RNF-05 | TC-003, TC-004 |
| Salida estándar y de error, y código de salida | RF-07, RF-11 | TC-006 |
| Cancelación sin bloqueo, escalamiento y cancelaciones concurrentes | RF-10, RF-26, RF-30, RNF-27 | TC-005, TC-017, TC-021 |
| Persistencia, recuperación al arrancar y 500 registros | RF-12, RF-13, RNF-06, RNF-10, RNF-11, RNF-28, RNF-31 | TC-007, TC-022, TC-026 |
| Bitácora de eventos | RF-14, RNF-15, RNF-22 | TC-025 |
| Inicio y cierre controlados, sin procesos huérfanos | RF-15, RNF-25, RNF-30 | TC-009 |
| Solicitudes duplicadas, desconexiones y muerte inesperada del hijo | RF-27, RF-28, RF-29, RNF-08, RNF-09 | TC-008, TC-018, TC-019, TC-020 |
| Liberación de recursos bajo carga | RNF-33 | TC-024 |
| Cliente: ayuda, códigos de salida y mensajes de error | RF-17, RNF-21, RNF-23 | TC-001, TC-004, TC-015 |
| Operación remota con la misma semántica que la local | RF-18, RF-19, RNF-26 | TC-010 |
| Restricción de acceso a localhost, redes privadas y VPN | RF-20, RNF-12, RNF-13 | TC-011 |
| Protocolo: mensajes delimitados y fragmentados, desconexiones, límites y versión | RF-21, RF-22, RNF-14, RNF-24, RNF-32 | TC-012, TC-019, TC-023 |
| Configuración y resumen de salud | RF-16, RF-24 | TC-013 |
| Construcción y ejecución reproducibles | RNF-01, RNF-02, RNF-03, RNF-19, RNF-20 | TC-014 |
| Calidad del código y de la documentación | RNF-16, RNF-17, RNF-18, RNF-34 | INS-016, INS-017, INS-018, INS-034 |

El detalle requisito por requisito (método, caso, evidencia y resultado) está en la [matriz de trazabilidad](matriz-trazabilidad.md), que es la fuente de verdad. Si un Change Request agrega requisitos, se agregan filas a la matriz y casos a este plan antes de implementarlos.

### 2.2 Fuera de alcance

- **Autenticación de personas y cifrado del tráfico.** El acceso se limita por red de origen y se recomienda la VPN (ADR-0008); no se verifica un control que el servicio no tiene.
- **Exposición a Internet.** El servicio se niega a escuchar en `0.0.0.0`, `::` o direcciones públicas, y eso es lo que se verifica (TC-011). Nunca se prueba con puertos abiertos en un router ni con direcciones públicas.
- **Rendimiento más allá de los requisitos.** Solo se verifican los umbrales de RNF-04, RNF-05 y RNF-06 (3 trabajos simultáneos, consulta en 1 s con 100 trabajos y 500 registros).

## 3. Estrategia

| Nivel | Qué cubre | Cómo |
|---|---|---|
| Unitario | `JobManager`, `Store`, la capa de red `Red`, la bitácora y las propias herramientas de verificación (`inspecciones.py`, `actualizar_matriz.py`) | `unittest` en `verif/unit/` |
| Integración local | Servidor y CLI reales por socket Unix, como los usaría una persona | `unittest` en `verif/integration/`: `helpers.py` levanta un servidor aislado (directorio y socket temporales) por prueba |
| Integración en red | Servidor real con `--listen` y `--allow`; clientes TCP desde `127.0.0.1` (permitido) y `127.0.0.2` (otro origen, rechazado) | `unittest` en `verif/integration/` (`test_servidor_tcp.py`, `test_acceso_tcp.py`) |
| Procesos | Zombis y huérfanos que deje el servicio, también en WSL | `verif/scripts/procesos.sh` (sección 6) y `test_procesos.py` |
| Clon limpio | Que alguien externo pueda clonar, construir y probar solo con el README | `verify.sh` clona el último commit y ejecuta `./scripts/setup.sh` (TC-014) |
| Robustez e inyección de fallas | Qué pasa cuando algo sale mal a propósito (sección 11) | Pruebas de integración que provocan la falla y revisan el estado, los procesos y la bitácora |
| Inspección | Calidad del código y de la documentación donde no hay comportamiento que ejecutar (RNF-16, 17, 18 y 34) | `verif/scripts/inspecciones.py`, con el criterio de cada una en `verif/inspecciones/` |
| Manual con evidencia | Lo que solo una persona o dos equipos pueden comprobar: usabilidad de la guía (TC-015) y operación entre dos equipos (TC-010) | Registro en `verif/manual/` y carpeta `verif/results/<run-id>-remoto/`; `verify.sh` los exige |
| Verificación cruzada | Que otro equipo, sin conocer el código, pueda construir, usar y romper el producto (sección 12) | Versión candidata, Issues `[Defecto] VC-NN` y `verif/revision-cruzada/` |

**Principios**

1. **La evidencia sale de la ejecución, no de la redacción.** Un caso es `PASS` solo si `verify.sh` lo calculó a partir del resultado de sus pruebas. Si falta una prueba, una inspección o una evidencia manual, el caso es `BLOCKED` y dice qué falta; nunca se da por cumplido.
2. **Las pruebas se buscan por nombre.** `verify.sh` asocia cada caso con los nombres de sus pruebas. Ninguna prueba cambia de nombre sin actualizar `verify.sh` y avisar a Verificación.
3. **Una prueba que no puede fallar no prueba nada.** Las pruebas de la verificación se comprueban rompiendo a propósito lo que verifican (por ejemplo, quitar un campo del almacén hace fallar TC-026, y cada inspección tiene una prueba que la hace fallar).
4. **Las pruebas con tiempos se repiten.** Antes de la ejecución formal se corre `verify.sh` más de una vez para descartar pruebas intermitentes (riesgo 12 del cronograma). Las esperas tienen límite; no se usan pausas fijas.
5. **Cada prueba tiene su servidor y su directorio.** Nada comparte estado entre pruebas ni toca `data/` del repositorio.
6. **La red solo se prueba en localhost, LAN privada o VPN.**

## 4. Entorno de verificación

- Linux (Ubuntu 22.04 / 24.04) o WSL2. La verificación formal se hace siempre desde un clon limpio en Linux (riesgo 5 del cronograma). Las pruebas de procesos y de sockets **no son válidas** en Git Bash con Python de Windows.
- En WSL, el repositorio va dentro de la carpeta personal (`~/JobRunner`), no en `/mnt/c/...`: en las carpetas de Windows el socket Unix no funciona.
- Python 3.10 o superior, solo biblioteca estándar (ADR-0001).
- Sin privilegios de root.
- **Red.** Las pruebas automáticas de red usan `127.0.0.1` y `127.0.0.2`, sin salir de la máquina. La operación entre dos equipos usa una LAN privada o la VPN (Tailscale, red `100.64.0.0/10`) y se registra en `verif/results/<run-id>-remoto/`. En WSL hace falta Tailscale dentro de WSL o el modo de red `mirrored`. Nunca se abren puertos en el router.

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
./scripts/test.sh                      # pruebas unitarias + integración + verify.sh
verif/scripts/verify.sh [run-id]       # solo la verificación y su evidencia
```

Cada ejecución de `verify.sh` crea `verif/results/<run-id>/` con:

| Archivo | Contenido |
|---|---|
| `entorno.txt` | Fecha, commit, versión de Python y sistema |
| `unittest.log` | Salida completa de las pruebas unitarias y de integración |
| `unit-resultados.tsv` | Resultado de cada prueba: `PASS`, `FAIL` o `XFAIL` (fallo esperado y conocido, `expectedFailure`) |
| `procesos.log` | Zombis y huérfanos que dejaron las pruebas |
| `tc-014-clon-limpio.log` | Clonado y construcción desde un clon limpio |
| `resumen.md` | Estado de cada TC en esa ejecución |

Además, `verify.sh` comprueba al final con `procesos.sh` que las pruebas no dejaron zombis ni huérfanos (`procesos.log`), y reemplaza la ruta del repositorio por `<repo>` en los registros para que la evidencia no lleve rutas personales.

**Zombis y huérfanos (`verif/scripts/procesos.sh`).** Solo lectura. Se guarda una línea base antes de la prueba y se revisa después:

```bash
verif/scripts/procesos.sh guardar base.txt
# ... prueba ...
verif/scripts/procesos.sh revisar --base base.txt [--patron 'sleep 300']
```

- **ZOMBI:** proceso en estado Z cuyo padre es el servidor (no recogió a un hijo terminado).
- **HUERFANO:** líder de sesión (los trabajos se lanzan con `start_new_session`) cuyo padre ya no es el servidor, es decir, su padre murió y lo adoptó otro proceso. En Linux lo adopta el PID 1, pero en WSL puede adoptarlo otro proceso de la sesión, por eso no se exige PPID 1 (DEF-005). Un trabajo vivo tiene como padre al servidor y no cuenta.
- Código de salida: 0 limpio, 1 hallazgos, 2 uso incorrecto. Detalle en la cabecera del script.

Al terminar una ejecución formal, `python3 verif/scripts/actualizar_matriz.py <run-id>` copia el estado de cada TC (de `resumen.md`) a la [matriz de trazabilidad](matriz-trazabilidad.md): la columna Estado de los casos y la columna Resultado de cada RF y RNF (el peor estado de sus casos).

Sin `run-id` se usa la fecha y hora (`AAAAMMDD-HHMMSS`). Para una ejecución formal conviene un nombre explícito, por ejemplo `20261002-avance1`, y confirmar los cambios antes de correrla, porque el clon limpio parte del último commit. Solo las ejecuciones formales se agregan al repositorio.

## 7. Casos de prueba

El catálogo completo (TC-001 a TC-025, con los requisitos que cubre cada uno) está en la [matriz de trazabilidad](matriz-trazabilidad.md); `verify.sh` calcula el estado de cada caso. Los del Avance 1:

| TC | Título | Nivel | Automatización |
|---|---|---|---|
| [TC-001](../test-cases/TC-001.md) | Enviar un trabajo y obtener un ID único | Integración | `verif/integration/test_tc001_enviar_trabajo.py`. Complemento unitario: `test_ids_unicos.py` |
| [TC-003](../test-cases/TC-003.md) | Estados y transiciones de un trabajo | Unitario | `test_ciclo_vida.py` |
| [TC-004](../test-cases/TC-004.md) | Consultar estado y listar trabajos desde el CLI | Integración | `verif/integration/test_tc004_consultar_listar.py` |
| [TC-005](../test-cases/TC-005.md) | Cancelación de un trabajo | Unitario | `test_ciclo_vida.py` |
| [TC-006](../test-cases/TC-006.md) | Ejecución como proceso separado y código de salida | Unitario | `test_ciclo_vida.py` |
| [TC-008](../test-cases/TC-008.md) | Entradas inválidas sin tumbar el gestor | Unitario | `test_ciclo_vida.py` |
| [TC-014](../test-cases/TC-014.md) | Construcción desde un clon limpio | Clon limpio | `verify.sh` |

## 8. Defectos

Un FAIL se registra con la plantilla de Issue "defecto" (`.github/ISSUE_TEMPLATE/defecto.md`) y se lista en la sección "Defectos abiertos" de la [matriz de trazabilidad](matriz-trazabilidad.md) hasta que se corrija y el caso vuelva a pasar.

## 9. Criterios de salida del Avance 1

- Todos los TC del catálogo están en PASS, o en BLOCKED con la dependencia indicada.
- No hay TC en FAIL sin defecto registrado.
- TC-014 en PASS desde un clon limpio (condición del tag `v0.1.0`).

## 10. Pendientes por confirmar con el equipo

- **Requisitos RF/RNF:** la matriz lista RF-01 a RF-24 y RNF-01 a RNF-26, pero el texto de cada requisito y su TC faltan: están en los PDF y el repositorio solo tiene los códigos citados en los ADR. Además, los ADR citan RNF-28, RNF-31 y RNF-32, fuera del rango.
- **Otros TC citados en los ADR:** TC-002 (ADR-0001, concurrencia), TC-007 y TC-022 (ADR-0002, escrituras en SQLite) y TC-023 (ADR-0003). Corresponden a los Hitos 2 y 3 y no se definen aquí.
- **Numeración de TC:** TC-005 (cancelación) y TC-006 (código de salida) siguen el PDF 05. El resto de la numeración, en particular TC-008, hay que confirmarla contra ese PDF: el ADR-0003 cita TC-008 como prueba del contrato de mensajes JSON, y aquí cubre las entradas inválidas.
