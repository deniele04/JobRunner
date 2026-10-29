import collections
import os
import signal
import subprocess
import time
from pathlib import Path

from . import bitacora
from .jobs import (
    Job, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED, FINAL_STATES, now_iso,
)

VALID_STATES = {QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED}

DEFAULT_MAX_JOBS = 3      # trabajos corriendo a la vez (ADR-0004)
DEFAULT_QUEUE_SIZE = 10   # trabajos esperando en la cola (ADR-0004)


class ColaLlena(Exception):
    """No hay lugar para correr ni para esperar: la solicitud se rechaza."""


class JobManager:
    def __init__(self, data_dir="data", store=None,
                 max_jobs=DEFAULT_MAX_JOBS, queue_size=DEFAULT_QUEUE_SIZE):
        if not isinstance(max_jobs, int) or max_jobs < 1:
            raise ValueError("max_jobs debe ser un entero de al menos 1")
        if not isinstance(queue_size, int) or queue_size < 0:
            raise ValueError("queue_size debe ser un entero no negativo")
        self.max_jobs = max_jobs
        self.queue_size = queue_size
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._jobs = {}    # id -> Job
        self._procs = {}   # id -> subprocess.Popen
        self._cola = collections.deque()   # ids en QUEUED, en orden de llegada
        self._store = store

    def _guardar(self, job):
        if self._store is not None:
            self._store.save(job)

    def recuperar(self):
        """Carga el historial guardado y reconcilia lo que quedo a medias (ADR-0005).

        Los QUEUED vuelven a la cola, en su orden original; los RUNNING pasan a FAILED y, si su grupo
        de procesos sigue vivo, se termina. Los estados finales no se tocan.
        """
        if self._store is None:
            return
        for job in self._store.list():
            self._jobs[job.id] = job
            if job.state == RUNNING:
                self._terminar_grupo(job.pid)
                job.error = "interrumpido por reinicio"
                job.finished_at = now_iso()
                job.transition(FAILED)
                self._guardar(job)
                bitacora.evento("recuperado", job.id, estado=FAILED, motivo="interrumpido por reinicio")
            elif job.state == QUEUED:
                bitacora.evento("recuperado", job.id, estado=QUEUED)
                self._cola.append(job.id)   # mismo orden y mismo limite (ADR-0004)
        self.tick()   # arranca de la cola solo lo que quepa en max_jobs

    @staticmethod
    def _terminar_grupo(pid, espera=5.0):
        if not pid:
            return
        try:
            os.killpg(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            return
        limite = time.monotonic() + espera
        while time.monotonic() < limite:
            try:
                os.killpg(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.1)
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def submit(self, argv, request_id=None):
        if not isinstance(argv, (list, tuple)) or not argv:
            raise ValueError("argv debe ser una lista no vacia de strings, p. ej. ['sleep', '5']")
        if not all(isinstance(a, str) and a for a in argv):
            raise ValueError("argv debe contener solo strings no vacios")

        if request_id is not None and not (isinstance(request_id, str) and request_id):
            raise ValueError("request_id debe ser un string no vacio")
        if request_id is not None:
            for existente in self._jobs.values():
                if existente.request_id == request_id:
                    bitacora.evento("duplicado", existente.id, request_id=request_id)
                    return existente.to_dict()

        # Primero se da su lugar a los que ya esperan: asi nadie se salta la cola.
        self._arrancar_de_la_cola()
        hay_lugar = len(self._procs) < self.max_jobs
        if not hay_lugar and len(self._cola) >= self.queue_size:
            # Sin lugar para correr ni para esperar: se rechaza y NO se crea el
            # trabajo (ADR-0004).
            bitacora.error("rechazado", motivo="cola llena", programa=argv[0])
            raise ColaLlena(
                "cola llena (capacidad " + str(self.queue_size) + "); intenta mas tarde"
            )

        job = Job.new(argv)
        job.request_id = request_id
        job.stdout_path = str(self.data_dir / (job.id + ".out"))
        job.stderr_path = str(self.data_dir / (job.id + ".err"))
        self._jobs[job.id] = job
        bitacora.evento("recibido", job.id, programa=argv[0])
        if hay_lugar:
            self._iniciar(job)
        else:
            self._cola.append(job.id)
            self._guardar(job)   # queda como QUEUED y sobrevive a un reinicio
            bitacora.evento("en_cola", job.id, posicion=len(self._cola))
        return job.to_dict()

    def _arrancar_de_la_cola(self):
        """Saca de la cola, en orden, mientras haya lugar para correr."""
        while self._cola and len(self._procs) < self.max_jobs:
            job = self._jobs[self._cola.popleft()]
            if job.state != QUEUED:   # se cancelo mientras esperaba
                continue
            self._iniciar(job)

    def _iniciar(self, job):
        job.transition(RUNNING)
        job.started_at = now_iso()

        try:
            with open(job.stdout_path, "wb") as out, open(job.stderr_path, "wb") as err:
                proc = subprocess.Popen(
                    job.argv, shell=False, stdout=out, stderr=err, start_new_session=True
                )
            self._procs[job.id] = proc
            job.pid = proc.pid
            bitacora.evento("iniciado", job.id, pid=proc.pid)
        except OSError as e:
            job.error = "No se pudo ejecutar " + repr(job.argv[0]) + ": " + str(e)
            job.finished_at = now_iso()
            job.transition(FAILED)
            bitacora.error("no_se_pudo_iniciar", job.id, motivo=e.strerror or str(e))
        self._guardar(job)

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
                bitacora.evento("terminado", job_id, estado=job.state, codigo=code)
            self._guardar(job)

    def tick(self):
        """Ciclo del servidor, cada 0.5 s (ADR-0004). Nunca bloquea.

        1. poll(): recoge los procesos que terminaron.
        2. arranca trabajos de la cola mientras haya lugar.
        """
        self.poll()
        self._arrancar_de_la_cola()

    def cancel(self, job_id):
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError("No existe el trabajo " + str(job_id))
        self.poll()
        if job.state in FINAL_STATES:
            raise ValueError("El trabajo " + str(job_id) + " ya termino en estado " + job.state + "; no se puede cancelar")

        if job.state == QUEUED:
            try:
                self._cola.remove(job_id)   # libera su lugar en la cola
            except ValueError:
                pass
            job.transition(CANCELED)
            job.finished_at = now_iso()
            bitacora.evento("cancelado", job_id, estado_previo=QUEUED)
            self._guardar(job)
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
        bitacora.evento("cancelado", job_id, codigo=job.exit_code)
        self._guardar(job)
        return job.to_dict()
