"""Ejecuta las pruebas de verif/unit y verif/integration y guarda el resultado de cada una.

Uso: python3 verif/scripts/ejecutar_pruebas.py <archivo-resultados.tsv>

Imprime la salida detallada de unittest y escribe un archivo con una línea por
prueba ("PASS<TAB>id", "FAIL<TAB>id" o "XFAIL<TAB>id") que verify.sh usa para
calcular el estado de cada caso de prueba. XFAIL es un fallo esperado y
conocido (`expectedFailure`); un éxito inesperado cuenta como FAIL para que se
quite la marca. Termina con código 0 solo si todo pasa.
"""
import os
import sys
import unittest


class Resultado(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.estados = {}

    def _marcar(self, test, estado):
        # Una prueba con algún fallo nunca vuelve a PASS.
        if self.estados.get(test.id()) != "FAIL":
            self.estados[test.id()] = estado

    def addSuccess(self, test):
        super().addSuccess(test)
        self._marcar(test, "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._marcar(test, "FAIL")

    def addError(self, test, err):
        super().addError(test, err)
        self._marcar(test, "FAIL")

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._marcar(test, "XFAIL")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._marcar(test, "FAIL")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._marcar(test, "FAIL")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    suite = unittest.TestSuite()
    for directorio in ("verif/unit", "verif/integration"):
        if os.path.isdir(directorio):
            suite.addTests(unittest.defaultTestLoader.discover(directorio))
    # warnings="default" iguala el comportamiento de `python -m unittest`:
    # deja visibles avisos como ResourceWarning (archivos sin cerrar) en el log.
    runner = unittest.TextTestRunner(
        stream=sys.stdout, verbosity=2, resultclass=Resultado, warnings="default"
    )
    resultado = runner.run(suite)
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        for prueba, estado in sorted(resultado.estados.items()):
            f.write(f"{estado}\t{prueba}\n")
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
