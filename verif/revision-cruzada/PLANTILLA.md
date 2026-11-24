# VC-NN: título corto del defecto

| Campo | Valor |
|---|---|
| **Identificador** | VC-NN |
| **Issue** | #N (`[Defecto] VC-NN`) |
| **Reportó** | Nombre y equipo de quien lo encontró |
| **Fecha del reporte** | DD/MM/AAAA |
| **Versión probada (commit)** | Hash completo |
| **Módulo afectado** | `archivo.py` |
| **Responsable** | Nombre |
| **Severidad** | Alta, Media o Baja (ver sección 8 del plan) |
| **Requisitos o casos afectados** | RF-NN, RNF-NN, TC-NNN |
| **Respuesta** | Corregido, No es defecto o Limitación aceptada |
| **Estado** | Abierto, En corrección o Cerrado |

## 1. Reporte

Lo que escribió o mostró el otro equipo, sin interpretarlo.

- **Qué hizo** (comandos exactos, en orden):
- **Qué esperaba:**
- **Qué pasó** (salida, mensaje de error, fragmento de la bitácora):
- **Entorno** (sistema, Python, local o remoto):

## 2. Análisis

- **¿Se reproduce?** Cómo se reprodujo y con qué frecuencia.
- **Causa:**
- **Clasificación:** defecto, limitación o uso incorrecto, y por qué.
- **Requisito, ADR o documento que lo define:**

## 3. Respuesta

Según la respuesta elegida, completar solo una de las tres:

**Corregido.** PR de la corrección: #N. Qué cambió:

**No es defecto.** Qué requisito, ADR o documento muestra que el comportamiento es el esperado. Qué se aclara en la guía, si algo:

**Limitación aceptada.** Quién lo decidió, por qué se acepta y su entrada en la lista de limitaciones y en las release notes:

## 4. Regresiones ejecutadas

| Prueba | Qué comprueba | Resultado | Ejecución |
|---|---|---|---|
| `test_...` (nueva, falla sin la corrección) | | PASS | `./scripts/test.sh`, DD/MM/AAAA |
| Pruebas del caso afectado (`TC-NNN`) | | PASS | |
| `verify.sh` completo, si se tocó un módulo compartido | | PASS | `verif/results/<run-id>/` |

## 5. Cierre

- [ ] El defecto pasó a «Cerrado» en la matriz y en la lista de defectos.
- [ ] La fila de este defecto en `verif/revision-cruzada/README.md` está al día.
- [ ] La Issue está cerrada con `Closes #N` en el PR.
