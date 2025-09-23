import datetime
import os
import queue
import subprocess
import sys
import threading
import time

from .config import config


def _fix_path(path):
    if not config.get("wsl", False):
        return path
    path = path.replace("C:\\", "/mnt/c/")
    path = path.replace("\\", "/")
    return path


_SOLVER_DATA_MAP = {
    "EV IP": "ev_ip",
    "EV OOP": "ev_oop",
    "Exploitable for": "exploitable",
    "IP's MES": "mes_ip",
    "OOP's MES": "mes_oop",
    "running time": "running_time"
}

_POLL_WAIT_TIME = 0.1


_PIO_PATH = _fix_path(config["path"])
_DEBUG_OUT = config.get("debug", False)
_ENCODING = config.get("encoding", "utf-8")

_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "pio.logs")
if not os.path.exists(os.path.dirname(_LOG_PATH)):
    os.makedirs(os.path.dirname(_LOG_PATH))


_log_file = sys.stdout if _DEBUG_OUT else open(_LOG_PATH, "w")


def _now_iso():
    return datetime.datetime.now().isoformat()


class PioInstance:
    def __init__(self, key, version=config["version"]):
        self._end_string = config["end_string"]
        self._key = key
        self._process = subprocess.Popen(
            [_PIO_PATH],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            cwd=os.path.dirname(_PIO_PATH),
        )
        self._reader_thread = threading.Thread(target=self._read)
        self._version = version
        self._is_alive = False
        self._outputs = queue.Queue()
        self._solver_data = {}
        self._listeners = []
        self._solver_result_mode = False

    def add_listener(self, listener):
        self._listeners.append(listener)

    def end_string(self):
        return self._end_string

    def flush(self):
        self._process.stdin.flush()

    def key(self):
        return self._key

    def is_alive(self):
        return self._is_alive

    def remove_listener(self, listener):
        self._listeners.remove(listener)

    def start(self):
        self._is_alive = True
        self._reader_thread.start()

    def stop(self, wait=True):
        self.write("exit")
        if wait:
            self._reader_thread.join()

    def write(self, lines, flush=True):
        for line in lines.split("\n"):
            if not line:
                continue
            self._process.stdin.write((line + "\n").encode(_ENCODING))
            _log_file.write("{} [{}] >>> {}\n".format(_now_iso(), self._key, line))
            _log_file.flush()
        if flush:
            self.flush()

    def poll(self, recursive_wait=False, wait=None):
        if self._outputs.empty():
            if wait is not None:
                time.sleep(wait)
                return self.poll(recursive_wait=recursive_wait, wait=(wait if recursive_wait else None))
            return None
        return self._outputs.get()

    def readline(self, wait_time=0):
        if self._version == 2:
            lines = self.readmultilines(wait_time=wait_time)
            assert len(lines) == 1, lines
            return lines[0]
        return self._readline(wait_time=wait_time)

    def readmultilines(self, wait_time=0):
        lines = []
        while True:
            line = self._readline()
            if line == self._end_string:
                return lines
            lines.append(line)

    def set_end_string(self, end_string):
        self._end_string = end_string

    def version(self):
        return self._version

    def _handle_input(self, content):
        if content == "SOLVER: started":
            self._solver_started = True
            self._solver_stopped = False
            self._notice_listeners("solve_begin")
        elif content.startswith("SOLVER: stopped"):
            self._solver_stopped = True
            self._solver_started = False
            self._notice_listeners("solve_end")
        elif content == "SOLVER:":
            self._solver_result_mode = True
            self._solver_data = {}
        elif self._solver_result_mode:
            if content == self._end_string:
                self._solver_result_mode = False
                self._notice_listeners("solve_iteration", self._solver_data)
            else:
                key, result = content.split(":")
                self._solver_data[_SOLVER_DATA_MAP[key]] = float(result.strip())
        else:
            if content.startswith("ERROR: "):
                self._notice_listeners("error", content[len("ERROR: "):])
            self._outputs.put(content)

    def _notice_listeners(self, event, args=None):
        for listener in self._listeners:
            method = getattr(listener, "on_{}".format(event))
            if args is None:
                method()
            else:
                method(args)

    def _read(self):
        for line in self._process.stdout:
            content = line.decode(_ENCODING).rstrip()
            _log_file.write("{} [{}] <<< {}\n".format(_now_iso(), self._key, content))
            _log_file.flush()
            self._handle_input(content)
        self._is_alive = False

    def _readline(self, wait_time=0):
        while True:
            value = self.poll()
            if value is not None:
                return value
            time.sleep(wait_time)
