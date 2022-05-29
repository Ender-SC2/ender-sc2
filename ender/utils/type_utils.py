from typing import Iterable


def convert_into_iterable(obj):
    if not obj:
        raise Exception("Possible a issue on setup.")
    if not isinstance(obj, Iterable):
        return [obj]
