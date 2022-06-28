from dataclasses import dataclass

from ender.unit.unit_command import IUnitCommand
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


@dataclass(frozen=True)
class BuildCommand(IUnitCommand):
    unit_type: UnitTypeId
    position: Point2

    async def execute(self, unit: Unit, queue: bool = False):
        unit.build(self.unit_type, self.position, queue)
