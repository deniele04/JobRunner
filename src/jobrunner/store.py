"""Persistencia de trabajos en SQLite (ADR-0002).

Solo el servidor escribe en la base. Cada escritura se ejecuta en su propia
transaccion: o se guarda completa o no se guarda.
"""
import json
import sqlite3
from pathlib import Path

from .jobs import Job

ESQUEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id           TEXT PRIMARY KEY,
  request_id   TEXT UNIQUE,
  argv         TEXT NOT NULL,
  state        TEXT NOT NULL CHECK (state IN
               ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELED')),
  exit_code    INTEGER,
  error        TEXT,
  pid          INTEGER,
  created_at   TEXT NOT NULL,
  started_at   TEXT,
  finished_at  TEXT,
  stdout_path  TEXT,
  stderr_path  TEXT
)
"""

COLUMNAS = (
    "id", "request_id", "argv", "state", "exit_code", "error", "pid",
    "created_at", "started_at", "finished_at", "stdout_path", "stderr_path",
)

_SQL_GUARDAR = (
    "INSERT INTO jobs (" + ", ".join(COLUMNAS) + ") "
    "VALUES (" + ", ".join("?" for _ in COLUMNAS) + ") "
    "ON CONFLICT(id) DO UPDATE SET "
    + ", ".join(c + " = excluded." + c for c in COLUMNAS if c != "id")
)


def _a_job(fila):
    return Job(
        id=fila["id"],
        argv=json.loads(fila["argv"]),
        created_at=fila["created_at"],
        state=fila["state"],
        exit_code=fila["exit_code"],
        started_at=fila["started_at"],
        finished_at=fila["finished_at"],
        stdout_path=fila["stdout_path"],
        stderr_path=fila["stderr_path"],
        error=fila["error"],
        request_id=fila["request_id"],
        pid=fila["pid"],
    )


class Store:
    def __init__(self, ruta="data/jobrunner.db"):
        if ruta != ":memory:":
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(ruta)
        self._conn.row_factory = sqlite3.Row
        with self._conn:
            self._conn.execute(ESQUEMA)

    def save(self, job):
        """Inserta el trabajo, o actualiza el existente con el mismo id.

        Si el request_id ya pertenece a otro trabajo, lanza
        sqlite3.IntegrityError y no cambia nada.
        """
        valores = (
            job.id, job.request_id, json.dumps(job.argv), job.state,
            job.exit_code, job.error, job.pid, job.created_at,
            job.started_at, job.finished_at, job.stdout_path, job.stderr_path,
        )
        with self._conn:
            self._conn.execute(_SQL_GUARDAR, valores)

    def get(self, job_id):
        fila = self._conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        return _a_job(fila) if fila else None

    def get_by_request_id(self, request_id):
        if request_id is None:
            return None
        fila = self._conn.execute(
            "SELECT * FROM jobs WHERE request_id = ?", (request_id,)
        ).fetchone()
        return _a_job(fila) if fila else None

    def list(self, state=None):
        """Trabajos en orden de creacion, opcionalmente filtrados por estado."""
        sql = "SELECT * FROM jobs"
        params = ()
        if state is not None:
            sql += " WHERE state = ?"
            params = (state,)
        sql += " ORDER BY created_at, rowid"
        return [_a_job(f) for f in self._conn.execute(sql, params).fetchall()]

    def close(self):
        self._conn.close()