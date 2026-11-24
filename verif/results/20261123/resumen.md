# Resumen de la ejecución 20261123

| TC | Estado | Evidencia |
|---|---|---|
| TC-001 | PASS | unittest.log, unit-resultados.tsv. Unicidad de 2000 IDs (unitaria): PASS |
| TC-002 | PASS | unittest.log, unit-resultados.tsv |
| TC-003 | PASS | unittest.log, unit-resultados.tsv |
| TC-004 | PASS | unittest.log, unit-resultados.tsv |
| TC-005 | PASS | unittest.log, unit-resultados.tsv |
| TC-006 | PASS | unittest.log, unit-resultados.tsv |
| TC-007 | PASS | unittest.log, unit-resultados.tsv |
| TC-008 | PASS | unittest.log, unit-resultados.tsv |
| TC-009 | PASS | unittest.log, unit-resultados.tsv, procesos.log |
| TC-010 | PASS | unittest.log. Si es BLOCKED falta verif/results/<run-id>-remoto/ (evidencia entre dos equipos, Josué y Diego) o falla alguna prueba |
| TC-011 | PASS | unittest.log, unit-resultados.tsv (acceso por red probado en 127.0.0.1) |
| TC-012 | PASS | unittest.log, unit-resultados.tsv |
| TC-013 | PASS | unittest.log, unit-resultados.tsv |
| TC-014 | PASS | tc-014-clon-limpio.log |
| TC-015 | BLOCKED | unittest.log, manual-TC-015.md. Si es BLOCKED falta llenar el registro de la persona evaluadora |
| TC-016 | PASS | unittest.log, unit-resultados.tsv |
| TC-017 | PASS | unittest.log, unit-resultados.tsv |
| TC-018 | PASS | unittest.log, unit-resultados.tsv |
| TC-019 | PASS | unittest.log, unit-resultados.tsv |
| TC-020 | PASS | unittest.log, unit-resultados.tsv |
| TC-021 | PASS | unittest.log, unit-resultados.tsv |
| TC-022 | PASS | unittest.log, unit-resultados.tsv |
| TC-023 | PASS | unittest.log, unit-resultados.tsv |
| TC-024 | PASS | unittest.log, unit-resultados.tsv |
| TC-025 | PASS | unittest.log, unit-resultados.tsv |
| TC-026 | PASS | unittest.log, unit-resultados.tsv |
| INS-016 | PASS | inspecciones.log (RNF-16). Si es BLOCKED falta seguridad.md (Josué) |
| INS-017 | PASS | inspecciones.log (RNF-17) |
| INS-018 | PASS | inspecciones.log (RNF-18) |
| INS-034 | PASS | inspecciones.log (RNF-34) |
| Sin zombis ni huérfanos tras las pruebas | PASS | procesos.log |
| procesos.sh detecta zombis y huérfanos, también adoptados por otro proceso (DEF-005) | PASS | unittest.log, unit-resultados.tsv |

Fallos esperados y conocidos (expectedFailure): 0. Ver las pruebas con estado XFAIL en unit-resultados.tsv y la matriz de trazabilidad.
