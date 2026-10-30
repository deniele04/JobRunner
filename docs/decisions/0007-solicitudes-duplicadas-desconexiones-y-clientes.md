# ADR-0007: Solicitudes duplicadas, desconexiones y clientes simultáneos

**Estado:** Propuesto
**Fecha:** 29/10/2026
**Responsable(s):** Daniel Alejandro Huerta Camberos
**Issue relacionado:** Por asignar
**Aprobado en:** Por asignar

## Contexto

En el Avance 2 varios clientes pueden usar el servicio al mismo tiempo, y el profesor pide que el sistema conserve un estado coherente ante solicitudes concurrentes, duplicadas o interrumpidas (RF-26, RF-27, RF-28). El documento de requisitos obliga a decidir y documentar dos comportamientos antes de implementarlos: el tratamiento de solicitudes duplicadas y el soporte para múltiples clientes simultáneos.

Restricciones:
- Solo biblioteca estándar de Python (ADR-0001).
- El servidor actual atiende una conexión a la vez, con un tiempo límite de lectura de 5 s.
- Hoy, si un cliente se desconecta antes de recibir la respuesta, el servidor termina. Lo detectamos el 07/10/2026 y se registrará como incidente INC-001.

Si no se decide, un reenvío por un error de red puede ejecutar dos veces el mismo trabajo, y dos clientes pueden dejar un trabajo en estados contradictorios.

## Alternativas consideradas

**A. Clientes simultáneos**

1. **Un hilo por cliente con candados**
   - A favor: varios clientes se atienden en paralelo.
   - En contra: hay que proteger con candados el gestor de trabajos y la base de datos; aparecen condiciones de carrera difíciles de probar y de explicar.
2. **Varias conexiones abiertas en un solo hilo (módulo `selectors`)**
   - A favor: un cliente lento no retrasa a los demás.
   - En contra: hay que manejar lecturas parciales de varias conexiones a la vez; más código para un beneficio que el Avance 2 no necesita.
3. **Atención secuencial con operaciones que no esperan**
   - A favor: las solicitudes nunca se intercalan, así que cada una ve y deja un estado completo, sin candados (RNF-27). Es simple de implementar, probar y explicar.
   - En contra: un cliente lento puede retrasar a los demás hasta el tiempo límite de lectura (5 s).

**B. Solicitudes duplicadas**

1. **Sin detección de duplicados:** cada `submit` crea un trabajo nuevo.
   - A favor: no requiere cambios.
   - En contra: un reenvío por un error de red ejecuta dos veces el mismo comando.
2. **Detectar duplicados por contenido** (mismo comando en pocos segundos)
   - A favor: el cliente no tiene que hacer nada.
   - En contra: bloquea envíos repetidos que sí son intencionales, y la ventana de tiempo es arbitraria.
3. **Identificador de solicitud opcional (`request_id`) que envía el cliente**
   - A favor: el cliente decide qué es un reenvío; es simple y se puede probar.
   - En contra: si el cliente no lo envía, no hay protección contra duplicados.

## Decisión

Se eligen la **atención secuencial con operaciones que no esperan** (A3) y el **identificador de solicitud opcional** (B3), con estas reglas:

1. **Clientes simultáneos:** el servidor atiende una solicitud a la vez. Ninguna operación espera: la lectura tiene un tiempo límite de 5 s y la cancelación responde de inmediato (ADR-0006). Los demás clientes esperan su turno en la cola de conexiones del socket.
2. **Duplicados en `submit`:**
   - Sin `request_id`, cada solicitud crea un trabajo nuevo.
   - Con un `request_id` ya registrado y el mismo comando, se devuelve el trabajo existente con `"duplicado": true` y no se crea otro.
   - Con un `request_id` ya registrado y un comando distinto, se rechaza con un error explícito.
   - El `request_id` es texto de 1 a 64 caracteres (letras, números, `-` y `_`) y se guarda en SQLite, así que la regla sigue funcionando después de reiniciar (ADR-0002, ADR-0005).
3. **Duplicados en `status`, `list` y `cancel`:** consultar nunca cambia el estado. Una segunda cancelación del mismo trabajo responde con su estado real, sin cambiarlo (RF-26, ADR-0006).
4. **Desconexión durante una solicitud (RF-28):**
   - Una solicitud **incompleta** (sin salto de línea al cerrarse la conexión o al vencer el tiempo límite) **no tiene efecto**, y se registra en la bitácora.
   - Una solicitud **completa se aplica** aunque el cliente se desconecte antes de leer la respuesta. El servidor no termina: el error al enviar la respuesta se ignora y se registra en la bitácora.
   - Para saber si su solicitud se aplicó, el cliente consulta con `status` o `list`, o la reenvía con el mismo `request_id` sin riesgo de duplicarla.

Razones técnicas:
- Con atención secuencial, dos solicitudes nunca modifican el mismo trabajo al mismo tiempo, lo que garantiza transiciones consistentes (RF-26, RNF-27) sin candados.
- El `request_id` da una regla clara y verificable para los duplicados (RF-27), y junto con la regla de desconexión deja documentado qué pasa con una solicitud interrumpida (RF-28).

Implementación: Josué (`request_id` y manejo de desconexiones en el servidor) y Juan (cancelación que no espera, ADR-0006).

## Consecuencias

**Positivas**
- No hay estados contradictorios por solicitudes concurrentes.
- Un reenvío con el mismo `request_id` no ejecuta dos veces el mismo trabajo.
- Un cliente que se desconecta ya no termina el servicio (RNF-08).

**Negativas**
- Un cliente lento puede retrasar a los demás hasta 5 s.
- La protección contra duplicados depende de que el cliente envíe el `request_id`.

**Riesgos**
- Un cliente lento o inactivo retrasa a todos — Mitigación: tiempo límite de lectura de 5 s y operaciones que no esperan — Prueba: TC-019.
- Dos cancelaciones del mismo trabajo dejan estados contradictorios — Mitigación: atención secuencial y transiciones validadas — Prueba: TC-017.
- Se reutiliza un `request_id` para otro comando — Mitigación: rechazo explícito — Prueba: TC-018.
- El cliente pierde la respuesta al desconectarse — Mitigación: la solicitud completa se aplica y se puede confirmar con `status` o con el mismo `request_id` — Prueba: TC-019.

## Decisiones abiertas

Si la atención secuencial es suficiente con clientes remotos (Hito 3). Se revisará al definir el protocolo TCP.

## Requisitos afectados

RF-22, RF-26, RF-27, RF-28, RNF-08, RNF-27, RNF-29, RNF-34

## Evidencia

- Comportamiento actual (07/10/2026): un cliente que se desconecta antes de recibir la respuesta termina el servidor con `BrokenPipeError`. Se documentará en `docs/incidents/` como INC-001.
- Pruebas que respaldarán la decisión: TC-017 (cancelaciones concurrentes), TC-018 (solicitud duplicada) y TC-019 (desconexión durante una solicitud).
