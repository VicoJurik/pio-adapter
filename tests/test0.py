from pio_adapter import PioAdapter

print("Library loaded ok")


def _ok(status):
    return "ok!" if status else "FAILED!!!"


def main():
    pio = PioAdapter()
    print("Adapter created ok")

    started = pio.start()
    print("PioSOLVER started by adapter {}".format(_ok(started)))

    is_alive = pio.is_alive()
    print("Adapter alive {}".format(_ok(is_alive)))

    print("Solver version: {}".format(pio.show_version()))
    print("Solver build version: {}".format(pio.show_build_version()))

    is_ready = pio.is_ready()
    print("Solver is ready {}".format(_ok(is_ready)))

    print(end="Bench...", flush=True)
    print(" {} ok!".format(pio.bench()))

    stopped = pio.stop()
    print("PioSOLVER stopped by adapter {}".format(_ok(stopped)))

    exited = pio.exit()
    print("Adapter exit {}".format(_ok(exited)))


if __name__ == "__main__":
    main()
