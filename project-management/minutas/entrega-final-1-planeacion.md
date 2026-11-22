# Minuta — Reunión de planeación de la entrega final

| Campo | Valor |
|---|---|
| **Medio** | WhatsApp y Discord |
| **Asistentes** | Diego Armando Durán Hernández, Josué Said Delgadillo Gutiérrez, Juan José Rentería Haro y Daniel Alejandro Huerta Camberos |
| **Redactó** | Daniel Alejandro Huerta Camberos |
| **Issue relacionado** | Por asignar |

## Objetivo

Analizar la asignación de la entrega final, tomar las decisiones técnicas de la operación remota (Hitos 3 y 4) y repartir el trabajo hasta la versión `v1.0.0`, la verificación cruzada y la demostración final. Es la primera de cuatro minutas de la entrega final.

## Análisis de la asignación

La versión `v0.2.0` cubre la funcionalidad de los avances 1 y 2. Para la entrega final se identificó lo siguiente:

| Lo que pide la entrega final | Cómo está | Qué falta | Requisitos |
|---|---|---|---|
| Servicio accesible por red y cliente remoto | Solo socket Unix local (ADR-0003) | Transporte TCP y cliente con `--host` y `--port` | RF-18, RF-19 |
| Envío, consulta, listado, salida y cancelación remotos | Todo existe en local, excepto la salida: se lee de `data/<id>.out` en la máquina del servidor | Las mismas operaciones por red y el comando `output` | RF-18, RF-19, RF-11 |
| Protocolo documentado y versionado | Documentado en la guía técnica, sin número de versión | Campo de versión e historial de versiones | RF-18, RNF-32 |
| Mensajes fragmentados | El servidor espera una línea completa y atiende una solicitud por conexión | Búfer por conexión, límite de tamaño y varias solicitudes por conexión | RF-21, RNF-14, RNF-24 |
| Desconexiones | Resuelto en local (INC-001, TC-019) | Repetirlo y probarlo sobre TCP | RF-22, RF-28 |
| Múltiples clientes | Se atienden uno por uno; un cliente lento retrasa a los demás hasta 5 s | Atender varias conexiones a la vez sin hilos | ADR-0007 |
| Restricción a localhost, LAN autorizada o VPN, y rechazo de accesos no autorizados | No aplica en local | Interfaz de escucha controlada, lista de acceso, rechazo y registro | RF-20, RNF-12, RNF-13, RNF-26 |
| Resumen de salud | No existe | Comando `health` | RF-24, RF-16 |
| Cierre controlado y liberación de recursos | Hecho en local (TC-009) | Incluir el puerto TCP y las conexiones abiertas | RF-15, RNF-25 |
| Change Request y análisis de impacto | No hay | CR-001 con su análisis de impacto | — |
| Matriz de trazabilidad completa | 21 de 64 requisitos en "Pendiente" o sin caso de prueba | TC-010, TC-011, TC-012, TC-013, TC-015, TC-023 y un caso para RNF-06; inspección documentada para RNF-16, RNF-17, RNF-18 y RNF-34 | Todos |
| Plan de verificación | Partes siguen escritas para el Avance 1 | Reescribirlo para la versión final | — |
| Defectos conocidos | DEF-005: `procesos.sh` no detecta huérfanos en WSL (2 pruebas de `test_procesos.py` fallaron en la ejecución del Avance 2) | Corregirlo con su prueba de regresión | RNF-30 |
| Evidencia de operación remota y de gestión | Solo hay evidencia local y las minutas | Evidencia entre dos equipos y resumen de participación | RNF-26 |

## Decisiones tomadas

