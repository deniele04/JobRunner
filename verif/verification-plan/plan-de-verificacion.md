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
| Requisitos cubiertos | RF y RNF que comprueba, según el PDF 05 y la [matriz](matriz-trazabilidad.md) |
| Objetivo | Qué comportamiento se comprueba |
| Precondiciones | Estado inicial, datos y configuración |
| Pasos | Acciones numeradas, reproducibles, con la forma automática y la manual |
| Resultado esperado | Resultado medible que satisface el requisito |
| Pruebas automatizadas | Nombres de las pruebas que `verify.sh` busca |
| Resultado observado | Lo que realmente ocurrió, con el `run-id` de la ejecución |
| Evidencia | Ruta en `verif/results/<run-id>/` |
| Estado | `PASS`, `FAIL`, `BLOCKED` o `Pendiente` |

**Inspecciones.** Los requisitos que el PDF 05 asigna al método «Inspección» tienen un archivo `verif/inspecciones/INS-0NN.md` con sus criterios de aceptación, y su resultado sale de `inspecciones.py`. Cuentan en la matriz como un caso más.

**Casos manuales.** Lo que no se puede automatizar entero (usabilidad de la guía, TC-015) se registra en `verif/manual/TC-0NN.md`: quién lo evaluó, cuándo, con qué versión y dónde está la evidencia. Sin esos datos, `verify.sh` no lo da por cumplido.

**Estados**

- **PASS:** el resultado observado coincide con el esperado y existe evidencia.
- **FAIL:** el caso se ejecutó y el resultado difiere del esperado. Todo FAIL debe quedar registrado como defecto (sección 8).
- **BLOCKED:** no se puede ejecutar porque falta una dependencia (una prueba que otra persona aún no integró, un documento, una evidencia manual). `resumen.md` indica cuál. En la ejecución formal final no debe quedar ninguno sin una excepción documentada en las release notes.
- **Pendiente:** solo en la matriz: el caso aún no tiene resultado porque no se ha hecho con él la ejecución formal.

## 6. Ejecución y evidencia

```bash
./scripts/test.sh                      # pruebas unitarias + integración + verify.sh
verif/scripts/verify.sh [run-id]       # solo la verificación y su evidencia
python3 verif/scripts/inspecciones.py  # solo las inspecciones (RNF-16, 17, 18 y 34)
```

Cada ejecución de `verify.sh` crea `verif/results/<run-id>/` con:

| Archivo | Contenido |
|---|---|
| `entorno.txt` | Fecha, commit, versión de Python y sistema |
| `unittest.log` | Salida completa de las pruebas unitarias y de integración |
| `unit-resultados.tsv` | Resultado de cada prueba: `PASS`, `FAIL` o `XFAIL` (fallo esperado y conocido, `expectedFailure`) |
| `procesos.log` | Zombis y huérfanos que dejaron las pruebas |
| `tc-014-clon-limpio.log` | Clonado y construcción desde un clon limpio |
| `inspecciones.log` y `inspecciones.tsv` | Detalle y estado de INS-016, INS-017, INS-018 e INS-034 |
| `manual-TC-015.md` | Copia del registro manual de usabilidad |
| `resumen.md` | Estado de cada TC e inspección en esa ejecución, con el motivo de cada `BLOCKED` |

Además, `verify.sh` comprueba al final con `procesos.sh` que las pruebas no dejaron zombis ni huérfanos (`procesos.log`) y que la propia herramienta funciona (pruebas de `test_procesos.py`, DEF-005), y reemplaza la ruta del repositorio por `<repo>` en los registros para que la evidencia no lleve rutas personales. Termina con código 1 si alguna prueba, TC o inspección falla; los `BLOCKED` no cuentan como fallo pero aparecen en el resumen.

**Zombis y huérfanos (`verif/scripts/procesos.sh`).** Solo lectura. Se guarda una línea base antes de la prueba y se revisa después:

```bash
verif/scripts/procesos.sh guardar base.txt
# ... prueba ...
verif/scripts/procesos.sh revisar --base base.txt [--patron 'sleep 300']
```

- **ZOMBI:** proceso en estado Z cuyo padre es el servidor (no recogió a un hijo terminado).
- **HUERFANO:** líder de sesión (los trabajos se lanzan con `start_new_session`) cuyo padre ya no es el servidor, es decir, su padre murió y lo adoptó otro proceso. En Linux lo adopta el PID 1, pero en WSL puede adoptarlo otro proceso de la sesión, por eso no se exige PPID 1 (DEF-005). Un trabajo vivo tiene como padre al servidor y no cuenta.
- Código de salida: 0 limpio, 1 hallazgos, 2 uso incorrecto. Detalle en la cabecera del script.

