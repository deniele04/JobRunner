# Registro de incidentes

Un incidente es una falla observada al operar o probar JobRunner que afecta al servicio. Cada uno tiene su propio archivo con síntomas, cómo reproducirlo, evidencia, causa, corrección y prueba de regresión.

## Índice

| ID | Título | Severidad | Requisitos | Corrección | Prueba de regresión | Estado |
|---|---|---|---|---|---|---|
| [INC-001](INC-001-caida-del-servidor-por-desconexion.md) | El servidor termina cuando un cliente se desconecta o envía bytes inválidos | Alta | RNF-08, RF-22, RF-28, RNF-30 | PR #51 | TC-019 | Corregido |

## Cómo registrar un incidente

1. Crear `INC-NNN-tema-corto.md` en esta carpeta, con el siguiente número libre y las secciones de INC-001: datos del incidente, síntomas, cómo reproducirlo, evidencia, hipótesis, causa, corrección, prueba de regresión y aprendizaje.
2. Guardar la evidencia (bitácora, salida de los comandos, `procesos.sh`) junto al análisis o en `verif/results/`.
3. Agregar su fila a este índice y, si deja un defecto o una limitación, registrarlo en [`docs/defectos-y-limitaciones.md`](../defectos-y-limitaciones.md).
4. Abrir una Issue con la plantilla de defecto (etiqueta `defecto`) y enlazar el PR de la corrección con `Closes #N`.

Para diagnosticar un incidente mientras ocurre, seguir la [guía de diagnóstico](../user-guide/diagnostico.md).
