import os


def get_root_dir() -> str:
    "Get an abosolute path from the current working directory"
    return os.path.dirname(os.path.abspath(__file__))


def is_path(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


LIB_DIR = get_root_dir()