**Operación entre dos equipos.** `verify.sh` prueba la red sobre `127.0.0.1`. La operación entre dos equipos se registra aparte, en `verif/results/<run-id>-remoto/`: bitácora de ambos lados, salida de los comandos y `health`. TC-010 no es `PASS` sin esa carpeta.

**De la ejecución a la matriz.** Al terminar una ejecución formal, `python3 verif/scripts/actualizar_matriz.py <run-id>` copia el estado de cada caso e inspección (de `resumen.md`) a la [matriz de trazabilidad](matriz-trazabilidad.md): la columna Estado de los casos y la columna Resultado de cada RF y RNF (el peor estado de sus casos).

Sin `run-id` se usa la fecha y hora (`AAAAMMDD-HHMMSS`). Para una ejecución formal conviene un nombre explícito, por ejemplo `20261030-v0.2.0`, y confirmar los cambios antes de correrla, porque el clon limpio parte del último commit. Solo las ejecuciones formales se agregan al repositorio.

## 7. Casos de prueba

El catálogo (TC-001 a TC-026, más las cuatro inspecciones) sigue la numeración del PDF 05, con [TC-025](../test-cases/TC-025.md) y [TC-026](../test-cases/TC-026.md) agregados por el equipo. Las pruebas automatizadas de cada caso, y su estado en la última ejecución formal, están en la [matriz de trazabilidad](matriz-trazabilidad.md); `verify.sh` calcula el estado de cada uno.

| Caso | Título | Nivel |
|---|---|---|
| [TC-001](../test-cases/TC-001.md) | Enviar un trabajo válido | Integración |
| [TC-002](../test-cases/TC-002.md) | Cola y límite de concurrencia | Unitario |
| [TC-003](../test-cases/TC-003.md) | Estados y tiempos | Unitario |
| [TC-004](../test-cases/TC-004.md) | Consultar y listar | Integración |
| [TC-005](../test-cases/TC-005.md) | Cancelar en cola y en ejecución | Unitario |
| [TC-006](../test-cases/TC-006.md) | Proceso separado, stdout/stderr y código de salida | Unitario |
| [TC-007](../test-cases/TC-007.md) | Reinicio y recuperación | Unitario |
| [TC-008](../test-cases/TC-008.md) | Aislamiento de fallo | Unitario e integración |
| [TC-009](../test-cases/TC-009.md) | Cierre controlado, también con TCP | Integración y unitario |
| TC-010 | Flujo remoto completo en LAN/VPN | Integración y manual con evidencia (dos equipos) |
| TC-011 | Restricción de red | Integración y unitario |
| TC-012 | Fragmentación y desconexión | Unitario e integración |
| TC-013 | Configuración y salud | Integración |
| [TC-014](../test-cases/TC-014.md) | Construcción desde un clon limpio | Clon limpio |
| TC-015 | Usabilidad documental | Integración y manual |
| [TC-016](../test-cases/TC-016.md) | Saturación de cola y rechazo explícito | Unitario |
| [TC-017](../test-cases/TC-017.md) | Cancelaciones concurrentes | Unitario |
| [TC-018](../test-cases/TC-018.md) | Solicitud duplicada | Unitario |
| [TC-019](../test-cases/TC-019.md) | Desconexión durante una solicitud | Integración |
| [TC-020](../test-cases/TC-020.md) | Terminación inesperada del proceso hijo | Integración |
| [TC-021](../test-cases/TC-021.md) | Escalamiento de cancelación | Unitario |
| [TC-022](../test-cases/TC-022.md) | Interrupción durante la persistencia | Unitario |
| TC-023 | Compatibilidad de protocolo | Integración |
| [TC-024](../test-cases/TC-024.md) | Liberación de recursos bajo carga | Integración |
| [TC-025](../test-cases/TC-025.md) | Bitácora de eventos (caso del equipo) | Unitario |
| [TC-026](../test-cases/TC-026.md) | 500 registros sin pérdida de metadatos (caso de Verificación) | Integración y unitario |
| [INS-016](../inspecciones/INS-016.md), [INS-017](../inspecciones/INS-017.md), [INS-018](../inspecciones/INS-018.md), [INS-034](../inspecciones/INS-034.md) | Inspecciones de RNF-16, RNF-17, RNF-18 y RNF-34 | Inspección |

