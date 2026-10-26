"""Bitácora de eventos del servicio (RF-14, RNF-22).

Escribe una línea por evento en <data_dir>/jobrunner.log con la fecha y hora en
UTC, el nivel, el tipo de evento y el ID del trabajo, por ejemplo:

    2026-10-25T18:30:00Z INFO iniciado job=7076f32d-... pid=2986

Solo registra el nombre del programa de cada trabajo, nunca sus argumentos ni
variables de entorno, para no exponer datos sensibles (RNF-15).

Mientras no se llame a configurar(), los eventos se descartan; así las pruebas
unitarias del ejecutor no escriben archivos.
"""
import logging
import time
from pathlib import Path

_logger = logging.getLogger("jobrunner")
_logger.addHandler(logging.NullHandler())
_logger.setLevel(logging.INFO)
_logger.propagate = False


def configurar(data_dir="data"):
    """Activa la bitácora en <data_dir>/jobrunner.log y devuelve su ruta."""
    cerrar()
    ruta = Path(data_dir) / "jobrunner.log"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    formato = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S")
    formato.converter = time.gmtime
    archivo = logging.FileHandler(ruta, encoding="utf-8")
    archivo.setFormatter(formato)
    _logger.addHandler(archivo)
    return ruta


def cerrar():
    """Cierra el archivo de la bitácora. Se llama al detener el servicio."""
    for handler in list(_logger.handlers):
        if isinstance(handler, logging.FileHandler):
            _logger.removeHandler(handler)
            handler.close()


def _valor(valor):
    texto = str(valor)
    return '"' + texto + '"' if " " in texto else texto


def _linea(tipo, job_id, detalles):
    partes = [tipo, "job=" + (job_id or "-")]
    partes += [clave + "=" + _valor(valor) for clave, valor in detalles.items()]
    return " ".join(partes)


def evento(tipo, job_id=None, **detalles):
    """Registra un evento normal. Ejemplo: evento("iniciado", job.id, pid=1234)."""
    _logger.info(_linea(tipo, job_id, detalles))


def error(tipo, job_id=None, **detalles):
    """Registra un error. Ejemplo: error("solicitud_invalida", motivo="JSON invalido")."""
    _logger.error(_linea(tipo, job_id, detalles))
