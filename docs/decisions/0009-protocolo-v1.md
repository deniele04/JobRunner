# ADR-0009: Protocolo v1: versión, delimitación, límites y varios clientes

**Estado:** Propuesto
**Fecha:** 19/11/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez
**Issue relacionado:** #76
**Aprobado en:** PR #85
**Historial:** v1 (19/11/2026): propuesta para el Hito 3. Formaliza el protocolo que ya usa el socket Unix y lo extiende a TCP.

## Contexto

El protocolo actual es un JSON de una línea por solicitud, y el servidor atiende una conexión a la vez con un tiempo límite de lectura de 5 s (ADR-0003, ADR-0007). Con clientes remotos aparecen problemas que en local no se ven: mensajes que llegan en pedazos, varias solicitudes en una misma conexión, mensajes enormes, clientes lentos que no cierran la conexión y clientes de versiones distintas (RF-21, RF-22, RNF-14, RNF-24, RNF-32).

Restricciones:
- Solo biblioteca estándar de Python (ADR-0001).
- Los estados se cambian en un solo lugar (`JobManager`), sin candados (ADR-0007).
- El ciclo del servidor debe seguir revisando los procesos cada 0.5 s (ADR-0004, ADR-0006).
- Los mensajes JSON de una línea ya existen y están probados; cambiarlos obligaría a reescribir cliente, servidor y pruebas.

Si no se decide, un mensaje partido en dos lecturas se interpreta como inválido, un cliente inactivo bloquea a los demás y un cliente nuevo habla con un servidor viejo sin saberlo.

## Alternativas consideradas

**A. Formato de los mensajes**

1. **JSON de una línea terminada en `\n`, con un búfer por conexión**
   - A favor: es el formato actual; se depura con `nc` o `socat`; la delimitación es trivial.
   - En contra: hay que fijar un tamaño máximo para que una línea sin salto de línea no crezca sin límite.
2. **Prefijo de longitud binario**
   - A favor: no hay ambigüedad sobre dónde termina un mensaje.
   - En contra: no se puede depurar a mano, rompe el formato actual y obliga a reescribir cliente y pruebas.
3. **HTTP**
   - A favor: estándar.
   - En contra: descartado en ADR-0008.

**B. Atención de varios clientes** (revisa la decisión A3 del ADR-0007)

1. **Un hilo por cliente con candados**
   - A favor: paralelismo real entre clientes.
   - En contra: obliga a proteger el gestor de trabajos y la base; condiciones de carrera difíciles de probar.
2. **Un solo hilo con varias conexiones abiertas (`selectors`)**
   - A favor: un cliente lento no retrasa a los demás; los estados se siguen cambiando en un solo hilo y en un solo lugar, sin candados; conserva el ciclo de 0.5 s.
   - En contra: hay que manejar lecturas parciales de varias conexiones a la vez.
3. **Atención secuencial de una conexión a la vez**
   - A favor: es lo que hay hoy.
   - En contra: un cliente remoto lento puede retrasar a todos.

## Decisión

Se eligen el **JSON de una línea con un búfer por conexión** (A1) y **un solo hilo con `selectors`** (B2), con estas reglas:

1. **Versión:** cada solicitud puede llevar el campo `v`. Si falta, se toma como `1`. Si es distinto de `1`, el servidor responde `{"v": 1, "error": "version de protocolo no soportada: N (soportada: 1)"}`. Todas las respuestas incluyen `"v": 1`.
2. **Delimitación:** cada mensaje termina en `\n`. El servidor guarda un búfer por conexión y procesa cada línea completa, aunque haya llegado en varias lecturas.
3. **Varias solicitudes por conexión:** el cliente puede enviar varias líneas en la misma conexión y el servidor las responde en orden.
4. **Tamaño máximo:** 64 KiB por mensaje. Si una línea lo supera sin llegar a `\n`, el servidor responde con un error y cierra la conexión.
5. **Inactividad:** una conexión sin datos durante 30 s se cierra.
6. **Una solicitud completa se ejecuta de una vez:** aunque haya varias conexiones abiertas, el servidor ejecuta una solicitud completa a la vez y sin intercalarla con otra. Los estados se siguen cambiando solo en `JobManager`.
7. **Ciclo del servidor:** `manager.tick()` se sigue ejecutando cada 0.5 s, incluso cuando no llegan solicitudes.
8. **Comandos:** a `submit`, `status`, `list` y `cancel` se suman `output` (leer la salida de un trabajo) y `health` (resumen de salud del servicio, con el número de accesos rechazados). El formato exacto de sus respuestas se documenta en la guía técnica del protocolo.
9. **Mismo protocolo para Unix y TCP:** las reglas valen para ambos transportes.

Razones técnicas:
- El mismo formato de mensajes mantiene la semántica local y remota (RF-19, RF-21) sin reescribir lo que ya está probado.
- Los límites de tamaño y de inactividad impiden que un cliente remoto agote la memoria o retenga conexiones (RNF-14).
- `selectors` resuelve el cliente lento sin candados ni hilos, y conserva la garantía de estados coherentes (RF-26, RNF-27).
- El campo `v` permite que un cliente detecte un servidor incompatible en lugar de fallar de forma confusa (RNF-32).

## Consecuencias

**Positivas**
- Un mensaje fragmentado o varias solicitudes en una conexión funcionan sin cambios para el cliente.
- Un cliente lento o inactivo ya no retrasa a los demás.
- Los clientes de versiones distintas reciben un error claro.

**Negativas**
- El servidor es más complejo que con la atención secuencial: un búfer y un reloj de inactividad por conexión.
- El código de salida del CLI hoy depende de que la respuesta tenga solo la clave `error`; con `v` en todas las respuestas esa regla debe ajustarse.
- Un mensaje legítimo mayor de 64 KiB se rechaza.

**Riesgos**
- Una línea sin `\n` crece sin límite en memoria — Mitigación: límite de 64 KiB y cierre de la conexión — Prueba: TC-012.
- Un cliente lento o inactivo retiene la conexión — Mitigación: cierre a los 30 s y atención con `selectors`, que no se bloquea en una conexión — Prueba: TC-012.
- Un mensaje llega partido en varias lecturas y se interpreta mal — Mitigación: búfer por conexión que corta solo en `\n` — Prueba: TC-012.
- Un cliente envía una versión de protocolo desconocida — Mitigación: error explícito con la versión soportada — Prueba: TC-023.
- Dos solicitudes de conexiones distintas dejan un trabajo en estados contradictorios — Mitigación: una solicitud completa se ejecuta de una vez y los estados solo cambian en `JobManager` — Prueba: TC-017.
- El ajuste del código de salida del CLI queda fuera de sincronía — Mitigación: acordarlo con quien mantiene el cliente antes de integrar — Prueba: TC-001 y TC-004.

## Decisiones abiertas

- Formato definitivo de las respuestas de `output` y `health`: lo propone quien implementa el cliente remoto y se documenta en la guía técnica.
- Política de evolución de versiones (qué hacer cuando exista una `v2`): fuera del alcance de este hito.

## Requisitos afectados

RF-18, RF-19, RF-21, RF-22, RF-24, RNF-14, RNF-24, RNF-32, RNF-34

## Evidencia

- Pruebas que respaldarán la decisión: TC-012 (mensajes fragmentados, varias solicitudes, mensaje enorme, cliente que se va a la mitad), TC-023 (versión del protocolo) y TC-017 (cancelaciones concurrentes).
