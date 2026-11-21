# ADR-0008: Transporte de red y restricción de acceso

**Estado:** Propuesto
**Fecha:** 19/11/2026
**Responsable(s):** Josué Said Delgadillo Gutiérrez
**Issue relacionado:** #76
**Aprobado en:** PR #85
**Historial:** v1 (19/11/2026): propuesta para el Hito 3 (operación remota privada). Cierra la decisión abierta del ADR-0003.

## Contexto

Hasta el Avance 2 el servicio solo atiende clientes de la misma máquina, por un socket Unix (ADR-0003). El Hito 3 pide operación remota con el mismo protocolo, restringida a una red privada o a una VPN (RF-18, RF-19, RF-20, RNF-12, RNF-13, RNF-26). El servicio ejecuta comandos del sistema, así que un acceso remoto abierto equivale a ejecución remota de código para cualquiera que lo alcance.

Restricciones:
- Solo biblioteca estándar de Python (ADR-0001).
- El servicio no autentica usuarios ni cifra los mensajes por sí mismo.
- La demostración y las pruebas se hacen en localhost, en una LAN privada o por una VPN. Nunca se abre un puerto en el router (RNF-26).
- El equipo trabaja en Ubuntu sobre WSL2, donde la red de WSL puede no ser alcanzable desde otro equipo sin configuración adicional.

Si no se decide, la tentación es escuchar en `0.0.0.0` para "que funcione", lo que expone el servicio a cualquier red a la que esté conectado el equipo.

## Alternativas consideradas

1. **TCP con el mismo JSON de una línea, restringido por dirección y acompañado de una VPN (Tailscale)**
   - A favor: reutiliza el protocolo y el código ya probados (ADR-0003); no agrega dependencias; la restricción por dirección se implementa con el módulo estándar `ipaddress`; Tailscale cifra el tráfico y evita abrir puertos.
   - En contra: la restricción por dirección no autentica a las personas, solo a la red de origen; hay que configurar la VPN en cada equipo.
2. **HTTP (REST)**
   - A favor: estándar ampliamente conocido, con herramientas para depurarlo.
   - En contra: obliga a reescribir el protocolo y a mantener dos; agrega análisis de cabeceras y métodos que el proyecto no necesita; no resuelve por sí mismo el control de acceso.
3. **Abrir el puerto en el router (acceso desde Internet)**
   - A favor: permite conectarse desde cualquier lugar.
   - En contra: expone un servicio que ejecuta comandos a Internet, sin autenticación ni cifrado. Está prohibido por RNF-26.
4. **Token compartido dentro de cada mensaje, como defensa principal**
   - A favor: agrega una forma sencilla de autenticar al cliente.
   - En contra: el token viaja sin cifrar en una LAN sin VPN; hay que guardarlo, rotarlo y protegerlo; da una falsa sensación de seguridad si el puerto además está expuesto.

## Decisión

Se elige **TCP con el protocolo JSON de una línea, restringido a redes privadas por dirección de origen, y Tailscale como VPN recomendada** (alternativa 1). El token compartido no se adopta en el Hito 3 (ver Decisiones abiertas).

Reglas:
1. **Dirección de escucha:** `--listen HOST:PUERTO`, por defecto `127.0.0.1:7070`. El socket Unix sigue funcionando igual, sin cambios.
2. **Direcciones prohibidas al arrancar:** si `--listen` es `0.0.0.0`, `::` o una dirección pública, el servidor se niega a arrancar y explica por qué.
3. **Lista de redes permitidas:** `--allow RED`, repetible, en notación CIDR. Por defecto solo `127.0.0.1` y `::1`. Una red de `--allow` que sea pública, `0.0.0.0` o `::` también impide el arranque.
4. **Redes aceptables:** loopback, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` y `100.64.0.0/10` (el rango que usa Tailscale).
5. **Conexión desde una dirección no permitida:** se cierra sin leer nada, se registra `ERROR acceso_rechazado ip=<dirección>` en la bitácora y se cuenta para el resumen de salud (`health`).
6. **Cifrado:** el servicio no cifra. El cifrado lo da la VPN. En una LAN sin VPN el tráfico viaja en claro y se documenta como limitación.
7. **WSL2:** se usa Tailscale instalado dentro de WSL, o el modo de red `mirrored` de WSL. La prueba de conexión entre equipos (sin JobRunner) fija cuál funciona.

Razones técnicas:
- Una sola implementación del protocolo para Unix y TCP mantiene la misma semántica local y remota (RF-19).
- Negarse a arrancar con una configuración insegura evita el error más probable, que es escuchar en todas las interfaces (RNF-12).
- Limitar por dirección y usar una VPN cumple RF-20, RNF-13 y RNF-26 sin dependencias externas ni abrir puertos.

## Consecuencias

**Positivas**
- El servicio es seguro por defecto: solo escucha en loopback.
- El cliente remoto usa el mismo protocolo que el local.
- Cada acceso rechazado queda en la bitácora y se cuenta.

**Negativas**
- No hay autenticación de personas: quien llegue desde una red permitida puede enviar comandos.
- Sin VPN, el tráfico en una LAN no está cifrado.
- Configurar Tailscale en WSL agrega pasos a la demostración.

**Riesgos**
- Se expone el servicio por error escuchando en todas las interfaces o en una IP pública — Mitigación: rechazo al arrancar de `0.0.0.0`, `::` y direcciones públicas, tanto en `--listen` como en `--allow` — Prueba: TC-011.
- Un equipo de una red no permitida se conecta — Mitigación: lista `--allow`, cierre sin leer y evento `acceso_rechazado` — Prueba: TC-011.
- Un atacante en la misma LAN lee o modifica el tráfico — Mitigación: usar la VPN (Tailscale) para cualquier acceso entre equipos; documentar la limitación en la guía de seguridad — Prueba: inspección documental (RNF-16).
- Un cliente remoto no autorizado intenta saturar el servicio con conexiones o mensajes enormes — Mitigación: límite de 64 KiB por mensaje y cierre por 30 s de inactividad (ADR-0009) — Prueba: TC-012.
- La red de WSL no es alcanzable desde otro equipo — Mitigación: Tailscale dentro de WSL o modo `mirrored`, verificado antes de implementar — Prueba: evidencia de operación entre dos equipos en `verif/results/`.

## Decisiones abiertas

- Si se agrega un token compartido como defensa adicional. Queda fuera del Hito 3 y se retomará solo si el equipo decide que el control por red no basta.
- Configuración definitiva de WSL (Tailscale dentro de WSL o modo `mirrored`): se cierra con la prueba de conexión entre equipos.

## Requisitos afectados

RF-18, RF-19, RF-20, RNF-12, RNF-13, RNF-16, RNF-26, RNF-34

## Evidencia

- Pruebas que respaldarán la decisión: TC-011 (restricción de acceso) y la evidencia de operación entre dos equipos, que se guardará en `verif/results/<run-id>-remoto/`.
- Prueba previa sin JobRunner: `python3 -m http.server 7070 --bind <IP 100.x>` en un equipo y `curl` desde el otro.
