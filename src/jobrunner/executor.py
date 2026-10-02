import os
import signal
import subprocess
from pathlib import Path

from .jobs import (
    Job, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED, FINAL_STATES, now_iso,
)


class JobManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._jobs = {}    # id -> Job
        self._procs = {}   # id -> subprocess.Popen

    def submit(self, argv):
        job = Job.new(argv)
        job.stdout_path = str(self.data_dir / f"{job.id}.out")
        job.stderr_path = str(self.data_dir / f"{job.id}.err")
        self._jobs[job.id] = job

        job.transition(RUNNING)
        job.started_at = now_iso()

        out = open(job.stdout_path, "wb")
        err = open(job.stderr_path, "wb")
        proc = subprocess.Popen(
            argv, shell=False, stdout=out, stderr=err, start_new_session=True
        )
        self._procs[job.id] = proc
        return job.to_dict()

    def get(self, job_id):
        job = self._jobs.get(job_id)
        return job.to_dict() if job else None

    def list(self, state=None):
        jobs = self._jobs.values()
        if state is not None:
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
            if job.state == RUNNING:
                job.transition(SUCCEEDED if code == 0 else FAILED)