| # | Decisión | Detalle | Registro |
|---|---|---|---|
| 1 | Transporte de red | TCP con el mismo protocolo de un objeto JSON por línea. El socket Unix se conserva para la operación local. Los comandos y las respuestas son los mismos en local y en remoto | ADR-0003 (decisión abierta resuelta) y ADR-0008 |
| 2 | Interfaz de escucha | Opción `--listen HOST:PUERTO`, por defecto `127.0.0.1:7070`. El servicio se niega a arrancar si la interfaz es `0.0.0.0`, `::` o una dirección pública: solo acepta loopback, redes privadas (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) y la red de la VPN (`100.64.0.0/10`). El servicio nunca se expone a Internet | ADR-0008 |
| 3 | Lista de acceso | Opción `--allow RED` (repetible, en notación CIDR). Por defecto solo se permite localhost. Las redes permitidas también deben ser privadas o de la VPN. Una conexión desde una dirección no autorizada se cierra sin leer nada y se registra `acceso_rechazado` en la bitácora | ADR-0008 |
| 4 | Red para la demostración entre dos equipos | Tailscale (VPN, red `100.64.0.0/10`). Alternativa: LAN privada con un punto de acceso propio. En WSL se prueba desde el inicio si hace falta el modo de red "mirrored" o Tailscale dentro de WSL | ADR-0008 |
| 5 | Varios clientes | Las conexiones se atienden con el módulo `selectors`: un solo hilo, sin bloqueos y con un búfer por conexión. Se conserva el ciclo de 0.5 s, y los estados se siguen cambiando en un solo lugar (`JobManager`), sin hilos | ADR-0007 (actualización) y ADR-0009 |
| 6 | Mensajes fragmentados | Los bytes se acumulan hasta el salto de línea. Una conexión puede enviar varias solicitudes y se responden en orden. Máximo 64 KiB por mensaje: si se excede, se responde con error y se cierra la conexión. Una conexión inactiva 30 s se cierra. Lo incompleto de un cliente que se desconecta se descarta sin crear trabajos | ADR-0009 |
| 7 | Versión del protocolo | Campo `"v": 1` en solicitudes y respuestas. Si falta, se asume la versión 1, por compatibilidad con el cliente local. Cualquier otra versión se responde con el error "versión de protocolo no soportada". La guía del protocolo lleva su historial de versiones | ADR-0009 |
| 8 | Recuperación de salida | Comando `output` (`id` y `stream`: `stdout` o `stderr`). Devuelve hasta los últimos 64 KiB y avisa si se recortó; los archivos completos siguen en `data/` | ADR-0009 |
| 9 | Resumen de salud | Comando `health`: versión del servicio y del protocolo, tiempo activo, trabajos por estado, ocupación (en ejecución contra `--max-jobs` y en cola contra `--queue-size`), clientes conectados, accesos rechazados y estado de la base | ADR-0009 |
| 10 | Cliente remoto | `royito --host HOST --port PUERTO`, o las variables `JOBRUNNER_HOST` y `JOBRUNNER_PORT`. Sin host, usa el socket Unix como hasta ahora | Guía de usuario |
| 11 | Cierre controlado | Además de lo que define el ADR-0006, deja de aceptar conexiones TCP, cierra las conexiones abiertas y libera el puerto | ADR-0006 (actualización) |
| 12 | Versión final | Tag `v1.0.0` con sus release notes. Lo que no se cumpla se declara como excepción documentada | Release notes |
| 13 | Change Request | CR-001 en `docs/change-requests/`, con su análisis de impacto (requisitos, ADR, módulos, casos de prueba, riesgos y esfuerzo) antes de implementarlo | CR-001 |
| 14 | Defectos y limitaciones | Un solo documento, `docs/defectos-y-limitaciones.md`, con cada defecto, su estado y las limitaciones vigentes | Ese documento |
| 15 | Verificación cruzada | Cada defecto que reporte el otro equipo se registra como Issue (`[Defecto] VC-NN`) y en `verif/revision-cruzada/`, con su análisis, la respuesta, la corrección o justificación y las regresiones ejecutadas | Plan de verificación |
| 16 | Evidencia remota | `verify.sh` prueba la red sobre `127.0.0.1`. La operación entre dos equipos se registra en `verif/results/<run-id>-remoto/`, con la bitácora de ambos lados, la salida de los comandos y el `health` | Plan de verificación |

## Decisiones abiertas (se resuelven en la minuta 2)

- Contenido del Change Request: se confirma con el profesor.
- Si se agrega un token compartido como segunda capa además de la lista de acceso (Josué lo evalúa como alternativa en el ADR-0008).
- Modo de red de WSL para la demostración entre dos equipos (Tailscale dentro de WSL o modo "mirrored"), según el resultado de la prueba de conexión.

## Acuerdos de trabajo

