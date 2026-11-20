import argparse
import json
import os
import signal
import socket
import threading
from pathlib import Path

from . import bitacora, red
from .executor import DEFAULT_MAX_JOBS, DEFAULT_QUEUE_SIZE, Cerrando, ColaLlena, JobManager
from .store import Store

DEFAULT_SOCKET_PATH = os.environ.get("JOBRUNNER_SOCKET", "data/jobrunner.sock")
INTERVALO_TICK = 0.5   # segundos entre revisiones de procesos


class _Cierre:
    """Estado del cierre controlado (ADR-0006): lo escriben los manejadores de senal."""

    def __init__(self):
        self.pedido = False   # primer Ctrl+C o SIGTERM: cerrar de forma ordenada
        self.forzar = False   # segundo aviso: SIGKILL inmediato a lo que siga vivo


def _instalar_senales(cierre):
    """SIGINT y SIGTERM solo piden el cierre; el ciclo principal lo ejecuta.

    Devuelve una funcion que restaura los manejadores anteriores. Fuera del hilo
    principal no se instalan (signal solo funciona ahi).
    """
    if threading.current_thread() is not threading.main_thread():
        return lambda: None

    def manejador(signum, frame):
        if cierre.pedido:
            cierre.forzar = True
        else:
            cierre.pedido = True

    anteriores = {s: signal.signal(s, manejador) for s in (signal.SIGINT, signal.SIGTERM)}

    def restaurar():
        for s, anterior in anteriores.items():
            signal.signal(s, anterior)
    return restaurar


def handle_request(manager, request):
    cmd = request.get("cmd")

    if cmd == "submit":
        argv = request.get("argv")
        if not isinstance(argv, (list, tuple)) or not argv:
            return {"error": "argv debe ser una lista no vacia de strings"}
        if not all(isinstance(a, str) and a for a in argv):
            return {"error": "argv debe contener solo strings no vacios"}
        request_id = request.get("request_id")
        if request_id is not None and not (isinstance(request_id, str) and request_id):
            return {"error": "request_id debe ser un string no vacio"}
        try:
            return manager.submit(list(argv), request_id=request_id)
        except ColaLlena:
            return {"error": "cola llena (capacidad " + str(manager.queue_size) + "); intenta más tarde"}
        except Cerrando as e:
            return {"error": str(e)}

    if cmd == "status":
        job_id = request.get("id")
        if not job_id:
            return {"error": "falta id"}
        manager.tick()
        job = manager.get(job_id)
        if job is None:
            return {"error": "no existe el trabajo " + str(job_id)}
        return job

    if cmd == "list":
        state = request.get("state")
        manager.tick()
        return {"jobs": manager.list(state=state)}

    if cmd == "cancel":
        job_id = request.get("id")
        if not job_id:
            return {"error": "falta id"}
        try:
            return manager.cancel(job_id)
        except KeyError as e:
            return {"error": str(e)}
        except ValueError as e:
            return {"error": str(e)}

    return {"error": "comando desconocido: " + str(cmd)}


