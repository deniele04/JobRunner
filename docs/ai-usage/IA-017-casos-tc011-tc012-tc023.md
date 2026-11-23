# IA-017 — Casos TC-011, TC-012 y TC-023 y correccion de --allow

| Campo | Valor |
|---|---|
| **Fecha** | 21/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 4 - Operacion remota (entrega final) |
| **Artefactos afectados** | verif/test-cases/TC-011.md, TC-012.md, TC-023.md, verif/integration/test_tc011_restriccion_acceso.py, test_tc012_mensajes_en_red.py, src/jobrunner/red.py, src/jobrunner/server.py (ayuda de --allow), pruebas de red y de acceso, docs/decisions/0008 |
| **Clasificacion** | En revision |

## 1. Objetivo

Implementar la tarea J6: documentar los casos TC-011 (restriccion de acceso), TC-012 (mensajes en red) y TC-023 (version del protocolo) y agregar sus pruebas con servidor real. Se uso la IA para redactar los casos, escribir las pruebas y revisar el comportamiento de `--allow`.

## 2. Entrada proporcionada

- La tarea J6 del reparto, ADR-0008 y ADR-0009, el formato de TC-018 y el codigo de J2, J3 y J4.

## 3. Resultado recibido

1. Tres casos de prueba con el formato de TC-018.
2. `test_tc011_restriccion_acceso.py` (9 pruebas) y `test_tc012_mensajes_en_red.py` (11 pruebas) con servidor real y puerto libre.
3. Una correccion de J3: `--allow` reemplaza la lista por defecto en lugar de agregarse a ella.
4. Aclaracion del ADR-0008 (regla 1: sin valor `--listen` usa 127.0.0.1:7070 y sin `--listen` no hay puerto; regla 3: `--allow` reemplaza la lista).

## 4. Revision realizada

- La prueba de TC-011 del reparto (`--allow 10.0.0.0/8` y conectar desde 127.0.0.1 debe rechazar) no era posible con J3 tal como se entrego, porque el loopback siempre estaba permitido (IA-014). Se corrigio J3 y sus pruebas.
- Al probar 20 clientes simultaneos aparecieron respuestas `cola llena` (capacidad 10): es el comportamiento correcto, y la prueba se ajusto para exigir respuesta a todos.
- Una prueba leia la bitacora antes de que el servidor escribiera el rechazo; ahora espera hasta 3 s a que aparezca el evento. Las pruebas nuevas se repitieron 5 veces sin fallos.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Casos TC-011, TC-012 y TC-023 | Adoptados | Aceptado |
| Pruebas de red y acceso con servidor real | Adoptadas | Aceptado con ajustes |
| `--allow` reemplaza la lista por defecto | Adoptado; corrige IA-014 | Modificado |

## 6. Limitaciones del resultado de la IA

- 127.0.0.2 como "otro equipo" solo existe en Linux/WSL2; el rechazo desde otra maquina real se prueba en J8/J9.
- La inactividad de 30 s se prueba con un valor corto en prueba unitaria, no esperando 30 s reales.

## 7. Prueba o verificacion agregada

| Caso | Pruebas | Resultado |
|---|---|---|
| TC-011 | test_tc011_restriccion_acceso.py (9) | Cumple |
| TC-012 | test_tc012_mensajes_en_red.py (11) | Cumple |
| TC-023 | test_tc023_version_protocolo.py (PR #91) | Cumple |

**Verifico:** Josue Said Delgadillo Gutierrez (21/11/2026)

## 8. Aprendizaje

- Una lista "por defecto mas lo indicado" impide probar el rechazo del propio loopback; "lo indicado reemplaza a lo de defecto" es mas simple y mas facil de verificar.
- Las pruebas que leen la bitacora deben esperar el evento, no asumir que ya se escribio.
