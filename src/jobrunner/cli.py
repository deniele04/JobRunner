import argparse
import json
import os
import socket
import sys

VERSION_PROTOCOLO = 1   # protocolo v1 (ADR-0009)
DEFAULT_SOCKET_PATH = os.environ.get("JOBRUNNER_SOCKET", "data/jobrunner.sock")
DEFAULT_PUERTO = 7070   # el mismo que usa `--listen` del servidor sin valor
TIMEOUT_CONEXION = 5.0  # segundos para abrir la conexion TCP

# Que hacer ante cada error del servicio (RNF-21: operacion, causa y accion). Se busca el
# primer fragmento que aparezca en el texto del error, sin distinguir mayusculas.
ACCIONES = (
    ("no existe el trabajo", "copia el id completo que devolvio 'royito submit' o 'royito list'"),
    ("cola llena", "espera a que termine algun trabajo o reinicia el servicio con un --queue-size mayor"),
    ("ya termino en estado", "no hay nada que hacer: un trabajo terminado no se puede cancelar"),
    ("estado desconocido", "usa QUEUED, RUNNING, SUCCEEDED, FAILED o CANCELED"),
    ("la salida del trabajo", "el archivo de salida ya no existe; revisa la carpeta data/ del servicio"),
    ("max_bytes", "usa un entero de 1 a 65536"),
    ("se esta cerrando", "espera a que el servicio vuelva a iniciar y repite la operacion"),
    ("request_id", "usa de 1 a 64 caracteres: letras, numeros, - y _"),
    ("argv", "escribe el comando despues de -- , por ejemplo: royito submit -- sleep 5"),
    ("version de protocolo", "usa un cliente de la misma version que el servicio"),
    ("mensaje demasiado grande", "reduce el tamano de la solicitud (maximo 64 KiB)"),
    ("error interno", "revisa data/jobrunner.log en el equipo del servicio y avisa a quien lo opera"),
)
OPERACIONES = {
    "submit": "enviar el trabajo",
    "status": "consultar el trabajo",
    "list": "listar los trabajos",
    "cancel": "cancelar el trabajo",
    "output": "leer la salida del trabajo",
    "health": "consultar la salud del servicio",
}


def _destino(host, puerto):
    return ("[" + host + "]" if ":" in host else host) + ":" + str(puerto)


def _fallar(mensaje):
    print(mensaje, file=sys.stderr)
    sys.exit(1)


def _conectar(socket_path, host, puerto):
    """Abre la conexion con el servicio: TCP si hay host, socket Unix si no."""
    if host is None:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client.connect(socket_path)
        except OSError as e:
            client.close()
            causa = "" if isinstance(e, (FileNotFoundError, ConnectionRefusedError)) \
                else " (" + (e.strerror or str(e)) + ")"
            _fallar("Error: no se pudo conectar al servidor en " + socket_path + causa
                    + ". Esta corriendo ./scripts/run.sh?")
        return client
    try:
        client = socket.create_connection((host, puerto), timeout=TIMEOUT_CONEXION)
    except OSError as e:
        causa = e.strerror or str(e)
        _fallar("Error: no se pudo conectar a " + _destino(host, puerto) + " (" + causa + "). "
                "Verifica que el servicio este corriendo con --listen, que el host y el puerto "
                "sean correctos y que tu IP este en --allow.")
    client.settimeout(None)
    return client


def send_request(request, socket_path=DEFAULT_SOCKET_PATH, host=None, puerto=None):
    puerto = DEFAULT_PUERTO if puerto is None else puerto
    donde = "el servidor" if host is None else "el servidor en " + _destino(host, puerto)
    client = _conectar(socket_path, host, puerto)
    data = b""
    with client:
        try:
            client.sendall((json.dumps({"v": VERSION_PROTOCOLO, **request}) + "\n").encode("utf-8"))
            while not data.endswith(b"\n"):
                chunk = client.recv(4096)
                if not chunk:
                    break
                data += chunk
        except OSError:
            data = b""   # el servidor cerro de golpe: se trata igual que un cierre sin respuesta
    if not data.strip():
        pista = ("Si el servicio esta en otro equipo, revisa que tu IP este en --allow."
                 if host is not None else "Revisa data/jobrunner.log.")
        _fallar("Error: " + donde + " cerro la conexion sin responder. " + pista)
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fallar("Error: " + donde + " envio una respuesta que no es JSON valido. "
                "Verifica que sea un servicio JobRunner.")


def es_error_del_servicio(response):
    """Error del servicio: trae "error" y no es un trabajo (trae "id") ni un listado (trae "jobs").

    Un trabajo fallido tambien trae la clave "error" (con la senal o el motivo), pero es una
    operacion exitosa; por eso se descartan las respuestas con "id" o "jobs" (ADR-0009).
    """
    return (isinstance(response, dict) and "error" in response
            and "id" not in response and "jobs" not in response)


def mensaje_de_error(comando, response):
    """Texto para stderr: operacion, causa y que hacer (RNF-21)."""
    causa = str(response.get("error")).strip().rstrip(".")
    operacion = OPERACIONES.get(comando, "completar la operacion")
    texto = "Error al " + operacion + ": " + causa + "."
    minusculas = causa.lower()
    for fragmento, accion in ACCIONES:
        if fragmento in minusculas:
            return texto + " Que hacer: " + accion + "."
    return texto


