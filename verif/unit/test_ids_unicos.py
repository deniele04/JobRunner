"""Prueba de unicidad de los IDs de trabajo (criterio: "obtener un ID único").

Genera 2000 trabajos y comprueba que ningún ID se repita.

Estado conocido: esta prueba FALLA con el código actual (defecto DEF-001, ver
verif/verification-plan/matriz-trazabilidad.md). Job.new() usa
uuid.uuid4().hex[:4], es decir 4 caracteres hexadecimales: solo 65 536 IDs
posibles. Con 2000 IDs la probabilidad de que haya al menos uno repetido es
prácticamente 1 (paradoja del cumpleaños). Además, JobManager.submit() guarda
el trabajo en self._jobs[job.id], de modo que un ID repetido sobrescribe en
silencio al trabajo anterior.

No se marca como expectedFailure a propósito: debe fallar hasta que se corrija.
"""
import unittest

from jobrunner.jobs import Job


class IdsUnicosTest(unittest.TestCase):
    TOTAL = 2000

    def test_ids_unicos_en_2000_trabajos(self):
        ids = [Job.new(["true"]).id for _ in range(self.TOTAL)]
        repetidos = len(ids) - len(set(ids))
        self.assertEqual(
            repetidos,
            0,
            f"{repetidos} IDs repetidos entre {self.TOTAL} trabajos "
            f"(longitud de cada ID: {len(ids[0])} caracteres)",
        )


if __name__ == "__main__":
    unittest.main()
