from typing import TypeVar
from typing import Union

from loguru import logger

T = TypeVar("T")


def convert_into_iterable(obj: Union[T, list[T]]) -> list[T]:
    if not obj:
        raise Exception("Possible a issue on setup.")
    if not isinstance(obj, list):
        return [obj]
    return obj


def get_version() -> str:
    try:
        with open("version.txt", "r") as file:
            return file.readline()
    except Exception as e:
        logger.warning(f"Fail reading version file: {e}")
        return "unknown"