def print_response(response, comando=None):
    version = response.get("v") if isinstance(response, dict) else None
    if version is not None and version != VERSION_PROTOCOLO:
        print("Error: el servidor usa el protocolo v" + str(version) +
              " y este cliente usa v" + str(VERSION_PROTOCOLO), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(response, indent=2))
    if es_error_del_servicio(response):
        print(mensaje_de_error(comando, response), file=sys.stderr)
        sys.exit(1)


def _enviar(args, request):
    return send_request(request, args.socket, args.host, args.port)


def cmd_submit(args):
    request = {"cmd": "submit", "argv": args.argv}
    if args.request_id:
        request["request_id"] = args.request_id
    print_response(_enviar(args, request), "submit")


def cmd_status(args):
    print_response(_enviar(args, {"cmd": "status", "id": args.id}), "status")


def cmd_list(args):
    print_response(_enviar(args, {"cmd": "list", "state": args.state}), "list")


def cmd_cancel(args):
    print_response(_enviar(args, {"cmd": "cancel", "id": args.id}), "cancel")


def cmd_output(args):
    request = {"cmd": "output", "id": args.id, "stream": "stderr" if args.stderr else "stdout"}
    if args.max_bytes is not None:
        request["max_bytes"] = args.max_bytes
    response = _enviar(args, request)
    if args.raw and isinstance(response, dict) and "data" in response \
            and not es_error_del_servicio(response):
        sys.stdout.write(response["data"])
        if response.get("truncated"):
            print("\nAviso: la salida es mas larga; solo se muestra el final.", file=sys.stderr)
        return
    print_response(response, "output")


def cmd_health(args):
    print_response(_enviar(args, {"cmd": "health"}), "health")


def _puerto(texto):
    try:
        numero = int(texto)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("puerto invalido: " + str(texto) + " (usa un numero de 1 a 65535)")
    if not 1 <= numero <= 65535:
        raise argparse.ArgumentTypeError("puerto fuera de rango: " + str(numero) + " (usa de 1 a 65535)")
    return numero


def build_parser():
    parser = argparse.ArgumentParser(
        prog="royito",
        description="royito: cliente de linea de comandos para JobRunner. Sin --host usa el socket "
                    "Unix local; con --host se conecta por TCP a un servicio remoto "
                    "(que debe haberse iniciado con --listen).",
        epilog="Codigos de salida: 0 operacion exitosa; 1 error (el servicio rechazo la operacion o "
               "no se pudo conectar); 2 uso incorrecto del comando. Un trabajo FAILED es una "
               "operacion exitosa (codigo 0).",
    )
    parser.add_argument(
        "--socket", default=DEFAULT_SOCKET_PATH,
        help="Ruta del socket Unix del servidor (default: " + DEFAULT_SOCKET_PATH + "). "
             "Se ignora si se indica --host",
    )
    parser.add_argument(
        "--host", default=os.environ.get("JOBRUNNER_HOST") or None, metavar="HOST",
        help="Direccion o nombre del servicio remoto (variable JOBRUNNER_HOST). "
             "Sin host se usa el socket Unix",
    )
    parser.add_argument(
        "--port", type=_puerto, default=None, metavar="PUERTO",
        help="Puerto TCP del servicio remoto (variable JOBRUNNER_PORT; default: "
             + str(DEFAULT_PUERTO) + "). Requiere --host",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_submit = sub.add_parser("submit", help="Encola un nuevo trabajo")
    p_submit.add_argument("argv", nargs="+", help="Comando a ejecutar, p. ej. sleep 5")
    p_submit.add_argument("--request-id", default=None, help="Identificador opcional: si se repite, se devuelve el mismo trabajo")
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

    p_output = sub.add_parser(
        "output", help="Muestra la salida de un trabajo (el final, hasta 64 KiB)",
        description="Muestra el final de la salida normal (o de errores, con --stderr) de un trabajo. "
                    "Responde un JSON con id, stream, data y truncated; truncated es true si habia "
                    "mas salida al principio.",
    )
    p_output.add_argument("id", help="Identificador del trabajo")
    p_output.add_argument("--stderr", action="store_true",
                          help="Muestra la salida de errores en lugar de la salida normal")
    p_output.add_argument("--max-bytes", type=int, default=None, metavar="N",
                          help="Cuantos bytes del final mostrar, de 1 a 65536 (default: 65536)")
    p_output.add_argument("--raw", action="store_true",
                          help="Imprime solo el texto de la salida, sin el JSON")
    p_output.set_defaults(func=cmd_output)

    p_health = sub.add_parser(
        "health", help="Resumen de salud del servicio",
        description="Resumen de salud del servicio: version, tiempo activo, los trabajos por estado, los trabajos en "
                    "ejecucion y en cola frente a sus limites (--max-jobs y --queue-size), el estado "
                    "de la base de datos, los clientes conectados y los accesos rechazados.",
    )
    p_health.set_defaults(func=cmd_health)

    return parser


def resolver_destino(parser, args):
    """Decide el transporte: TCP si hay host (opcion o JOBRUNNER_HOST), socket Unix si no.

    Deja en args.host y args.port el destino final (args.host es None para el socket Unix).
    """
    if args.host is None:
        if args.port is not None:
            parser.error("--port requiere --host (o la variable JOBRUNNER_HOST)")
        return
    if args.port is None:
        desde_entorno = os.environ.get("JOBRUNNER_PORT")
        if desde_entorno:
            try:
                args.port = _puerto(desde_entorno)
            except argparse.ArgumentTypeError as e:
                parser.error("JOBRUNNER_PORT: " + str(e))
        else:
            args.port = DEFAULT_PUERTO


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    resolver_destino(parser, args)
    args.func(args)


if __name__ == "__main__":
    main()
