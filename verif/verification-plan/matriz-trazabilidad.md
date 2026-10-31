# Matriz de trazabilidad

Cadena obligatoria del Plan de Verificación: Requisito → Método → Caso → Resultado esperado → Evidencia → PASS/FAIL. Esta matriz relaciona cada RF y RNF con sus casos de prueba y el último resultado de la ejecución formal. Plan: [plan-de-verificacion.md](plan-de-verificacion.md).

**Última ejecución formal:** pendiente (la columna Resultado se llena con `verif/scripts/actualizar_matriz.py <run-id>` a partir del `resumen.md` de esa ejecución).

**Numeración de TC:** alineada con el PDF 05 del Plan de Verificación ([TC-001](../test-cases/TC-001.md) a [TC-024](../test-cases/TC-024.md)). [TC-025](../test-cases/TC-025.md) (bitácora) lo agregó el equipo.

**Valores de Resultado:** `PASS`, `FAIL`, `BLOCKED` (el caso existe pero no puede ejecutarse) y `Pendiente` (sin ejecución automatizada todavía, por ejemplo los casos del Hito 3).

## Casos de prueba

| TC | Título | Pruebas automatizadas | Estado |
|---|---|---|---|
| [TC-001](../test-cases/TC-001.md) | Enviar un trabajo válido | `verif/integration/test_tc001_enviar_trabajo.py` | Pendiente |
| [TC-002](../test-cases/TC-002.md) | Cola y límite de concurrencia | `verif/unit/test_cola.py` | Pendiente |
| [TC-003](../test-cases/TC-003.md) | Estados y tiempos | `verif/unit/test_ciclo_vida.py` | Pendiente |
| [TC-004](../test-cases/TC-004.md) | Consultar y listar | `verif/integration/test_tc004_consultar_listar.py` | Pendiente |
| [TC-005](../test-cases/TC-005.md) | Cancelar en cola y en ejecución | `verif/unit/test_ciclo_vida.py`, `test_cola.py` | Pendiente |
| [TC-006](../test-cases/TC-006.md) | Proceso separado, stdout/stderr y código de salida | `verif/unit/test_ciclo_vida.py` | Pendiente |
| [TC-007](../test-cases/TC-007.md) | Reinicio y recuperación | `verif/unit/test_persistencia.py`, `test_reinicio_servidor.py`, `test_store.py` | Pendiente |
| [TC-008](../test-cases/TC-008.md) | Aislamiento de fallo | `verif/unit/test_ciclo_vida.py`, `test_servidor_robusto.py`, `verif/integration/test_tc001_enviar_trabajo.py` | Pendiente |
| [TC-009](../test-cases/TC-009.md) | Cierre controlado | `verif/integration/test_tc009_cierre_controlado.py`, `test_procesos.py`, `verif/unit/test_cierre.py` | Pendiente |
| TC-010 | Flujo remoto completo en LAN/VPN | sin automatizar todavía | Pendiente |
| TC-011 | Restricción de red | sin automatizar todavía | Pendiente |
| TC-012 | Fragmentación y desconexión | sin automatizar todavía | Pendiente |
| TC-013 | Configuración y salud | sin automatizar todavía | Pendiente |
| [TC-014](../test-cases/TC-014.md) | Construcción desde clon limpio | `verif/scripts/verify.sh` | Pendiente |
| TC-015 | Usabilidad documental | sin automatizar todavía | Pendiente |
| [TC-016](../test-cases/TC-016.md) | Saturación de cola y rechazo explícito | `verif/unit/test_cola.py`, `test_servidor_cola.py` | Pendiente |
| [TC-017](../test-cases/TC-017.md) | Cancelaciones concurrentes | `verif/unit/test_cola.py` | Pendiente |
| [TC-018](../test-cases/TC-018.md) | Solicitud duplicada | `verif/unit/test_persistencia.py`, `test_reinicio_servidor.py`, `test_store.py` | Pendiente |
| [TC-019](../test-cases/TC-019.md) | Desconexión durante una solicitud | `verif/integration/test_tc019_desconexion.py` | Pendiente |
| [TC-020](../test-cases/TC-020.md) | Terminación inesperada del proceso hijo | `verif/integration/test_tc020_trabajo_muere.py` | Pendiente |
| [TC-021](../test-cases/TC-021.md) | Escalamiento de cancelación | `verif/unit/test_cola.py` | Pendiente |
| [TC-022](../test-cases/TC-022.md) | Interrupción durante la persistencia | `verif/unit/test_interrupcion_escritura.py` | Pendiente |
| TC-023 | Compatibilidad de protocolo | sin automatizar todavía | Pendiente |
| [TC-024](../test-cases/TC-024.md) | Liberación de recursos bajo carga | `verif/integration/test_tc024_estres.py` | Pendiente |
| [TC-025](../test-cases/TC-025.md) | Bitácora de eventos (caso del equipo) | `verif/unit/test_bitacora.py` | Pendiente |

