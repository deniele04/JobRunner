# Prueba entre equipos por VPN (Tailscale)

| Campo | Valor |
|---|---|
| Fecha | 2026-11-23 |
| Commit de main | a4d48aa |
| Red | Tailscale (100.64.0.0/10), sin puertos abiertos en el router |
| Servidor | Josué Said Delgadillo Gutiérrez, 100.90.230.53 |
| Cliente 1 | Daniel Alejandro Huerta Camberos, 100.102.244.92 |

| Prueba | Qué se comprobó | Requisitos | Resultado | Evidencia |
|---|---|---|---|---|
| Red | http.server y curl desde el cliente; tailscale ping directo de 4 ms | RNF-26 | PASS (verificado en vivo, antes de grabar) | — |
| P1 | No arranca con --listen 0.0.0.0 | RNF-12 | PASS | prueba-vpn-servidor.txt |
| P2 | --listen, --allow y health remoto | RF-16, RF-24 | PASS | health-daniel.json |
| P3 | submit, list, output, cancel, cola llena | RF-18, RF-19 | PASS (ver nota) | prueba-vpn-cliente-daniel.txt |
| P4 | Varios clientes a la vez | ADR-0009, RF-18 | No aplica (un solo cliente) | — |
| P5 | Origen no permitido rechazado | RF-20, RNF-13 | PASS | jobrunner.log |
| P6 | Cierre con clientes conectados | ADR-0006, RNF-30 | PASS (sin trabajos corriendo al cerrar) | jobrunner.log |

Notas: en P3 los sleep iniciales terminaron solos antes del primer cancel, que respondió que el trabajo ya había terminado; la cancelación de un trabajo en ejecución se mostró con un trabajo nuevo (CANCELED, exit_code -15). El trabajo en cola arrancó solo al liberarse un lugar.

Configuración usada: configuracion.txt
