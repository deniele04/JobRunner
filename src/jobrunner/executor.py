import os
import signal
import subprocess
from pathlib import Path

from .jobs import (
    Job, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED, FINAL_STATES, now_iso,
)

VALID_STATES = {QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED}


class JobManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._jobs = {}    # id -> Job
        self._procs = {}   # id -> subprocess.Popen

    def submit(self, argv):
        if not isinstance(argv, (list, tuple)) or not argv:
            raise ValueError("argv debe ser una lista no vacia de strings, p. ej. ['sleep', '5']")
        if not all(isinstance(a, str) and a for a in argv):
            raise ValueError("argv debe contener solo strings no vacios")

        job = Job.new(argv)
        job.stdout_path = str(self.data_dir / (job.id + ".out"))
        job.stderr_path = str(self.data_dir / (job.id + ".err"))
        self._jobs[job.id] = job

        job.transition(RUNNING)
        job.started_at = now_iso()

        try:
            with open(job.stdout_path, "wb") as out, open(job.stderr_path, "wb") as err:
                proc = subprocess.Popen(
                    argv, shell=False, stdout=out, stderr=err, start_new_session=True
                )
            self._procs[job.id] = proc
        except OSError as e:
            job.error = "No se pudo ejecutar " + repr(argv[0]) + ": " + str(e)
            job.finished_at = now_iso()
            job.transition(FAILED)
        return job.to_dict()

    def get(self, job_id):
        job = self._jobs.get(job_id)
        return job.to_dict() if job else None

    def list(self, state=None):
        jobs = self._jobs.values()
        if state is not None:
            state = state.upper()
            if state not in VALID_STATES:
                raise ValueError("Estado desconocido: " + state)
            jobs = [j for j in jobs if j.state == state]
        return [j.to_dict() for j in jobs]

    def poll(self):
        for job_id, proc in list(self._procs.items()):
            code = proc.poll()
            if code is None:
                continue
            job = self._jobs[job_id]
            del self._procs[job_id]
            job.exit_code = code
            job.finished_at = now_iso()
            if code < 0:
                job.error = signal.Signals(-code).name
            if job.state == RUNNING:
                job.transition(SUCCEEDED if code == 0 else FAILED)

    def cancel(self, job_id):
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError("No existe el trabajo " + str(job_id))
        if job.state in FINAL_STATES:
            raise ValueError("El trabajo " + str(job_id) + " ya termino en estado " + job.state + "; no se puede cancelar")

        if job.state == QUEUED:
            job.transition(CANCELED)
            job.finished_at = now_iso()
            return job.to_dict()

        proc = self._procs[job_id]
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()

        del self._procs[job_id]
        job.exit_code = proc.returncode
        job.finished_at = now_iso()
        job.transition(CANCELED)
        return job.to_dict()