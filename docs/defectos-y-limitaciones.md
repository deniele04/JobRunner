# Defectos y limitaciones conocidos

Registro único de los defectos encontrados en JobRunner, su estado, y las limitaciones vigentes de la versión actual. Lo mantiene Producto (Daniel Alejandro Huerta Camberos), con la información de Verificación y de cada responsable de módulo.

- Un **defecto** es un comportamiento que no cumple un requisito, un ADR o la documentación. Se corrige con una prueba de regresión o se justifica.
- Una **limitación** es un comportamiento conocido y aceptado por diseño. Se documenta para que el usuario lo sepa.
- Los incidentes (fallas observadas en operación, con su análisis) están en [`docs/incidents/`](incidents/README.md).

## Defectos

| ID | Descripción | Requisitos | Detectado en | Responsable | Estado |
|---|---|---|---|---|---|
| DEF-001 | IDs de trabajo con colisiones: `Job.new()` generaba el ID con `uuid.uuid4().hex[:4]` (65 536 valores) | RF-01 | TC-001 (Avance 1) | Ingeniería | **Cerrado.** `Job.new()` usa el UUID completo; `test_ids_unicos_en_2000_trabajos` pasa |
| DEF-002 | Archivos de salida sin cerrar en `JobManager.submit()` (avisos `ResourceWarning`) | RF-11 | TC-006 (Avance 1) | Ingeniería | **Cerrado.** `submit()` abre los archivos con `with`; `unittest.log` ya no contiene `ResourceWarning` |
| DEF-003 | El CLI terminaba con código 1 en operaciones exitosas (`"error" in response` con la clave `error` en `null`) | RF-17 | TC-001 y TC-004 (`20261028-integracion`) | Josué Said Delgadillo Gutiérrez | **Cerrado** en el PR #51. Pruebas: `test_submit_exitoso_termina_con_codigo_0`, `test_status_y_list_exitosos_terminan_con_codigo_0`, `test_trabajo_con_error_nulo_no_es_error` |
| DEF-004 | Los trabajos terminados que nadie consultaba quedaban como zombis hasta la siguiente consulta | RF-29, RNF-33 | TC-020 y TC-024 (Avance 2) | Juan José Rentería Haro | **Cerrado** en el PR #66. El ciclo de 0,5 s del servidor (`tick()`, ADR-0004) recoge los procesos; `test_servidor_inactivo_no_deja_zombis` pasa |
| DEF-005 | `procesos.sh` no detecta procesos huérfanos en WSL: busca huérfanos con PPID 1, pero en WSL el proceso huérfano puede quedar adoptado por otro proceso de la sesión. En la ejecución formal del Avance 2 fallaron `test_detecta_un_huerfano` y `test_si_el_servidor_muere_de_golpe_el_trabajo_queda_huerfano` | RNF-30 | `verif/results/20261030-v0.2.0/unittest.log` | Diego Armando Durán Hernández | **Cerrado** en el PR #101. Un huérfano es un líder de sesión cuyo padre ya no es el servidor. Regresión: `test_detecta_un_huerfano_adoptado_por_otro_proceso_que_no_es_el_pid_1` y `test_un_trabajo_en_ejecucion_no_es_un_huerfano`; se confirma en WSL en la ejecución formal |
| DEF-006 | Al cancelar un ID que no existe, el mensaje sale entre comillas: `"error": "'No existe el trabajo <id>'"`. `server.py` convierte el `KeyError` con `str(e)`, que agrega las comillas | RNF-23 | Revisión de los PR #91 y #92 | Ingeniería | **Cerrado** (U2). `handle_request` usa `e.args[0]`; pruebas: `test_cancelar_un_id_inexistente_no_pone_comillas_en_el_mensaje`, `test_output_de_id_inexistente_sin_comillas` |
| DEF-007 | Un estado inválido en `list --state` responde `"error interno: Estado desconocido: ..."`, aunque es un error del usuario y no del servicio | RNF-23 | Revisión de los PR #91 y #92 | Ingeniería | **Cerrado** (U2). `list` responde `Estado desconocido: <X>` como error del usuario; pruebas: `test_list_con_estado_desconocido_no_es_un_error_interno`, `test_list_con_estado_que_no_es_texto` |
| DEF-008 | Se puede iniciar un segundo servidor con la misma carpeta `data/` mientras el primero sigue vivo. El segundo borra el socket del primero, recupera sus trabajos en `RUNNING` como `FAILED` «interrumpido por reinicio» y termina sus procesos; el primero queda corriendo sin que ningún cliente pueda alcanzarlo | RF-15, RNF-08 | Revisión de los PR #91 y #92 (reproducido sobre `main` con #91 y #92) | Josué Said Delgadillo Gutiérrez | **Abierto, aceptado para `v1.0.0`** (severidad media, Issue #105). Se evita iniciando un solo servidor por carpeta `data/`; la guía de diagnóstico explica cómo detectarlo (`pgrep -af jobrunner.server`) y recuperarse. Corrección propuesta para una versión posterior: al arrancar, si el socket existe y responde, negarse a iniciar (o un candado `fcntl.flock` sobre `data/jobrunner.lock`) |

