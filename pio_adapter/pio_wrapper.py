from utils import fix_wsl_path, random_key

from .config import config
from .pio_instance import PioInstance


_BOOL_ARRAY_SETTINGS = ["isomorphism"]
_FLOAT_SETTINGS = ["accuracy", "hopeless_thres", "step"]
_FLOAT_ARRAY_SETTINGS = ["recalc_accuracy"]
_INT_SETTINGS = ["thread_no", "info_freq"]
_ACCURACY_MODE_SETTING = "accuracy mode"

_RESULTS_KEYMAP = {
    "running time": "running_time",
    "EV OOP": "oop_ev",
    "EV IP": "ip_ev",
    "OOP's MES": "oop_mes",
    "IP's MES": "ip_mes",
    "Exploitable for": "exploitable",
}

_PLAYERS = ["OOP", "IP"]
_STREETS = ["flop", "turn", "river"]

_STREETS_INDICES = {"flop": 3, "turn": 4, "river": 5}

_DEFAULT_END_STRING = "END"

ALGO_AUTO = "auto"
ALGO_CFR = "pio_cfr"
ALGO_ORIGINAL = "original_pio"

ROOT_NODE_ID = "r:0"

IP_NODE_TYPE = "IP_DEC"
OOP_NODE_TYPE = "OOP_DEC"
SPLIT_NODE_TYPE = "SPLIT_NODE"
END_NODE_TYPE = "END_NODE"

OOP = "OOP"
IP = "IP"


def dec_node_player(node_type):
    if node_type == IP_NODE_TYPE:
        return IP
    if node_type == OOP_NODE_TYPE:
        return OOP
    raise ValueError(node_type)


def _int_of_bool(b):
    return "1" if b else "0"


