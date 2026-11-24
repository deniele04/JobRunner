# Registro manual de TC-015: usabilidad documental

Este caso no se puede automatizar entero: comprueba que una persona **ajena a la parte que escribió la guía** puede instalar y usar JobRunner solo con el README y la guía de usuario, y que los mensajes de error le dicen qué hacer. `verify.sh` lee la tabla de abajo: mientras el estado sea `Pendiente`, o falte quién lo evaluó o la evidencia, TC-015 queda `BLOCKED`.

Requisitos: RNF-23 (guía de usuario sin asistencia del equipo), RNF-21 (mensajes de error con operación, causa y acción) y RF-17 (ayuda de uso y códigos de salida). La parte automática (la ayuda lleva el nombre `royito` y los códigos de salida del cliente) la ejecuta `verify.sh` con pruebas.

| Campo | Valor |
|---|---|
| **Estado** | Pendiente |
| **Evaluó** | |
| **Fecha** | |
| **Versión probada (commit)** | |
| **Evidencia** | |

`Estado` es `PASS`, `FAIL` o `Pendiente`. Con `PASS` o `FAIL` hay que llenar también `Evaluó` y `Evidencia` (por ejemplo, la ruta de una captura o de las notas en `verif/results/<run-id>/`).

## Procedimiento

1. La persona evaluadora (idealmente del otro equipo, durante la verificación cruzada) parte de un clon limpio y sigue **solo** el README y la [guía de usuario](../../docs/user-guide/guia-de-usuario.md), sin ayuda del equipo.
2. Instala, arranca el servicio y usa `royito submit`, `status`, `list`, `cancel` y, cuando existan, `output` y `health`.
3. Provoca estos errores y anota cada mensaje: un ID que no existe, un comando que no existe y la cola llena.
4. Para cada mensaje de error responde: ¿dice qué operación falló, por qué y qué hacer?

| Pregunta | Respuesta |
|---|---|
| ¿Instaló y arrancó sin pedir ayuda? | |
| ¿Completó las cuatro operaciones y, si existen, `output` y `health`? | |
| ¿El mensaje de «ID que no existe» dice operación, causa y acción? | |
| ¿El mensaje de «comando que no existe» dice operación, causa y acción? | |
| ¿El mensaje de «cola llena» dice operación, causa y acción? | |
| Dudas o pasos donde se atoró | |

## Criterio

`PASS` si completó todo sin asistencia y los tres mensajes dicen operación, causa y acción. Cualquier ayuda del equipo, o un mensaje que no diga qué hacer, es `FAIL`: se registra como defecto (Issue «[Defecto]» y la matriz de trazabilidad) y se corrige la guía o el mensaje.