- Se mantienen los acuerdos de las minutas anteriores: rama propia, PR con 3 aprobaciones, `Closes #N` y cada PR de código con su prueba y la actualización de su documento.
- Ninguna prueba cambia de nombre sin actualizar `verify.sh`.
- La red solo se prueba en localhost, en una LAN privada o en la VPN. No se abren puertos en el router ni se usan direcciones públicas.
- Toda evidencia sale de `./scripts/test.sh`, de `verify.sh` o de la ejecución remota registrada. No se prepara evidencia a mano para la demostración.
- Cada integrante registra su uso de IA en el mismo PR donde lo usó.
- Todos deben poder explicar cualquier requisito, ADR, módulo y caso de prueba, porque la defensa individual puede tocar cualquiera.

## Reparto para la demostración final

| Momento de la demostración | Presenta | Evidencia |
|---|---|---|
| Instalación desde un clon limpio | Diego Armando Durán Hernández | TC-014 |
| Operación local | Juan José Rentería Haro | TC-001, TC-004 |
| Operación entre dos equipos en LAN o VPN | Josué Said Delgadillo Gutiérrez | TC-010, TC-011 |
| Concurrencia y saturación | Juan José Rentería Haro | TC-002, TC-016 |
| Cancelación | Diego Armando Durán Hernández | TC-005, TC-021 |
| Recuperación después de reinicio | Josué Said Delgadillo Gutiérrez | TC-007 |
| Manejo de una falla | Daniel Alejandro Huerta Camberos | TC-019, TC-020 y la bitácora |
| Trazabilidad de un requisito al azar | Daniel Alejandro Huerta Camberos | Matriz de trazabilidad |

## Preparación de la defensa individual

| Integrante | Módulo principal | ADR | Requisitos | Casos de prueba | Defecto o incidente |
|---|---|---|---|---|---|
| Josué Said Delgadillo Gutiérrez | `server.py` (red y protocolo) y `store.py` | ADR-0003, ADR-0008, ADR-0009, ADR-0002, ADR-0005 | RF-18 a RF-22, RF-12, RF-13 | TC-011, TC-012, TC-023, TC-007 | INC-001 |
| Juan José Rentería Haro | `executor.py` (cola, cancelación, `output` y `health`) y `cli.py` | ADR-0004, ADR-0006 | RF-03, RF-05, RF-10, RF-16, RF-24 | TC-002, TC-010, TC-013 | DEF-004 |
| Diego Armando Durán Hernández | `verify.sh`, `procesos.sh` y las pruebas | ADR-0006 | RF-15, RF-29, RNF-25, RNF-30, RNF-33 | TC-009, TC-020, TC-024 | DEF-005 |
| Daniel Alejandro Huerta Camberos | `bitacora.py`, documentación y gestión | ADR-0007 | RF-14, RNF-22, RNF-23 | TC-025, TC-019, TC-015 | INC-001 |

## Acciones