class PioWrapper:
    def __init__(self, solver_version=config["version"], wsl=False):
        self._key = random_key()
        self._instance = PioInstance(self._key, version=solver_version)
        self._solver_started = False
        self._solver_stopped = False
        self._tree_path = None
        self._wsl = wsl

    def add_all_flops(self):
        self._write("add_all_flops")
        return self._read() == "add_all_flops ok!"

    def add_line(self, ints):
        ints = " ".join(str(i) for i in ints)
        self._write(f"add_line {ints}")
        return self._read() == "add_line ok!"

    def add_preflop_line(self, ints):
        ints = " ".join(str(i) for i in ints)
        self._write(f"add_preflop_line {ints}")
        return self._read() == "add_preflop_line ok!"

    def add_schematic_tree(self, node_id):
        self._write(f"add_schematic_tree {node_id}")
        return self._read() == "add_schematic_tree ok!"

    def add_to_subset(self, weight, c1, c2, c3):
        self._write(f"add_to_subset {weight} {c1} {c2} {c3}")
        return self._read() == "add_to_subset ok!"

    def bench(self):
        self._write("bench")
        _, value = self._read().split(":")
        return float(value.strip())

    def build_preflop_tree(self):
        self._write("build_preflop_tree")
        return self._read() == "build_preflop_tree ok!"

    def build_tree(self):
        self._write("build_tree")
        return self._read() == "build_tree ok!"

    def calc_ev(self, player, node_id):
        self._write(f"calc_ev {player} {node_id}")
        lines = self._read_multi()
        return [[float(f) for f in line.split(" ")] for line in lines]

    def calc_eq(self, player):
        self._write(f"calc_eq {player}")
        lines = self._read_multi()
        return [[float(f) for f in line.split(" ")] for line in lines]

    def calc_eq_node(self, player, node_id):
        self._write(f"calc_eq_node {player} {node_id}")
        lines = self._read_multi()
        return [[float(f) for f in line.split(" ")] for line in lines[:2]], float(
            lines[2]
        )

    def calc_eq_preflop(self, player, node_id):
        self._write(f"calc_eq_preflop {player} {node_id}")
        return [[float(f) for f in self._read().split(" ")] for _ in range(2)], float(
            self._read()
        )

    def calc_global_freq(self, node_id):
        self._write(f"calc_global_freq {node_id}")
        return float(self._read())

    def calc_line_freq(self, node_id):
        self._write(f"calc_line_freq {node_id}")
        return float(self._read())

    def calc_results(self):
        self._write("calc_results")
        data = {}
        for line in self._read_multi():
            key, value = line.split(":")
            data[_RESULTS_KEYMAP[key]] = float(value.strip())
        return data

    def change_step(self, step):
        self._write(f"change_step {step}")
        return self._read() == "change_step ok!"

    def clear_cache(self):
        self._write("clear_cache")
        return self._read() == "clear_cache ok!"

    def clear_lines(self):
        self._write("clear_lines")
        return self._read() == "clear_lines ok!"

    def clear_preflop_lines(self):
        self._write("clear_preflop_lines")
        return self._read() == "clear_preflop_lines ok!"

    def combo_lock_node(self, node_id, bools):
        bools = " ".join(("1" if b else "0") for b in bools)
        self._write(f"combo_lock_node {node_id} {bools}")
        return self._read() == "combo_lock_node ok!"

    def cut_line(self, node_id):
        self._write(f"cut_line {node_id}")
        return self._read() == "cut_line ok!"

    def dump_tree(self, file_path, mode="full"):
        if self._wsl:
            file_path = fix_wsl_path(file_path)
        self._write(f"dump_tree {file_path} {mode}")
        return self._read() == "dump_tree ok!"

    def end_string(self):
        return self._instance.end_string()

    def estimate_schematic_tree(self):
        self._write("estimate_schematic_tree")
        return self._read()

    def estimate_tree(self):
        self._write("estimate_tree")
        return self._read()

    def exit(self):
        self._write("exit")
        return True

    def explo_partial(self, node_id):
        self._write(f"explo_partial {node_id}")
        return float(self._read())

    def force_line(self, ints):
        ints = " ".join(str(i) for i in ints)
        self._write(f"force_line {ints}")
        return self._read() == "force_line ok!"

    def forget(self, street):
        self._write(f"forget {street}")
        return self._read() == "forget ok!"

    def free_tree(self):
        self._write("free_tree")
        if self._read() != "free_tree ok!":
            return False
        self._tree_path = None
        return True

    def go(self, seconds=None, steps=None):
        message = "go"
        if seconds is not None:
            message += f" {seconds} seconds"
        elif steps is not None:
            message += f" {steps}"
        self._write(message)
        return self._read() == "go ok!"

    def ignore_mem_check(self, value=True):
        arg = "on" if value else "off"
        self._write(f"ignore_mem_check {arg}")
        return self._read() == "ignore_mem_check ok!"

    def is_alive(self):
        return self._instance.is_alive()

    def is_ready(self):
        self._write("is_ready")
        return self._read() == "is_ready ok!"

    def is_tree_present(self):
        self._write("is_tree_present")
        return self._read() == "true"

    def list_algorithms(self):
        self._write("list_algorithms")
        algorithms = []
        for line in self._read_multi():
            code, name, description = line.split(",")
            algorithm = {"code": code, "description": description, "name": name}
            algorithms.append(algorithm)
        return algorithms

    def lock_node(self, node_id):
        self._write(f"lock_node {node_id}")
        return self._read() == "lock_node ok!"

    def load_script(self, file_path):
        if self._wsl:
            file_path = fix_wsl_path(file_path)
        self._write(f"load_script {file_path}")
        return self._read() == "load_script ok!"

    def load_script_silent(self, file_path):
        if self._wsl:
            file_path = fix_wsl_path(file_path)
        self._write(f"load_script_silent {file_path}")
        self._read_multi()
        return True
        # return self._read() == "load_script_silent ok!"

    def load_tree_if_other(self, file_path):
        if self._wsl:
            file_path = fix_wsl_path(file_path)
        print("reload:", self._tree_path, file_path)
        if self._tree_path == file_path:
            return True
        if self._tree_path is not None:
            if not self.free_tree():
                return False
        return self.load_tree(file_path)

    def load_tree(self, file_path):
        if self._wsl:
            file_path = fix_wsl_path(file_path)
        self._write(f"load_tree {file_path}")
        if self._read() != "load_tree ok!":
            return False
        self._tree_path = file_path
        return True

    def needed_memory(self):
        self._write("needed_memory")
        return int(self._read()), int(self._read())

    def node_count(self):
        self._write("node_count")
        data = {"flop_total": 0, "turn_total": 0, "river_total": 0}
        category = None
        for line in self._read_multi():
            key, value = [g for g in line.strip().split(" ") if g]
            value = int(value)
            if key.endswith(":"):
                category = key[:-1].lower()
                key = "total"
            key = key.lower()
            data[f"{category}_{key}"] = value
            if key == "flop":
                data["flop_total"] += value
            elif key == "turn":
                data["turn_total"] += value
            elif key == "river":
                data["river_total"] += value
        return data

    def normalize_tree(self):
        self._write("normalize_tree")
        return self._read() == "normalize_tree ok!"

    def recover_subset(self):
        self._write(f"recover_subset")
        return self._read() == "recover_subset ok!"

    def remove_line(self, ints):
        ints = " ".join(str(i) for i in ints)
        self._write(f"remove_line {ints}")
        return self._read() == "remove_line ok!"

    def remove_preflop_line(self, ints):
        ints = " ".join(str(i) for i in ints)
        self._write(f"remove_preflop_line {ints}")
        return self._read() == "remove_preflop_line ok!"

    def reset_end_string(self):
        self._write("reset_end_string")
        if "reset_end_string ok!" != self._read():
            return False
        self._instance.set_end_string(_DEFAULT_END_STRING)

    def reset_subset(self):
        self._write("reset_subset")
        return self._read() == "reset_subset ok!"

    def round_up_to(self, player, chunks, street):
        if (
            player not in _PLAYERS
            or not isinstance(chunks, int)
            or street not in _STREETS
        ):
            return False
        self._write(f"round_up_to {player} {chunks} {street}")
        return self._read() == "round_up_to ok!"

    def set_accuracy(self, value=0.0, chips=True):
        mode = "chips" if chips else "fraction"
        self._write(f"set_accuracy {value} {mode}")
        return self._read() == "set_accuracy ok!"

    def set_adjust_strat(self, starting_step, hopeless_time, adjust_mode):
        self._write(
            f"set_adjust_strat {starting_step} {hopeless_time} {_int_of_bool(adjust_mode)}"
        )
        return self._read() == "set_adjust_strat ok!"

    def set_algorithm(self, algorithm):
        self._write(f"set_algorithm {algorithm}")
        return self._read() == "set_algorithm ok!"

    def set_always_recalc(self, street, timeout):
        street_index = _STREETS_INDICES.get(street)
        if street_index is None:
            return False
        self._write(f"set_always_recalc {street_index} {timeout}")
        return self._read() == "set_always_recalc ok!"

    def set_board(self, board):
        board = board if isinstance(board, str) else "".join(board)
        self._write(f"set_board {board}")
        return self._read() == "set_board ok!"

    def set_end_string(self, end_string):
        self._write(f"set_end_string {end_string}")
        if self._read() != "set_end_string ok!":
            return False
        self._instance.set_end_string(end_string)
        return True

    def set_eff_stack(self, value):
        self._write(f"set_eff_stack {value}")
        return self._read() == "set_eff_stack ok!"

    def set_first_iteration_player(self, player):
        self._write(f"set_first_iteration_player {player}")
        return self._read() == "set_first_iteration_player ok!"

    def set_info_freq(self, value):
        self._write(f"set_info_freq {value}")
        return self._read() == "set_info_freq ok!"

    def set_isomorphism(self, flop, turn):
        self._write(f"set_isomorphism {_int_of_bool(flop)} {_int_of_bool(turn)}")
        return self._read() == "set_isomorphism ok!"

    def set_mes(self, player):
        self._write(f"set_mes {player}")
        return self._read() == "set_mes ok!"

    def set_pot(self, value, oop=0, ip=0):
        self._write(f"set_pot {oop} {ip} {value}")
        return self._read() == "set_pot ok!"

    def set_rake(self, fraction, cap):
        self._write(f"set_rake {fraction} {cap}")
        return self._read() == "set_rake ok!"

    def set_range(self, player, floats):
        freqs = " ".join(str(f) for f in floats)
        self._write(f"set_range {player} {freqs}")
        return self._read() == "set_range ok!"

    def set_recalc_accuracy(self, flop, turn, river):
        self._write(f"set_recalc_accuracy {flop} {turn} {river}")
        return self._read() == "set_recalc_accuracy ok!"

    def set_strategy(self, node_id, strategy):
        self._write(
            "set_strategy {} {}".format(
                node_id, " ".join(" ".join(str(f) for f in freqs) for freqs in strategy)
            )
        )
        return self._read() == "set_strategy ok!"

    def set_threads(self, value):
        self._write(f"set_threads {value}")
        return self._read() == "set_threads ok!"

    def show_all_freqs(self, is_global=True):
        arg = "global" if is_global else "local"
        self._write(f"show_all_freqs {arg}")
        data = {}
        for line in self._read_multi():
            line, freq = line.split(" - ")
            data[line] = float(freq)
        return data

    def show_build_version(self):
        self._write("show_build_version")
        return self._read()

    def show_categories(self, board):
        board = " ".join(board)
        self._write(f"show_categories {board}")
        return [[int(i) for i in line.split(" ")] for line in self._read_multi()]

    def show_category_names(self):
        self._write("show_category_names")
        return [line.split(" ") for line in self._read_multi()]

    def show_children(self, node_id):
        self._write(f"show_children {node_id}")
        lines = self._read_multi()
        children = []
        for offset in range(0, len(lines), 8):
            children.append(self._parse_node_info(lines[offset + 1 :]))
        return children

    def show_effective_stack(self):
        self._write("show_effective_stack")
        return int(self._read())

    def show_hand_order(self):
        self._write("show_hand_order")
        hands = self._read()
        return hands.split(" ")

    def show_iters(self):
        self._write("show_iters")
        return int(self._read())

    def show_locked_combos(self, node_id):
        self._write(f"show_locked_combos {node_id}")
        return [float(f) for f in self._read().split(" ")]

    def show_memory(self):
        self._write("show_memory")
        lines = [self._read() for _ in range(2)]
        return tuple(int(line.split(" ")[-2]) for line in lines)

    def show_node(self, node_id):
        self._write(f"show_node {node_id}")
        lines = self._read_multi()
        return self._parse_node_info(lines)

    def show_preflop_order(self):
        self._write("show_preflop_order")
        hands = self._read()
        return hands.split(" ")

    def show_range(self, player, node_id):
        self._write(f"show_range {player} {node_id}")
        return [float(f) for f in self._read().split(" ")]

    def show_settings(self):
        self._write("show_settings")
        settings = {}
        for line in self._read_multi():
            key, value = line.split(":")
            value = value.strip()
            if key in _FLOAT_ARRAY_SETTINGS:
                value = [float(v) for v in value.split(" ")]
            elif key in _BOOL_ARRAY_SETTINGS:
                value = [v == "1" for v in value.split(" ")]
            elif key in _FLOAT_SETTINGS:
                value = float(value)
            elif key in _INT_SETTINGS:
                value = int(value)
            elif key == _ACCURACY_MODE_SETTING:
                value = value == "chips"
            else:
                value = value == "1"
            settings[key.strip()] = value
        return settings

    def show_step(self):
        self._write("show_step")
        return float(self._read())

    def show_strategy(self, node_id):
        self._write(f"show_strategy {node_id}")
        strategy = []
        for line in self._read_multi():
            strategy.append([float(f) for f in line.split(" ")])
        return strategy

    def show_strategy_pp(self, node_id):
        self._write(f"show_strategy_pp {node_id}")
        hands = []
        for line in self._read_multi():
            tokens = line.split(" ")
            hands.append((tokens[0][:4], [float(token) for token in tokens[1:]]))

    def show_subset(self):
        self._write("show_subsets")
        flops = []
        for line in self._read_multi():
            if line.endswith("total"):
                continue
            weight, c1, c2, c3 = line.split(" ")
            flops.append(("".join([c1, c2, c3]), float(weight)))
        return flops

    def show_tree_params(self):
        self._write("show_tree_params")
        data = {}
        for line in self._read_multi():
            key, value = line.split(":")
            key = key.strip()
            value = value.strip()
            if key == "board":
                if value == "not set":
                    value = None
                else:
                    value = value.split(" ")
            elif key in ["pot", "bet_sizes"]:
                value = [int(p) for p in value.split(" ") if p]
            elif key == "donk_bet":
                value = value == "TRUE"
            data[key] = value
        return data

    def show_version(self):
        self._write("show_version")
        return self._read()

    def small_strats(self, mode):
        mode = "on" if mode is True else "off" if mode is False else mode
        self._write(f"small_strats {mode}")
        return self._read() == "small_strats ok!"

    def solve_all_splits(self, street):
        if street not in ["turns", "rivers"]:
            return False
        self._write(f"solve_all_splits {street}")
        return self._read() == "solve_all_splits ok!"

    def solve_partial(self, node_id):
        self._write(f"solve_partial {node_id}")
        return self._read() == "solve_partial ok!"

    def solver_time(self):
        self._write("solver_time")
        return float(self._read())

    def solver_version(self):
        return self._instance.version()

    def stdoutback(self):
        self._write("stdoutback")
        return self._read() == "stdoutback ok!"

    def stdoutredi(self, file_path):
        if self._wsl:
            file_path = fix_wsl_path(file_path)
        self._write(f"stdoutredi {file_path}")
        return True

    def stdoutredi_append(self, file_path):
        if self._wsl:
            file_path = fix_wsl_path(file_path)
        self._write(f"stdoutredi_append {file_path}")
        return True

    def stop(self):
        self._write("stop")
        return self._read() == "stop ok!"

    def take_a_break(self, seconds):
        self._write(f"take_a_break {seconds}")
        return self._read() == "take_a_break ok!"

    def tree_path(self):
        return self._tree_path

    def unlock_node(self, node_id):
        self._write(f"unlock_node {node_id}")
        return self._read() == "unlock_node ok!"

    def wait_for_solver(self):
        self._write("wait_for_solver")
        return self._read() == "wait_for_solver ok!"

    def add_listener(self, listener):
        self._instance.add_listener(listener)

    def remove_listener(self, listener):
        self._instance.remove_listener(listener)

    def get_key(self):
        return self._key

    def get_solver_started(self):
        return self._solver_started

    def _parse_node_info(self, lines):
        if len(lines) < 6:
            return {"error": lines}
        data = {}
        data["node_id"] = lines[0]
        data["node_type"] = lines[1]
        data["board"] = lines[2].split(" ")
        data["pot"] = [int(i) for i in lines[3].split(" ")]
        data["children_count"] = int(lines[4].split(" ")[0])
        data["flags"] = [f for f in lines[5].split(":")[1].strip().split(" ") if f]
        return data

    def _write(self, cmd):
        self._instance.write(cmd)

    def _read(self):
        return self._instance.readline()

    def _read_multi(self):
        return self._instance.readmultilines()

    def start(self):
        self._instance.start()
        for _ in range(4):
            self._instance._readline()
        if self.solver_version() == 2:
            if not self.set_end_string(config["end_string"]):
                return False
        return True