## Matriz por requisito

Incluye RF-01 a RF-30 y RNF-01 a RNF-34 (el PDF 05 exige RF-01…RF-24 y RNF-01…RNF-26 sin huecos; RF-25 a RF-30 y RNF-27 a RNF-34 son los requisitos de condiciones operativas del documento de requisitos). **Prioridad:** solo las ocho filas de la matriz de muestra del PDF 05 tienen prioridad definida; el resto la decide Producto. **Método y TC:** se toman del PDF 05; cuando el PDF no asigna caso, la columna Defecto/Excepción lo indica y propone uno.

### Requisitos funcionales

| Req ID | Descripción breve | Prioridad | Método | Caso(s) | Evidencia | Resultado | Defecto/Excepción |
|---|---|---|---|---|---|---|---|
| RF-01 | Enviar trabajo e ID único | Alta | Prueba | [TC-001](../test-cases/TC-001.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-02 | Validar y rechazar entradas inválidas con mensaje útil | Por definir | Prueba | [TC-001](../test-cases/TC-001.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-03 | Cola cuando no hay capacidad inmediata | Por definir | Prueba | [TC-002](../test-cases/TC-002.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-04 | Procesos separados sin bloquear nuevas solicitudes | Por definir | Prueba | [TC-002](../test-cases/TC-002.md), [TC-006](../test-cases/TC-006.md) | unittest.log, unit-resultados.tsv | Pendiente | El PDF 05 no asigna TC; se propone [TC-002](../test-cases/TC-002.md) y [TC-006](../test-cases/TC-006.md) |
| RF-05 | Límite de concurrencia configurable y respetado | Alta | Prueba | [TC-002](../test-cases/TC-002.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-06 | Estados QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED | Por definir | Prueba | [TC-003](../test-cases/TC-003.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-07 | Tiempos de recepción, inicio, terminación y código de salida | Por definir | Prueba | [TC-003](../test-cases/TC-003.md), [TC-006](../test-cases/TC-006.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-08 | Consultar estado y metadatos por ID | Por definir | Prueba | [TC-004](../test-cases/TC-004.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-09 | Listar trabajos con filtro por estado | Por definir | Prueba | [TC-004](../test-cases/TC-004.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-10 | Cancelación en cola o en ejecución | Alta | Prueba | [TC-005](../test-cases/TC-005.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-11 | Capturar stdout y stderr sin mezclarlos | Por definir | Prueba | [TC-006](../test-cases/TC-006.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-12 | Conservar metadatos y resultados tras reiniciar | Por definir | Prueba | [TC-007](../test-cases/TC-007.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-13 | Recuperar historial y marcar trabajos interrumpidos | Por definir | Prueba | [TC-007](../test-cases/TC-007.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-14 | Bitácora con marca temporal e ID de trabajo | Por definir | Prueba | [TC-025](../test-cases/TC-025.md) | unittest.log, unit-resultados.tsv | Pendiente | [TC-025](../test-cases/TC-025.md) lo define el equipo; no está en el PDF 05 |
| RF-15 | Inicio y cierre controlados, sin aceptar trabajos durante el cierre | Por definir | Prueba | [TC-009](../test-cases/TC-009.md) | unittest.log, procesos.log | Pendiente | — |
| RF-16 | Configuración de directorio, concurrencia, interfaz y puerto | Por definir | Prueba/Inspección | TC-013 | pendiente | Pendiente | Hito 3 (interfaz y puerto) |
| RF-17 | Ayuda de uso y códigos de salida del cliente | Por definir | Prueba/Inspección | [TC-001](../test-cases/TC-001.md), [TC-004](../test-cases/TC-004.md), TC-015 | pendiente; unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-18 | Operación remota con protocolo documentado | Alta | Prueba/Demo | TC-010 | pendiente | Pendiente | Hito 3 |
| RF-19 | Misma semántica local y remota | Por definir | Prueba/Demo | TC-010 | pendiente | Pendiente | Hito 3 |
| RF-20 | Acceso remoto restringido a LAN/VPN autorizada | Crítica | Prueba/Análisis | TC-011 | pendiente | Pendiente | Hito 3 |
| RF-21 | Protocolo con mensajes delimitados y lecturas parciales | Por definir | Prueba | TC-012, TC-023 | pendiente | Pendiente | Hito 3 |
| RF-22 | Desconexiones de cliente sin terminar el servicio | Por definir | Prueba | TC-012, [TC-019](../test-cases/TC-019.md) | pendiente; unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-23 | Rechazar y registrar solicitudes que excedan límites | Por definir | Prueba | [TC-016](../test-cases/TC-016.md) | unittest.log, unit-resultados.tsv | Pendiente | El PDF 05 no asigna TC; se propone [TC-016](../test-cases/TC-016.md) (cola llena) |
| RF-24 | Resumen de salud del servicio | Por definir | Prueba | TC-013 | pendiente | Pendiente | Hito 3 |
| RF-25 | Cola llena: rechazo explícito sin perder trabajos | Por definir | Prueba | [TC-016](../test-cases/TC-016.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-26 | Cancelaciones concurrentes con estado final coherente | Por definir | Prueba | [TC-017](../test-cases/TC-017.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-27 | Solicitudes duplicadas sin estados contradictorios | Por definir | Prueba | [TC-018](../test-cases/TC-018.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-28 | Estado coherente si el cliente se desconecta | Por definir | Prueba | [TC-019](../test-cases/TC-019.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-29 | Detectar muerte inesperada del hijo y registrar diagnóstico | Por definir | Prueba | [TC-020](../test-cases/TC-020.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RF-30 | Escalamiento de cancelación documentado y verificable | Por definir | Prueba | [TC-021](../test-cases/TC-021.md) | unittest.log, unit-resultados.tsv | Pendiente | — |

### Requisitos no funcionales

| Req ID | Descripción breve | Prioridad | Método | Caso(s) | Evidencia | Resultado | Defecto/Excepción |
|---|---|---|---|---|---|---|---|
| RNF-01 | Compilar y ejecutar en Linux declarado | Por definir | Prueba/Inspección | [TC-014](../test-cases/TC-014.md) | tc-014-clon-limpio.log | Pendiente | — |
| RNF-02 | Construcción reproducible desde clon limpio | Alta | Prueba/Inspección | [TC-014](../test-cases/TC-014.md) | tc-014-clon-limpio.log | Pendiente | — |
| RNF-03 | Sin privilegios de root | Por definir | Prueba/Inspección | [TC-014](../test-cases/TC-014.md) | tc-014-clon-limpio.log | Pendiente | — |
| RNF-04 | Al menos 3 trabajos simultáneos con límite 3 | Por definir | Prueba | [TC-002](../test-cases/TC-002.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-05 | Consulta de estado en máximo 1 s con 100 trabajos | Por definir | Prueba | [TC-004](../test-cases/TC-004.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-06 | Soportar 500 registros sin pérdida de metadatos | Por definir | Prueba | sin TC | pendiente | Pendiente | El PDF 05 no asigna TC; falta definir el caso |
| RNF-07 | No iniciar más procesos que el límite | Por definir | Prueba | [TC-002](../test-cases/TC-002.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-08 | Solicitud inválida o desconexión no termina el servicio | Por definir | Prueba | [TC-008](../test-cases/TC-008.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-09 | Terminación anormal de un trabajo no afecta a otros | Crítica | Prueba | [TC-008](../test-cases/TC-008.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-10 | Tras reinicio no reportar RUNNING lo que ya no se controla | Por definir | Prueba | [TC-007](../test-cases/TC-007.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-11 | Escritura persistente sin estado parcial | Por definir | Prueba | [TC-007](../test-cases/TC-007.md), [TC-022](../test-cases/TC-022.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-12 | No escuchar en interfaces públicas por defecto | Por definir | Prueba/Inspección | TC-011 | pendiente | Pendiente | Hito 3 |
| RNF-13 | Acceso remoto limitado a localhost, redes privadas o VPN | Por definir | Prueba/Análisis | TC-011 | pendiente | Pendiente | Hito 3 |
| RNF-14 | Validar longitud y formato de mensajes de red | Por definir | Prueba | TC-012 | pendiente | Pendiente | Hito 3 |
| RNF-15 | Registros sin secretos ni configuración sensible | Por definir | Prueba/Inspección | [TC-025](../test-cases/TC-025.md) | unittest.log, unit-resultados.tsv | Pendiente | [TC-025](../test-cases/TC-025.md) lo define el equipo; no está en el PDF 05 |
| RNF-16 | Mínimo privilegio y modelo de amenazas básico | Por definir | Inspección | sin TC | pendiente | Pendiente | El PDF 05 no asigna TC; es de inspección documental |
| RNF-17 | Código modular, sin archivos monolíticos injustificados | Por definir | Inspección | sin TC | pendiente | Pendiente | El PDF 05 no asigna TC; es de inspección |
| RNF-18 | Interfaces y decisiones documentadas | Por definir | Inspección | sin TC | pendiente | Pendiente | El PDF 05 no asigna TC; es de inspección (ADR, guías) |
| RNF-19 | Compilar sin advertencias nuevas | Por definir | Prueba/Inspección | [TC-014](../test-cases/TC-014.md) | tc-014-clon-limpio.log | Pendiente | El PDF 05 no asigna TC; se propone [TC-014](../test-cases/TC-014.md) (`compileall`) |
| RNF-20 | Pruebas con un único comando documentado | Por definir | Inspección | [TC-014](../test-cases/TC-014.md) | tc-014-clon-limpio.log | Pendiente | El PDF 05 no asigna TC; se propone [TC-014](../test-cases/TC-014.md) (`./scripts/test.sh`) |
| RNF-21 | Mensajes de error con operación, causa y acción | Por definir | Inspección/Demo | TC-015 | pendiente | Pendiente | — |
| RNF-22 | Bitácora que correlaciona solicitud y trabajo | Por definir | Prueba | [TC-025](../test-cases/TC-025.md) | unittest.log, unit-resultados.tsv | Pendiente | [TC-025](../test-cases/TC-025.md) lo define el equipo; no está en el PDF 05 |
| RNF-23 | Guía de usuario sin asistencia del equipo | Por definir | Demo | TC-015 | pendiente | Pendiente | — |
| RNF-24 | Protocolo con mensajes fragmentados y solicitudes secuenciales | Por definir | Prueba | TC-012 | pendiente | Pendiente | Hito 3 |
| RNF-25 | Liberar sockets y procesos hijos al cerrar | Por definir | Prueba | [TC-009](../test-cases/TC-009.md) | unittest.log, procesos.log | Pendiente | — |
| RNF-26 | Demostración remota solo en red privada o VPN | Crítica | Inspección/Demo | TC-010, TC-011 | pendiente | Pendiente | Hito 3 |
| RNF-27 | Transiciones consistentes ante concurrencia | Por definir | Prueba | [TC-017](../test-cases/TC-017.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-28 | Actualizaciones persistentes atómicas o recuperables | Por definir | Prueba | [TC-022](../test-cases/TC-022.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-29 | Backpressure o rechazo explícito en los límites | Por definir | Prueba | [TC-016](../test-cases/TC-016.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-30 | Sin procesos huérfanos tras un cierre o falla | Por definir | Prueba | [TC-020](../test-cases/TC-020.md), [TC-009](../test-cases/TC-009.md) | unittest.log, procesos.log; unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-31 | Recuperación que distingue pendientes, terminados e interrumpidos | Por definir | Prueba | [TC-022](../test-cases/TC-022.md), [TC-007](../test-cases/TC-007.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-32 | Compatibilidad de versión del protocolo | Por definir | Prueba | TC-023 | pendiente | Pendiente | Hito 3 |
| RNF-33 | Pruebas de estrés con liberación de recursos | Por definir | Prueba | [TC-024](../test-cases/TC-024.md) | unittest.log, unit-resultados.tsv | Pendiente | — |
| RNF-34 | Decisiones de seguridad, consistencia o recuperación con riesgo y prueba | Por definir | Inspección | sin TC | pendiente | Pendiente | Se verifica en la sección Consecuencias de cada ADR (ADR-0002, 0005, 0006, 0007) |

## Defectos

| ID | Descripción | TC afectado | Estado |
|---|---|---|---|
| DEF-001 | **IDs de trabajo con colisiones.** `Job.new()` generaba el ID con `uuid.uuid4().hex[:4]` (65 536 valores). | [TC-001](../test-cases/TC-001.md) | Cerrado. `Job.new()` usa el UUID completo; `test_ids_unicos_en_2000_trabajos` pasa |
| DEF-002 | **Archivos de salida sin cerrar** en `JobManager.submit()`. | [TC-006](../test-cases/TC-006.md) | Cerrado. `submit()` abre los archivos con `with`; `unittest.log` ya no contiene `ResourceWarning` |
| DEF-003 | **El CLI devolvía código de salida 1 en consultas exitosas** (`"error" in response` con la clave `error` en `null`). Incumplía RF-17. | [TC-001](../test-cases/TC-001.md), [TC-004](../test-cases/TC-004.md) | Cerrado en el PR #51. Pruebas: `test_submit_exitoso_termina_con_codigo_0`, `test_status_y_list_exitosos_terminan_con_codigo_0`, `test_trabajo_con_error_nulo_no_es_error` |
| DEF-004 | **Zombis de trabajos terminados que nadie consulta.** `poll()` solo se llamaba desde `status`, `list` y `cancel`. Afectaba RF-29 y RNF-33. | [TC-020](../test-cases/TC-020.md), [TC-024](../test-cases/TC-024.md) | Cerrado. El ciclo de 0,5 s del servidor (`tick()`, ADR-0004) recoge los procesos; `test_servidor_inactivo_no_deja_zombis` pasa sin marca |

## Pendiente

| Pendiente | Efecto en la verificación |
|---|---|
| TC-010, TC-011, TC-012, TC-013, TC-015 y TC-023 | Hito 3 (acceso remoto) o verificación documental: quedan `Pendiente`. |
| RNF-06, RNF-16, RNF-17, RNF-18 | El PDF 05 no les asigna TC. Hay que definirlo con Producto o aceptarlo como inspección. |
| Prioridad de cada requisito | Solo ocho filas la tienen (matriz de muestra del PDF 05). Producto debe completarla. |
