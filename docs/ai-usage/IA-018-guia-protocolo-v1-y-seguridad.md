# IA-018 — Guia tecnica del protocolo v1 y de seguridad

| Campo | Valor |
|---|---|
| **Fecha** | 22/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josue Said Delgadillo Gutierrez |
| **Revisado por** | Pendiente de revision |
| **Hito** | Hito 4 - Operacion remota (entrega final) |
| **Artefactos afectados** | docs/technical-guide/protocolo-y-persistencia.md, docs/technical-guide/seguridad.md |
| **Clasificacion** | En revision |

## 1. Objetivo

Implementar la tarea J7: actualizar la guia del protocolo (transportes Unix y TCP, campo `v`, delimitacion, limites, comandos, errores e historial de versiones) y escribir la guia de seguridad (RNF-16) con amenazas, mitigaciones y pruebas. Se uso la IA para redactar a partir del codigo y de los ADR-0008 y ADR-0009.

## 2. Entrada proporcionada

- La guia anterior, `server.py`, `red.py`, `cli.py` y `executor.py` ya integrados, ADR-0008 y ADR-0009, y los casos TC-011, TC-012 y TC-023.

## 3. Resultado recibido

1. Guia del protocolo reescrita en su seccion 1 (10 subsecciones), con un cliente minimo en Python.
2. Guia de seguridad nueva: activos, modelo, tabla de 8 amenazas con mitigacion y prueba, riesgos aceptados y eventos de bitacora.
3. La guia anterior estaba desactualizada (decia una solicitud por conexion y servidor de una conexion a la vez); se corrigio.

## 4. Revision realizada

- Cada mensaje de error, limite y valor por defecto se comparo con el codigo (64 KiB, 30 s, cola de 10, 3 trabajos, formato de `request_id`).
- Cada prueba citada en la tabla de amenazas se busco por nombre en el repositorio.
- Los enlaces entre documentos se revisaron.

## 5. Cambios aplicados

| Resultado de la IA | Decision del equipo | Clasificacion |
|---|---|---|
| Guia del protocolo v1 con errores, limites y ejemplo de cliente | Adoptada | Aceptado |
| Guia de seguridad con amenazas, pruebas y riesgos aceptados | Adoptada | Aceptado |
| Comandos `output` y `health` | Se dejan marcados como pendientes hasta integrar el trabajo del cliente (U2) | Modificado |

## 6. Limitaciones del resultado de la IA

- `output` y `health` no existen aun en el servidor; la seccion 1.8 debe completarse al integrarlos.
- La guia de seguridad describe el control por red; una revision de la configuracion real de WSL/Tailscale queda para J8.

## 7. Prueba o verificacion agregada

| Caso | Verificacion | Resultado |
|---|---|---|
| RNF-16 | Inspeccion documental de seguridad.md contra el ADR-0008 | Pendiente de revision por Diego (D3) |

**Verifico:** Josue Said Delgadillo Gutierrez (22/11/2026)

## 8. Aprendizaje

- Una guia de protocolo se valida mejor escribiendo un cliente solo con ella: el ejemplo minimo obligo a precisar que hay que leer hasta el salto de linea.
- Conviene citar en el documento de seguridad el nombre exacto de cada prueba, para que la inspeccion sea comprobable.