## Defectos de la verificación cruzada

En `v1.0.0` **no se realizó verificación cruzada** con otro equipo, así que no hay defectos VC-NN. Se declara como excepción en las release notes de `v1.0.0`. En su lugar, la versión se verificó con la ejecución formal de `verify.sh`, la prueba entre equipos por VPN (`verif/results/20261123-remoto/`) y la evaluación de la guía de usuario por un integrante que no la escribió (TC-015).

Si en una versión posterior se hace, cada defecto que reporte el otro equipo se registra como Issue `[Defecto] VC-NN`, con su análisis, la respuesta, la corrección o justificación y las pruebas de regresión ejecutadas (plan de verificación, sección 12).

## Limitaciones vigentes

| # | Limitación | Por qué se acepta | Referencia |
|---|---|---|---|
| L-1 | Un trabajo que terminó justo antes de una caída del servicio queda `FAILED` «interrumpido por reinicio», porque su resultado no alcanzó a guardarse | Repetirlo podría duplicar su efecto; se marca con su motivo y el usuario decide | ADR-0005 |
| L-2 | El servicio no autentica personas: cualquiera que se conecte desde una red permitida puede enviar, consultar y cancelar trabajos | El acceso se limita por red de origen y VPN; el token compartido quedó fuera del alcance | ADR-0008 |
| L-3 | El servicio no cifra los mensajes. En una LAN sin VPN el tráfico viaja en claro | El cifrado lo da Tailscale; la LAN sin VPN solo se usa en una red de confianza | ADR-0008 |
| L-4 | Solo se aceptan redes IPv4 privadas y la de Tailscale (`100.64.0.0/10`). Las direcciones IPv6 de Tailscale (`fd7a:...`) no se pueden usar; en IPv6 solo se acepta `::1` | Se usa la IP `100.x` de Tailscale, que siempre existe | ADR-0008, `red.py` (`REDES_ACEPTABLES`) |
| L-5 | Cada conexión rechazada escribe una línea `acceso_rechazado` en la bitácora, y la bitácora no se rota: muchos intentos la hacen crecer | El servicio solo escucha en loopback, redes privadas o la VPN, donde los intentos son pocos | Riesgo 17 del cronograma |
| L-6 | Se conservan todos los trabajos y sus archivos `.out` y `.err`; no hay borrado automático | Es la política de retención; para empezar de cero se borra la carpeta `data/` con el servicio apagado | ADR-0002 |
| L-7 | Al cerrar el servicio, las respuestas pendientes se intentan enviar una sola vez y sin esperar: un cliente que en ese instante espera una respuesta grande puede recibirla incompleta | El cierre no debe quedar bloqueado por un cliente; el cliente puede repetir la consulta al reiniciar | ADR-0006, PR #92 |
| L-8 | En WSL, el repositorio debe estar dentro de la carpeta personal (`~`): en `/mnt/c/...` el socket Unix no funciona | Limitación del sistema de archivos de Windows | Riesgo 5 del cronograma |
| L-9 | La red de WSL no es alcanzable desde otro equipo sin configuración: hace falta Tailscale dentro de WSL o el modo `mirrored` | Limitación de la red virtual de WSL2 | ADR-0008, [conexion-lan-vpn.md](user-guide/conexion-lan-vpn.md) |

## Historial

| Versión | Cambio |
|---|---|
| 1 | Se reúnen en un solo documento DEF-001 a DEF-004 (antes en la matriz de trazabilidad), DEF-005 (minuta de planeación de la entrega final) y los defectos y limitaciones encontrados al revisar la operación remota |
| 2 | DEF-005 pasa a Cerrado (PR #101) |
| 3 | DEF-006 y DEF-007 pasan a Cerrado con el cliente remoto, `output` y `health` (PR #110) |
| 4 | Cierre de `v1.0.0`: DEF-008 queda abierto y aceptado; no hubo verificación cruzada |
