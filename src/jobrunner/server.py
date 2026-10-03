import json
import os
import socket
import sys
from pathlib import Path

from .executor import JobManager

DEFAULT_SOCKET_PATH = os.environ.get("JOBRUNNER_SOCKET", "data/jobrunner.sock")


def handle_request(manager, request):
    cmd = request.get("cmd")

    if cmd == "submit":
        argv = request.get("argv")
        if not isinstance(argv, (list, tuple)) or not argv:
            return {"error": "argv debe ser una lista no vacia de strings"}
        if not all(isinstance(a, str) and a for a in argv):
            return {"error": "argv debe contener solo strings no vacios"}
        return manager.submit(list(argv))

    if cmd == "status":
        job_id = request.get("id")
        if not job_id:
            return {"error": "falta id"}
        manager.poll()
        job = manager.get(job_id)
        if job is None:
            return {"error": "no existe el trabajo " + str(job_id)}
        return job

    if cmd == "list":
        state = request.get("state")
        manager.poll()
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


def serve(socket_path=DEFAULT_SOCKET_PATH):
    socket_path = Path(socket_path)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()

    manager = JobManager(data_dir=str(socket_path.parent))

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(socket_path))
    server.listen(5)
    print("JobRunner escuchando en " + str(socket_path))

    try:
        while True:
            conn, _ = server.accept()
            with conn:
                data = b""
                while not data.endswith(b"\n"):
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                if not data.strip():
                    continue
                try:
                    request = json.loads(data.decode("utf-8"))
                except json.JSONDecodeError:
                    response = {"error": "JSON invalido"}
                else:
                    try:
                        response = handle_request(manager, request)
                    except Exception as e:
                        response = {"error": "error interno: " + str(e)}
                conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
    except KeyboardInterrupt:
        print("\nDeteniendo JobRunner...")
    finally:
        server.close()
        if socket_path.exists():
            socket_path.unlink()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOCKET_PATH
    serve(path)