| Acción | Responsable |
|---|---|
| **Bloque 1 — Base (en paralelo; se revisa en la minuta 2)** | |
| ADR-0008 (transporte de red y restricción de acceso) y ADR-0009 (protocolo v1: versión, mensajes fragmentados, varios clientes, `output` y `health`); actualización del ADR-0003 (decisión abierta resuelta) y del ADR-0007 | Josué Said Delgadillo Gutiérrez |
| Servidor TCP con `selectors`: `--listen`, varias conexiones a la vez, búfer por conexión, varias solicitudes por conexión, límite de 64 KiB e inactividad de 30 s | Josué Said Delgadillo Gutiérrez |
| Cliente remoto: `--host`, `--port` y variables de entorno en `cli.py` y `royito` | Juan José Rentería Haro |
| Prueba de conexión entre dos equipos con Tailscale (también desde WSL), con su instructivo paso a paso | Daniel Alejandro Huerta Camberos y Josué Said Delgadillo Gutiérrez |
| Corregir DEF-005 (`procesos.sh` en WSL) con su prueba de regresión | Diego Armando Durán Hernández |
| Reescribir el plan de verificación para la versión final, con una sección de pruebas de robustez e inyección de fallas | Diego Armando Durán Hernández |
| Issues y milestone "Entrega final", cronograma de los Hitos 3 y 4 y registro de riesgos | Daniel Alejandro Huerta Camberos |
| CR-001 y su análisis de impacto | Daniel Alejandro Huerta Camberos |
| **Bloque 2 — Funciones (se revisa en la minuta 3)** | |
| Lista de acceso (`--allow`), rechazo de interfaces públicas y evento `acceso_rechazado` | Josué Said Delgadillo Gutiérrez |
| Versión del protocolo (`v`) y error de versión no soportada | Josué Said Delgadillo Gutiérrez |
| Cierre controlado con TCP: dejar de aceptar conexiones, cerrar las abiertas y liberar el puerto | Josué Said Delgadillo Gutiérrez |
| Comandos `output` y `health` en el ejecutor, el servidor y el cliente | Juan José Rentería Haro |
| Implementación del CR-001 según su análisis de impacto | Se asigna en la minuta 2, según el contenido del CR |
| **Bloque 3 — Casos de prueba y documentos (se revisa en la minuta 3)** | |
| TC-011 (restricción de acceso), TC-012 (mensajes fragmentados y desconexiones en red) y TC-023 (versión del protocolo), con sus pruebas | Josué Said Delgadillo Gutiérrez |
| Guía técnica: protocolo v1 con su historial de versiones, y modelo de amenazas (RNF-16) | Josué Said Delgadillo Gutiérrez |
| TC-010 (operación remota con la misma semántica que la local), TC-013 (salud y configuración) y TC-015 (ayuda y mensajes de error), con sus pruebas | Juan José Rentería Haro |
| Arquitectura y modelo de estados con la red, `output` y `health` | Juan José Rentería Haro |
| Caso de prueba para RNF-06 (500 registros sin pérdida) e inspección documentada de RNF-16, RNF-17, RNF-18 y RNF-34 en la matriz | Diego Armando Durán Hernández |
| `verify.sh` final con todos los casos y matriz de trazabilidad completa, sin requisitos en "Pendiente" | Diego Armando Durán Hernández |
| README final, guía de usuario (operación remota, `output`, `health` y conexión LAN/VPN) y bitácora con los eventos de red | Daniel Alejandro Huerta Camberos |
| Defectos y limitaciones conocidos, índice del registro de incidentes y guía de diagnóstico para incidentes no anunciados | Daniel Alejandro Huerta Camberos |
| Evidencia de gestión y participación (`project-management/participacion.md`: PR, commits, revisiones e Issues por integrante) | Daniel Alejandro Huerta Camberos |
| AI-LOG: un registro por integrante y el índice actualizado | Todos (índice: Daniel Alejandro Huerta Camberos) |
| **Bloque 4 — Candidata, verificación cruzada y entrega (se revisa en la minuta 4)** | |
| Ejecución de `verify.sh` sobre la versión candidata y entrega al otro equipo | Diego Armando Durán Hernández |
| Evidencia de operación entre dos equipos en `verif/results/<run-id>-remoto/` | Josué Said Delgadillo Gutiérrez y Diego Armando Durán Hernández |
| Respuesta a cada defecto de la verificación cruzada, su corrección y sus regresiones | Responsable del módulo afectado; coordina Diego Armando Durán Hernández |
| Ejecución formal final con resultados PASS/FAIL | Diego Armando Durán Hernández |
| Release notes `v1.0.0`, tag `v1.0.0` y Release | Daniel Alejandro Huerta Camberos |
| Guía de defensa individual y simulacro de trazabilidad de un requisito al azar | Daniel Alejandro Huerta Camberos (guía) y todos |
| Ensayo completo de la demostración final | Todos |

## Próximas reuniones

| Minuta | Cuándo | Qué se revisa |
|---|---|---|
| 2 | Al integrar el bloque 1 | ADR-0008 y ADR-0009 aprobados, servidor TCP y cliente remoto integrados, conexión entre dos equipos probada y decisiones abiertas resueltas |
| 3 | Al terminar los bloques 2 y 3 | Funciones integradas, casos en PASS o con defecto registrado, matriz completa y documentos listos. Se congela la versión candidata para la verificación cruzada |
| 4 | Al recibir la verificación cruzada | Respuesta a cada defecto, regresiones, ejecución formal, tag `v1.0.0` y ensayo de la demostración |

## Notas

Cada decisión de esta minuta se formaliza al aprobarse su ADR. Si cambia al implementarla, se actualiza el ADR y se registra en la siguiente minuta.
