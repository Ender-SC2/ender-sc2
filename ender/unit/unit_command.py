from abc import ABC

from sc2.unit import Unit


class IUnitCommand(ABC):
    async def execute(self, unit: Unit, queue: bool = False):
        raise NotImplementedError
