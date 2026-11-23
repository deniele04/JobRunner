import collections
import os
import re
import signal
import subprocess
import time
from pathlib import Path

from . import __version__, bitacora
from .jobs import (
    Job, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED, FINAL_STATES, now_iso,
)

VALID_STATES = {QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED}

DEFAULT_MAX_JOBS = 3      # trabajos corriendo a la vez (ADR-0004)
DEFAULT_QUEUE_SIZE = 10   # trabajos esperando en la cola (ADR-0004)
ESPERA_SIGKILL = 5.0      # segundos entre SIGTERM y SIGKILL al cancelar (ADR-0006)
MAX_SALIDA = 64 * 1024    # bytes maximos que devuelve output (el final de la salida)
STREAMS = {"stdout": "stdout_path", "stderr": "stderr_path"}


class ColaLlena(Exception):
    """No hay lugar para correr ni para esperar: la solicitud se rechaza."""


class RequestIdEnUso(Exception):
    """El request_id ya pertenece a un trabajo con otro comando (ADR-0007)."""


_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


def validar_request_id(request_id):
    """request_id: texto de 1 a 64 caracteres (letras, numeros, - y _), ADR-0007."""
    if not (isinstance(request_id, str) and _REQUEST_ID.fullmatch(request_id)):
        raise ValueError(
            "request_id debe ser texto de 1 a 64 caracteres (letras, numeros, - y _)"
        )