def responder(manager, linea):
    """Procesa una solicitud completa (una linea de bytes) y devuelve el dict de respuesta."""
    try:
        request = json.loads(linea.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        bitacora.error("solicitud_invalida", motivo="JSON invalido")
        return {"error": "JSON invalido"}
    try:
        return handle_request(manager, request)
    except Exception as e:
        bitacora.error("error_interno", motivo=e)
        return {"error": "error interno: " + str(e)}


def serve(socket_path=DEFAULT_SOCKET_PATH, max_jobs=DEFAULT_MAX_JOBS, queue_size=DEFAULT_QUEUE_SIZE,
          listen=None, allow=None):
    try:
        permitidas = red.redes_permitidas(allow)
    except ValueError as e:
        raise SystemExit("Error: " + str(e))
    socket_path = Path(socket_path)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()

    store = Store(str(socket_path.parent / "jobrunner.db"))
    manager = JobManager(data_dir=str(socket_path.parent), store=store,
                         max_jobs=max_jobs, queue_size=queue_size)
    bitacora.configurar(socket_path.parent)
    manager.recuperar()

    servidor_red = red.Red(lambda linea: responder(manager, linea), permitidas=permitidas)
    detalles = {"socket": socket_path}
    try:
        unix = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        unix.bind(str(socket_path))
        unix.listen(128)
        servidor_red.escuchar(unix)
        if listen is not None:
            host, puerto = red.parsear_direccion(listen)
            red.validar_escucha(host)
            tcp = red.abrir_tcp(host, puerto)
            servidor_red.escuchar(tcp)
            direccion = tcp.getsockname()
            detalles["tcp"] = ("[" + direccion[0] + "]" if ":" in direccion[0] else direccion[0]) \
                + ":" + str(direccion[1])
            detalles["permitidas"] = ",".join(str(r) for r in permitidas)
    except (OSError, ValueError) as e:
        servidor_red.cerrar()
        store.close()
        bitacora.cerrar()
        if socket_path.exists():
            socket_path.unlink()
        raise SystemExit("Error: no se pudo abrir el servicio: " + str(e))
    print("JobRunner escuchando en " + str(socket_path))
    if "tcp" in detalles:
        print("JobRunner escuchando en " + detalles["tcp"] + " (TCP); origenes permitidos: "
              + detalles["permitidas"])
    bitacora.evento("servicio_iniciado", **detalles)

    cierre = _Cierre()
    restaurar_senales = _instalar_senales(cierre)

    try:
        while not cierre.pedido:
            manager.tick()   # recoge terminados, arranca la cola, aplica escalamiento
            servidor_red.atender(INTERVALO_TICK)   # espera hasta 0.5 s (ADR-0004, ADR-0009)
    except KeyboardInterrupt:   # solo si no se pudieron instalar los manejadores
        cierre.pedido = True
    finally:
        # Cierre controlado (ADR-0006): 1) dejar de aceptar solicitudes, 2) cancelar los
        # RUNNING, 3) conservar los QUEUED, 4) registrar y eliminar el socket. Corre tambien
        # si el ciclo termina por un error, para no dejar hijos huerfanos.
        print("\nDeteniendo JobRunner...")
        servidor_red.cerrar()
        try:
            resumen = manager.cerrar(forzar=lambda: cierre.forzar)
            bitacora.evento("servicio_detenido", cancelados=resumen["cancelados"],
                            en_cola=resumen["en_cola"])
        finally:
            store.close()
            bitacora.cerrar()
            if socket_path.exists():
                socket_path.unlink()
            restaurar_senales()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="jobrunner.server",
        description="Servicio JobRunner: ejecuta trabajos con cola y limite de concurrencia.",
    )
    parser.add_argument(
        "socket", nargs="?", default=DEFAULT_SOCKET_PATH,
        help="Ruta del socket Unix (default: " + DEFAULT_SOCKET_PATH + ")",
    )
    parser.add_argument(
        "--max-jobs", type=int, default=DEFAULT_MAX_JOBS,
        help="Trabajos simultaneos (default: %(default)s)",
    )
    parser.add_argument(
        "--queue-size", type=int, default=DEFAULT_QUEUE_SIZE,
        help="Trabajos que pueden esperar en la cola (default: %(default)s)",
    )
    parser.add_argument(
        "--listen", nargs="?", const="127.0.0.1:7070", default=None, metavar="HOST:PUERTO",
        help="Ademas del socket Unix, escucha por TCP en HOST:PUERTO "
             "(sin valor: 127.0.0.1:7070). Sin esta opcion no se abre ningun puerto.",
    )
    parser.add_argument(
        "--allow", action="append", default=[], metavar="RED",
        help="Red de origen permitida por TCP, en CIDR (p. ej. 100.64.0.0/10 para Tailscale). "
             "Se puede repetir. Siempre se permite 127.0.0.1 y ::1. Solo se aceptan redes "
             "privadas; 0.0.0.0, :: y las publicas impiden el arranque.",
    )
    args = parser.parse_args(argv)
    try:
        if args.listen is not None:
            red.validar_escucha(red.parsear_direccion(args.listen)[0])
        red.redes_permitidas(args.allow)
    except ValueError as e:
        parser.error(str(e))
    if args.allow and args.listen is None:
        parser.error("--allow solo tiene efecto con --listen")
    if args.max_jobs < 1:
        parser.error("--max-jobs debe ser al menos 1")
    if args.queue_size < 0:
        parser.error("--queue-size no puede ser negativo")
    return args


if __name__ == "__main__":
    args = parse_args()
    serve(args.socket, max_jobs=args.max_jobs, queue_size=args.queue_size, listen=args.listen,
          allow=args.allow)
