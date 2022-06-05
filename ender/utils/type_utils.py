from typing import Iterable

from loguru import logger


def convert_into_iterable(obj):
    if not obj:
        raise Exception("Possible a issue on setup.")
    if not isinstance(obj, Iterable):
        return [obj]
    return obj


def get_version() -> str:
    try:
        with open("version.txt", "r") as file:
            return file.readline()
    except Exception as e:
        logger.warning(f"Fail reading version file: {e}")
        return "unknown"