class Cerrando(Exception):
    """El servicio esta en cierre controlado y no acepta trabajos nuevos (RF-15)."""


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
        self._cancelando = {}              # id -> instante (monotonic) del SIGKILL
        self._cerrando = False             # True durante el cierre controlado (ADR-0006)
        self._store = store
        self._inicio = time.monotonic()    # para el tiempo activo de health

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
        if self._cerrando:
            raise Cerrando("el servicio se esta cerrando; no acepta trabajos nuevos")
        if not isinstance(argv, (list, tuple)) or not argv:
            raise ValueError("argv debe ser una lista no vacia de strings, p. ej. ['sleep', '5']")
        if not all(isinstance(a, str) and a for a in argv):
            raise ValueError("argv debe contener solo strings no vacios")

        if request_id is not None:
            validar_request_id(request_id)
            for existente in self._jobs.values():
                if existente.request_id == request_id:
                    if list(existente.argv) != list(argv):
                        bitacora.error("request_id_en_uso", existente.id, request_id=request_id)
                        raise RequestIdEnUso(
                            "el request_id ya se uso para otro comando (trabajo " + existente.id + ")"
                        )
                    bitacora.evento("duplicado", existente.id, request_id=request_id)
                    respuesta = existente.to_dict()
                    respuesta["duplicado"] = True
                    return respuesta

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
        if self._cerrando:   # en el cierre la cola se conserva para el siguiente arranque
            return
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

    def output(self, job_id, stream="stdout", max_bytes=MAX_SALIDA):
        """Final de la salida de un trabajo: {id, stream, data, truncated}.

        stream es "stdout" o "stderr". Se devuelven como mucho max_bytes bytes (por defecto y
        como maximo 64 KiB) tomados del FINAL del archivo; truncated indica que habia mas al
        principio. data es texto UTF-8; los bytes que no lo sean se sustituyen. Un trabajo en
        cola todavia no tiene archivos: devuelve data vacio. Solo lee: no cambia ningun estado.
        """
        if stream not in STREAMS:
            raise ValueError("stream debe ser stdout o stderr")
        if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_SALIDA:
            raise ValueError("max_bytes debe ser un entero de 1 a " + str(MAX_SALIDA))
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError("No existe el trabajo " + str(job_id))
        ruta = getattr(job, STREAMS[stream])
        datos, truncado = b"", False
        try:
            with open(ruta, "rb") as archivo:
                archivo.seek(0, os.SEEK_END)
                tamano = archivo.tell()
                inicio = max(0, tamano - max_bytes)
                archivo.seek(inicio)
                datos = archivo.read(tamano - inicio)
                truncado = inicio > 0
        except (FileNotFoundError, TypeError):   # TypeError: ruta None
            if job.state != QUEUED:
                raise ValueError("la salida del trabajo " + str(job_id) + " no esta disponible: "
                                 "no existe su archivo " + str(ruta))
        except OSError as e:
            raise ValueError("no se pudo leer la salida del trabajo " + str(job_id) + ": "
                             + (e.strerror or str(e)))
        if truncado:   # el corte puede caer a la mitad de un caracter UTF-8: se descarta ese pedazo
            while datos and 0x80 <= datos[0] < 0xC0:
                datos = datos[1:]
        return {"id": job_id, "stream": stream,
                "data": datos.decode("utf-8", errors="replace"), "truncated": truncado}

    def health(self):
        """Resumen de salud del servicio (RF-24), sin los datos de red (los agrega el servidor).

        version del software, tiempo activo, trabajos por estado, en ejecucion contra
        max_jobs, en cola contra queue_size y estado de la base de datos.
        """
        por_estado = {estado: 0 for estado in (QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED)}
        for job in self._jobs.values():
            por_estado[job.state] += 1
        if self._store is None:
            base = "no configurada"
        else:
            try:
                self._store.verificar()
                base = "ok"
            except Exception as e:   # sqlite3.Error, base cerrada, etc.
                base = "error: " + str(e)
        return {
            "version": __version__,
            "uptime_seconds": round(time.monotonic() - self._inicio, 1),
            "jobs_by_state": por_estado,
            "running": por_estado[RUNNING],
            "max_jobs": self.max_jobs,
            "queued": por_estado[QUEUED],
            "queue_size": self.queue_size,
            "database": base,
        }

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
                if job_id in self._cancelando:
                    job.transition(CANCELED)
                    bitacora.evento("cancelado", job_id, codigo=code)
                else:
                    job.transition(SUCCEEDED if code == 0 else FAILED)
                    bitacora.evento("terminado", job_id, estado=job.state, codigo=code)
            self._cancelando.pop(job_id, None)
            self._guardar(job)

    def tick(self):
        """Ciclo del servidor, cada 0.5 s (ADR-0004). Nunca bloquea.

        1. poll(): recoge los procesos que terminaron.
        2. escalamiento: SIGKILL a los cancelados que siguen vivos tras 5 s.
        3. arranca trabajos de la cola mientras haya lugar.
        """
        self.poll()
        self._escalar()
        self._arrancar_de_la_cola()

    def _escalar(self):
        """SIGKILL al grupo de los trabajos cancelados que ignoraron SIGTERM (ADR-0006)."""
        ahora = time.monotonic()
        for job_id, limite in list(self._cancelando.items()):
            if ahora < limite:
                continue
            proc = self._procs.get(job_id)
            if proc is None or proc.poll() is not None:
                continue
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self._cancelando[job_id] = float("inf")   # se envia una sola vez
            bitacora.evento("escalamiento", job_id, senal="SIGKILL")

    def cerrar(self, forzar=None):
        """Cierre controlado (ADR-0006, RF-15, RNF-25, RNF-30).

        Deja de arrancar trabajos, cancela los RUNNING con el mismo mecanismo que
        cancel() (SIGTERM al grupo y, a los 5 s, SIGKILL) y espera a recogerlos, de
        modo que no quede ningun hijo vivo. Los QUEUED no se tocan: ya estan guardados
        y ADR-0005 los reanuda en el siguiente arranque.

        forzar: funcion sin argumentos; si devuelve True (segundo Ctrl+C) se envia
        SIGKILL de inmediato a lo que siga vivo.
        Devuelve {"cancelados": n, "en_cola": m}.
        """
        self._cerrando = True
        self.poll()
        en_cola = len([i for i in self._cola if self._jobs[i].state == QUEUED])
        cancelados = 0
        for job_id in list(self._procs):
            try:
                self.cancel(job_id)
                cancelados += 1
            except (KeyError, ValueError):
                pass   # ya habia terminado por su cuenta

        limite = time.monotonic() + ESPERA_SIGKILL + 5.0   # SIGKILL a los 5 s + margen para recogerlos
        while self._procs:
            if forzar is not None and forzar():
                for job_id in self._cancelando:
                    self._cancelando[job_id] = 0.0
            self._escalar()
            self.poll()
            if not self._procs:
                break
            if time.monotonic() >= limite:
                bitacora.error("cierre_incompleto", motivo="procesos que no terminaron",
                               pendientes=len(self._procs))
                break
            time.sleep(0.05)
        return {"cancelados": cancelados, "en_cola": en_cola}

    def cancel(self, job_id):
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError("No existe el trabajo " + str(job_id))
        # Segunda cancelacion (ADR-0006, regla 5): si el trabajo ya se esta
        # cancelando o ya quedo CANCELED, se devuelve su estado real sin
        # modificarlo ni reenviar senales. Se decide ANTES de recoger procesos para
        # que la respuesta no dependa de si el proceso ya murio o no.
        if job_id in self._cancelando or job.state == CANCELED:
            return job.to_dict()

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

        # RUNNING: SIGTERM al grupo y se responde de inmediato (ADR-0006). El
        # trabajo sigue en RUNNING hasta que poll() recoja su proceso; entonces
        # pasa a CANCELED.
        proc = self._procs[job_id]
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        self._cancelando[job_id] = time.monotonic() + ESPERA_SIGKILL
        bitacora.evento("cancelacion_solicitada", job_id)
        return job.to_dict()
