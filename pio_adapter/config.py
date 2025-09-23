import json
import os


_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "resources", "config.json")


config = None
try:
    with open(_CONFIG_PATH, "r") as fp:
        config = json.load(fp)
except FileNotFoundError:
    print("Error: cannot find configuration file")
    exit(1)