Los casos sin enlace (TC-010, TC-011, TC-012, TC-013, TC-015 y TC-023) todavía no tienen su documento en `verif/test-cases/`; los escriben Josué (TC-011, TC-012 y TC-023) y Juan (TC-010, TC-013 y TC-015). Mientras tanto sus pruebas ya se ejecutan desde `verify.sh`.

## 8. Defectos

Un FAIL se registra con la plantilla de Issue «defecto» (`.github/ISSUE_TEMPLATE/defecto.md`), se lista en la sección «Defectos» de la [matriz de trazabilidad](matriz-trazabilidad.md) y, cuando exista, en `docs/defectos-y-limitaciones.md` (que mantiene Producto). Un defecto que reporta el otro equipo sigue además el proceso de la sección 12.

- **Severidad.** Alta: pierde o corrompe datos, tira el servicio, deja procesos sueltos o expone el servicio a una red no permitida. Media: un requisito no se cumple pero hay forma de seguir usando el producto. Baja: un mensaje, un texto o un caso borde sin consecuencia para los datos.
- **Cierre.** Un defecto se cierra con una corrección **y** una prueba de regresión que falla sin ella, en el mismo PR. Si no se corrige, se justifica como limitación aceptada con quién lo decidió y por qué; queda en las release notes.
- **Ningún FAIL sin defecto.** Si un caso falla en una ejecución formal, antes de la siguiente debe existir su Issue.

## 9. Criterios de aceptación de la entrega final

La versión `v1.0.0` se acepta cuando la ejecución formal final de `verify.sh` sobre el commit etiquetado cumple todo lo siguiente:

1. **Casos e inspecciones.** Todos los TC y las cuatro inspecciones están en `PASS`. Un `BLOCKED` solo se admite como excepción documentada en las release notes, con su motivo y quién lo resolverá; ningún caso queda en `Pendiente`.
2. **Sin defectos sin atender.** No hay un `FAIL` sin defecto registrado. Todo defecto abierto tiene severidad y decisión (corregir o limitación aceptada); ninguno de severidad alta queda abierto.
3. **Matriz completa.** Los 30 RF y los 34 RNF tienen su caso o inspección y su resultado: sin `Pendiente` ni `Sin TC`, con la evidencia enlazada.
4. **Construcción reproducible.** TC-014 en `PASS` desde un clon limpio; quien recibe la versión puede clonar, construir y probar solo con el README.
5. **Sin procesos sueltos.** La revisión de `procesos.sh` al final de las pruebas no encuentra zombis ni huérfanos, y las pruebas de la propia herramienta pasan también en WSL.
6. **Operación entre dos equipos.** Existe `verif/results/<run-id>-remoto/` con la bitácora de ambos lados, la salida de los comandos y el `health`, hecha solo en LAN privada o VPN.
7. **Verificación cruzada cerrada.** Cada defecto reportado por el otro equipo tiene su respuesta y su regresión en `PASS`, o su justificación (sección 12).
8. **Reproducible por cualquiera.** `./scripts/test.sh` termina sin `FAILED` sobre el commit etiquetado, y la evidencia entregada sale de esa ejecución, no de una preparada a mano.

## 10. Pendientes por confirmar con el equipo

| Pendiente | Quién | Efecto en la verificación |
|---|---|---|
| Contenido del Change Request CR-001 (se confirma con el profesor) | Daniel | Si agrega requisitos, se agregan filas a la matriz y casos a este plan antes de implementarlo |
| Si se agrega un token compartido como segunda capa de acceso | Josué (en el ADR-0008) | Obligaría a casos nuevos en TC-011 y a actualizar el modelo de amenazas (INS-016) |
| Modo de red de WSL para la demostración entre dos equipos (Tailscale dentro de WSL o `mirrored`) | Daniel y Josué | Define cómo se hace la evidencia `verif/results/<run-id>-remoto/` |
| Pruebas del cliente remoto y de `health` (`test_tc010_*.py` y `test_tc013_*.py`) | Juan | TC-010 y TC-013 quedan `BLOCKED` hasta que existan; `verify.sh` las toma por nombre de archivo |
| Documentos de los casos TC-010, TC-011, TC-012, TC-013, TC-015 y TC-023 | Josué y Juan | Sus pruebas ya se ejecutan, pero falta su descripción en `verif/test-cases/` |
| `seguridad.md` (modelo de amenazas y mínimo privilegio) | Josué | INS-016 queda `BLOCKED` sin él |
| Persona que evalúa TC-015 (idealmente del otro equipo) | Diego | El caso queda `BLOCKED` hasta que llene `verif/manual/TC-015.md` |
| Prioridad de cada requisito | Producto (Daniel) | Solo ocho filas la tienen (matriz de muestra del PDF 05) |

