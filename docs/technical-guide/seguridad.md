# Guía técnica: seguridad

Esta guía explica qué protege JobRunner, de qué amenazas, con qué mitigaciones y con qué pruebas (RNF-16). Se apoya en [ADR-0008](../decisions/0008-transporte-de-red-y-restriccion-de-acceso.md) (red y restricción de acceso) y [ADR-0009](../decisions/0009-protocolo-v1.md) (protocolo v1). El formato de los mensajes está en [protocolo y persistencia](protocolo-y-persistencia.md); cómo conectar dos equipos, en la guía de usuario.

## 1. Qué se protege
| Activo | Por qué importa |
|---|---|
| El equipo donde corre el servicio | `submit` ejecuta cualquier comando con los permisos del usuario que lo inició. Quien pueda enviar solicitudes puede ejecutar código en ese equipo. |
| Los trabajos y su salida | Los archivos `.out` y `.err` y la base de datos pueden contener información sensible. |
| La disponibilidad del servicio | Un cliente remoto no debe poder dejarlo sin responder a los demás. |
| La bitácora | Es la evidencia de quién se conectó y qué se rechazó. |

## 2. Modelo de seguridad
- **Por defecto es local.** Sin `--listen` solo existe el socket Unix, protegido por los permisos del archivo. No se abre ningún puerto.
- **El acceso remoto es opcional y explícito.** Se activa con `--listen` y solo atiende a los orígenes de `--allow` (o a `127.0.0.1` y `::1` si no se indica `--allow`).
- **El control es por red, no por persona.** No hay usuarios, contraseñas ni cifrado propio: quien llegue desde una red permitida puede enviar comandos. Por eso solo se aceptan redes privadas y se recomienda una VPN (Tailscale, `100.64.0.0/10`).
- **Nunca se abren puertos en el router.** La red solo se usa en localhost, LAN privada o VPN.

## 3. Amenazas, mitigaciones y pruebas
| # | Amenaza | Mitigación | Prueba |
|---|---|---|---|
| 1 | **Acceso desde fuera:** un equipo de una red no permitida se conecta | Lista de orígenes `--allow`; la conexión se cierra sin leer ni responder; evento `acceso_rechazado` con la IP; el rechazo no afecta al servicio | TC-011: `test_con_allow_10_0_0_0_8_la_conexion_desde_127_0_0_1_se_rechaza`, `test_sin_allow_entra_127_0_0_1_y_no_otro_origen`, `test_con_allow_se_acepta_solo_lo_indicado`, `test_un_origen_rechazado_no_puede_enviar_ni_cancelar_nada`, `test_rechazos_y_permitidos_intercalados_no_se_afectan` |
| 2 | **Exposición por error en una IP pública o en todas las interfaces** | El servidor se niega a arrancar si `--listen` es `0.0.0.0`, `::` o una dirección pública, o si `--allow` es `0.0.0.0/0`, `::/0` o una red pública. Sin `--listen` no hay puerto | TC-011: `test_listen_en_todas_las_interfaces_o_en_una_direccion_publica_no_arranca`, `test_allow_abierto_o_publico_no_arranca`, `test_sin_listen_no_se_abre_ningun_puerto` |
| 3 | **Mensajes enormes** para agotar memoria | Máximo 64 KiB por mensaje, con o sin salto de línea; se responde error, se registra y se cierra la conexión | TC-012: `test_mensaje_de_mas_de_64_kib_sin_salto_de_linea_recibe_error_y_se_cierra`, `test_linea_completa_de_mas_de_64_kib_tambien_se_rechaza`, `test_un_mensaje_de_exactamente_64_kib_si_se_procesa` |
| 4 | **Clientes lentos u ociosos** que retienen el servicio | Un solo hilo con selectores: ninguna conexión bloquea a otra; cierre tras 30 s sin datos; un cliente que no lee su respuesta no frena a los demás | TC-012: `test_un_cliente_conectado_que_no_envia_nada_no_retrasa_a_los_demas`; `test_conexion_inactiva_se_cierra` y `test_respuesta_enorme_a_un_cliente_que_no_lee_no_bloquea_a_los_demas` (`test_red.py`) |
| 5 | **Muchas conexiones o trabajos a la vez** | Cola con capacidad fija (`--queue-size`) y límite de trabajos simultáneos (`--max-jobs`); al llenarse se responde `cola llena` | TC-012: `test_veinte_clientes_a_la_vez_reciben_cada_uno_su_respuesta`; TC-024 (estrés) |
| 6 | **Cliente que se va a la mitad** y deja trabajos a medias | Una solicitud incompleta no se procesa; una completa se aplica una sola vez y es idempotente con `request_id` | TC-012: `test_cliente_que_se_va_a_la_mitad_no_crea_trabajos_y_el_servicio_sigue`, `test_cliente_que_se_va_sin_leer_la_respuesta_la_solicitud_se_aplica_una_vez` |
| 7 | **Clientes o servidores con otra versión** del protocolo | Campo `v`; una versión no soportada recibe error y no se ejecuta nada | TC-023 |
| 8 | **Lectura o alteración del tráfico** en una LAN | No se cifra: usar la VPN para cualquier acceso entre equipos | Inspección documental (esta guía y la guía de usuario) |

## 4. Riesgos que se aceptan
- **Sin autenticación de personas.** Cualquiera dentro de una red permitida puede ejecutar comandos. Es una decisión consciente del Hito 3; el token compartido quedó como decisión abierta en el ADR-0008.
- **Sin cifrado propio.** Se delega en la VPN. En una LAN sin VPN el tráfico viaja en claro.
- **La IP de origen es la del transporte.** Detrás de un reenvío (NAT o `portproxy` de Windows) todas las conexiones pueden parecer venir de una misma IP; por eso la lista debe revisarse con la configuración real de WSL.
- **Los límites son fijos** (64 KiB, 30 s) y no se pueden cambiar por opción.

## 5. Qué se registra
Cada rechazo y cada anomalía deja un evento en `jobrunner.log` (ver la [bitácora](../user-guide/bitacora.md)):
`servicio_iniciado` (con `tcp=` y `permitidas=`), `acceso_rechazado` (con `ip=`), `solicitud_invalida` (motivo: JSON inválido, no es un objeto, versión no soportada, mensaje demasiado grande o solicitud incompleta), `cliente_desconectado` y `red_cerrada`.

## 6. Cómo comprobarlo
1. `./scripts/test.sh` (o `verif/scripts/verify.sh <run-id>`): ejecuta TC-011, TC-012 y TC-023.
2. Evidencia entre dos equipos: carpeta `verif/results/<run-id>-remoto/` (incluye un acceso rechazado desde una IP no permitida).
3. Revisión de esta guía contra el ADR-0008 (inspección de RNF-16).
