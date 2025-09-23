import threading
import time

from .pio_wrapper import PioWrapper

_UNUSED_INSTANCE_TIME = 60 * 60


class PioPool:
    def __init__(self, *, adapter_args={}):
        self._pio_args = adapter_args
        self._instances = {}
        self._idle_instances = []
        self._background_thread = threading.Thread(target=self._run_background)
        self._background_thread.start()

    def get(self, key):
        instance = self._instances.get(key)
        return None if instance["idle"] else instance

    def get_new(self):
        now = time.time()
        if self._idle_instances:
            instance_key = self._idle_instances.pop()
            instance = self._instances[instance_key]
            instance["idle"] = False
            instance["last_use"] = now
            return instance
        pio = PioWrapper(**self._pio_args)
        if not pio.start():
            pio.exit()
            return None
        print("create_instance", pio.get_key())
        instance = {
            "creation_time": now,
            "idle": False,
            "key": pio.get_key(),
            "last_use": now,
            "pio": pio,
        }
        self._instances[instance["key"]] = instance
        return instance

    def update(self, instance):
        instance["last_use"] = time.time()

    def _release_instance(self, instance):
        pio = instance["pio"]
        if pio.is_tree_present():
            pio.free_tree()
        print("release_instance", pio.get_key())
        instance["idle"] = True
        self._idle_instances.append(instance["key"])

    def _run_background(self):
        while True:
            self._update_idle_instances()
            time.sleep(5 * 60)

    def _update_idle_instances(self):
        now = time.time()
        for instance in self._instances.values():
            if (
                not instance["idle"]
                and instance["last_use"] + _UNUSED_INSTANCE_TIME < now
            ):
                self._release_instance(instance)
