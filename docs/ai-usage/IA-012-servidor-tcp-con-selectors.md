# IA-012 — Servidor TCP con varios clientes (selectors)

| Campo | Valor |
|---|---|
| **Fecha** | 19/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 4 - Operacion remota (entrega final) |
| **Artefactos afectados** | src/jobrunner/red.py, src/jobrunner/server.py, verif/unit/test_red.py, verif/integration/test_servidor_tcp.py |
| **Clasificacion** | En revision |

## 1. Objetivo

Implementar la tarea J2 segun ADR-0008 y ADR-0009: que el servidor atienda por socket Unix y por TCP (`--listen`) a varios clientes a la vez, con un solo hilo y `selectors`, sin que un cliente lento retrase a los demas. Se uso la IA para disenar la capa de red y las pruebas.

## 2. Entrada proporcionada

- ADR-0008, ADR-0009, el `server.py` de `main` y las pruebas de integracion existentes.

## 3. Resultado recibido

1. `red.py`: lectura por conexion con buffer y delimitador `\n`, maximo de 64 KiB, cierre a los 30 s de inactividad, escritura con buffer y varias solicitudes por conexion respondidas en orden.
2. `server.py`: el ciclo principal alterna `manager.tick()` y `atender()`; opcion `--listen`.
3. 15 pruebas unitarias y 9 de integracion.

## 4. Revision realizada

- Se ejecutaron las 177 pruebas del proyecto: todas pasan; las pruebas TCP se repitieron 3 veces sin fallos intermitentes.
- Una prueba inicial con respuesta de 3 MiB y buffer minimo tardaba 79 s; se cambio a 12 MiB con buffer normal (ahora 3 s).

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| `red.py` con selectors | Adoptado | Aceptado |
| Cambios en `server.py` y `--listen` | Adoptados; sin `--allow` todavia (J3) | Aceptado |
| Pruebas unitarias e integracion | Adoptadas | Aceptado |

## 6. Limitaciones del resultado de la IA

- Esta version NO restringe quien se conecta: eso llega con J3 (`--allow`). No usar `--listen 0.0.0.0`.
- No hay autenticacion ni cifrado; se confia en la red privada (Tailscale).

## 7. Prueba o verificacion agregada

| Alcance | Pruebas | Resultado |
|---|---|---|
| Capa de red | verif/unit/test_red.py (15) | Cumple |
| Servidor con TCP | verif/integration/test_servidor_tcp.py (9) | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (19/11/2026)

## 8. Aprendizaje

- Con `selectors` un cliente conectado que no envia nada no bloquea a los demas; con el modelo anterior cada uno esperaba hasta su tiempo limite.
- Una respuesta grande para un cliente que no lee se guarda en un buffer y se envia cuando puede, sin detener el servidor.
