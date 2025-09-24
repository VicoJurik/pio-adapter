import random


def fix_wsl_path(path):
    return path.replace("/mnt/c/", "C:\\").replace("/mnt/d/", "D:\\").replace("/", "\\")


def random_key(charset="0123456789abcdef", length=16):
    return "".join(random.choice(charset) for _ in range(length))
