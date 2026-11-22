# IA-016 — Cierre controlado con TCP

| Campo | Valor |
|---|---|
| **Fecha** | 21/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 4 - Operacion remota (entrega final) |
| **Artefactos afectados** | src/jobrunner/red.py, src/jobrunner/server.py, verif/unit/test_red.py, verif/integration/test_tc009_cierre_tcp.py |
| **Clasificacion** | En revision |

## 1. Objetivo

Implementar la tarea J5: que con Ctrl+C o SIGTERM el servicio deje de aceptar conexiones TCP, cierre las abiertas, libere el puerto y despues cancele los trabajos como en el ADR-0006, sin dejar procesos, conexiones ni el puerto ocupado. Se uso la IA para revisar el cierre actual, completarlo y escribir las pruebas.

## 2. Entrada proporcionada

- ADR-0006 y ADR-0008, `server.py` y `red.py` (J2 a J4), las pruebas de TC-009 y la descripcion de J5.

## 3. Resultado recibido

1. El cierre de la red ya ocurria antes de `manager.cerrar()`; la IA lo confirmo con pruebas en lugar de reescribirlo.
2. `Red.cerrar()` ahora devuelve cuantas conexiones cerro e intenta enviar una vez lo que ya estaba listo para un cliente.
3. `server.py` registra el evento `red_cerrada` (conexiones cerradas y direccion TCP) antes de `servicio_detenido`.
4. 3 pruebas unitarias y 11 de integracion nuevas (`test_tc009_cierre_tcp.py`).

## 4. Revision realizada

- Se ejecutaron las 241 pruebas del proyecto: todas pasan; las de cierre TCP se repitieron 3 veces sin fallos intermitentes.
- Una prueba fallo al principio por una carrera propia (la conexion de comprobacion del arranque aun no se atendia); se corrigio en la prueba con una espera corta.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Las pruebas de cierre con TCP (puerto libre, conexiones cerradas, sin huerfanos) | Adoptadas | Aceptado |
| `Red.cerrar()` devuelve el conteo y el evento `red_cerrada` | Adoptados | Aceptado |

## 6. Limitaciones del resultado de la IA

- La comprobacion `ss -ltn` solo se hace si el comando existe en el sistema.
- Una respuesta grande pendiente de envio puede perderse si el cliente no la alcanza a leer; se intenta enviar una vez y luego se cierra.
- Diego debe agregar los nombres de las pruebas nuevas al bloque de TC-009 en `verify.sh` (D4).

## 7. Prueba o verificacion agregada

| Caso | Pruebas | Resultado |
|---|---|---|
| TC-009 con TCP | test_tc009_cierre_tcp.py (11) | Cumple |
| Cierre de la capa de red | test_red.py (3 nuevas) | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (21/11/2026)

## 8. Aprendizaje

- Cerrar primero la red y despues los trabajos evita que un cliente cuelgue los 5 s que puede tardar un trabajo terco.
- Una conexion recien aceptada puede seguir "abierta" para el servidor unos milisegundos despues de que el cliente la cierre; las pruebas del conteo deben dejar pasar un instante.
