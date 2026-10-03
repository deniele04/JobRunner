import argparse
import json
import os
import socket
import sys

DEFAULT_SOCKET_PATH = os.environ.get("JOBRUNNER_SOCKET", "data/jobrunner.sock")


def send_request(request, socket_path=DEFAULT_SOCKET_PATH):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(socket_path)
    except (FileNotFoundError, ConnectionRefusedError):
        print("Error: no se pudo conectar al servidor en " + socket_path + ". Esta corriendo ./scripts/run.sh?", file=sys.stderr)
        sys.exit(1)

    with client:
        client.sendall((json.dumps(request) + "\n").encode("utf-8"))
        data = b""
        while not data.endswith(b"\n"):
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
    return json.loads(data.decode("utf-8"))


def print_response(response):
    print(json.dumps(response, indent=2))
    if isinstance(response, dict) and "error" in response:
        sys.exit(1)


def cmd_submit(args):
    response = send_request({"cmd": "submit", "argv": args.argv}, args.socket)
    print_response(response)


def cmd_status(args):
    response = send_request({"cmd": "status", "id": args.id}, args.socket)
    print_response(response)


def cmd_list(args):
    response = send_request({"cmd": "list", "state": args.state}, args.socket)
    print_response(response)


def cmd_cancel(args):
    response = send_request({"cmd": "cancel", "id": args.id}, args.socket)
    print_response(response)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="jobrunner",
        description="Cliente de linea de comandos para JobRunner.",
    )
    parser.add_argument(
        "--socket", default=DEFAULT_SOCKET_PATH,
        help="Ruta del socket Unix del servidor (default: " + DEFAULT_SOCKET_PATH + ")",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_submit = sub.add_parser("submit", help="Encola un nuevo trabajo")
    p_submit.add_argument("argv", nargs="+", help="Comando a ejecutar, p. ej. sleep 5")
    p_submit.set_defaults(func=cmd_submit)

    p_status = sub.add_parser("status", help="Consulta el estado de un trabajo")
    p_status.add_argument("id", help="Identificador del trabajo")
    p_status.set_defaults(func=cmd_status)

    p_list = sub.add_parser("list", help="Lista los trabajos")
    p_list.add_argument("--state", default=None, help="Filtra por estado (QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED)")
    p_list.set_defaults(func=cmd_list)

    p_cancel = sub.add_parser("cancel", help="Cancela un trabajo")
    p_cancel.add_argument("id", help="Identificador del trabajo")
    p_cancel.set_defaults(func=cmd_cancel)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()