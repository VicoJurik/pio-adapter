import datetime
import sys

from flask import Flask

from vpokerlib.pio_adapter import PioAdapter
from vpokerlib.mypath import fix_wsl_path


EXIT_FAILURE = 1


def runtime_error(message, exit=EXIT_FAILURE):
    print("error: {}".format(message), file=sys.stderr)
    exit(EXIT_FAILURE)


pio = PioAdapter()
if not pio.start():
    runtime_error("cannot start pio adapter")


_BLACKLISTED_COMMANDS = [
    "exit", "get_key", "get_solver_started", "start", "stdoutredi", "stdoutredi_append",
    "add_listener", "remove_listener",
]


def get_time():
    return datetime.datetime.now().timestamp()


def set_command_data(data, command=None, args=None, duration=None):
    data["time"] = datetime.datetime.now().isoformat()
    if command:
        data["command"] = {"command": command}
    if args:
        data.setdefault("command", {})["args"] = args
    if duration:
        data["command_time"] = int(1000 * duration)
    return data


def error(message, command=None, args=None):
    data = {"ok": False, "error": message}
    set_command_data(data, command, args)
    return data


def ok(result, command=None, args=None, duration=None):
    data = {"ok": True, "result": result}
    set_command_data(data, command, args, duration)
    return data


app = Flask(__name__)


def _parse_go(args):
    seconds = None
    steps = None
    if args:
        arg = args[0]
        if arg.endswith("seconds"):
            seconds = int(args.split(" ")[0])
        else:
            steps = int(args.split(" ")[0])
    return [seconds, steps]

def _make_path(args): return [fix_wsl_path("/" + "/".join(args))]

def _singleton(args): return [args]


_PREPROCESSORS = {
    "add_line": _singleton,
    "add_preflop_line": _singleton,
    "combo_lock_node": lambda args: [args[0], args[1:]],
    "force_line": _singleton,
    "go": _parse_go,
    "ignore_mem_check": lambda args: [True if not args else args[0] == "on"],
    "load_script": _make_path,
    "load_script_silent": _make_path,
    "load_tree": _make_path,
    "remove_line": _singleton,
    "remove_preflop_line": _singleton,
    "set_accuracy": lambda args: [args[0], len(args) <= 1 or args[1] != "fraction"],
    "set_adjust_strat": lambda args: [args[0], args[1], args[2] != "false"],
    "set_board": _singleton,
    "set_isomorphism": lambda args: [arg != "false" for arg in args],
    "set_range": lambda args: [args[0], args[1:]],
    "set_strategy": lambda args: [args[0], args[1], args[2:]],
    "show_all_freqs": lambda args: [not args or args[1] != "local"],
    "show_categories": _singleton,
    "small_strats": lambda args: [args[0] != "off"],
}


@app.route("/<path:path>")
def index(path):
    args = path.split("/")
    command = args[0]
    args = args[1:]
    try:
        if command.startswith("_") or command in _BLACKLISTED_COMMANDS:
            raise AttributeError()
        method = getattr(pio, command)
    except AttributeError:
        return error("\"{}\": unknown command".format(command), command, args)
    start_time = get_time()
    preprocessor = _PREPROCESSORS.get(command)
    if preprocessor is not None:
        args = preprocessor(args)
    result = method(*args)
    return ok(result, command, args, get_time() - start_time)


if __name__ == "__main__":
    app.run(debug=True)
