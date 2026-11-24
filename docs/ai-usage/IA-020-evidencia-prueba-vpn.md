# IA-020 — Guía y revisión de la evidencia de la prueba entre equipos por VPN

| Campo | Valor |
|---|---|
| **Fecha** | 23/11/2026 |
| **Herramienta** | Claude |
| **Usado por** | Josué Said Delgadillo Gutiérrez |
| **Revisado por** | Pendiente de revisión |
| **Hito** | Hito 4 — Operación remota (entrega final) |
| **Artefactos afectados** | verif/results/20261123-remoto/ |
| **Clasificación** | En revisión |

## 1. Objetivo

Ejecutar J8 y J9 con el instructivo «Prueba entre equipos por VPN» (servidor: Josué, cliente: Daniel) y dejar la evidencia en verif/results/. Se usó la IA para guiar los pasos, interpretar las salidas y revisar la evidencia antes de subirla.

## 2. Entrada proporcionada

- El instructivo de la prueba, las salidas de los comandos de ambos equipos y el contenido de la carpeta de evidencia.

## 3. Resultado recibido

1. Pasos adaptados a un solo cliente (P4 no aplica; P5 con una IP permitida distinta de la del cliente).
2. Revisión de las salidas de P1 a P6 contra lo esperado.
3. Redacción de configuracion.txt y resumen.md.

## 4. Revisión realizada

- Se comprobó que la bitácora tiene el rechazo de la IP del cliente y red_cerrada con conexiones=1, y que ninguna grabación ni archivo contiene correos ni tailscale status.
- Se corrigió una línea de la configuración (P6 sí se inició con --max-jobs 2 --queue-size 1).
- Se corrigió la fila Red del resumen: la prueba con http.server y curl se hizo antes de grabar, por lo que no tiene archivo de evidencia.
- En P3 los sleep iniciales terminaron antes del primer cancel por el tiempo entre comandos; se repitió la cancelación con un trabajo nuevo y se anotó en el resumen.

## 5. Cambios aplicados

| Resultado de la IA | Decisión del equipo | Clasificación |
|---|---|---|
| Resumen y configuración de la prueba | Adoptados | Aceptado con ajustes |
| Fila Red con evidencia en la grabación | Corregida a verificación en vivo, sin archivo | Modificado |

## 6. Limitaciones del resultado de la IA

- Un solo cliente: P4 queda como No aplica.
- P6 se hizo sin trabajos corriendo al cerrar; el cierre con trabajos activos lo cubre TC-009.

## 7. Prueba o verificación agregada

| Caso | Verificación | Resultado |
|---|---|---|
| J8 y J9 | Carpeta verif/results/20261123-remoto/ | Cumple |

**Verificó:** Josué Said Delgadillo Gutiérrez (23/11/2026)

## 8. Aprendizaje

- La evidencia debe grabarse desde el primer paso que se quiere demostrar: lo que se hace antes de empezar a grabar no queda como evidencia.
- Con comandos de 120 s conviene cancelar de inmediato; si no, los trabajos terminan antes de poder cancelarlos.
