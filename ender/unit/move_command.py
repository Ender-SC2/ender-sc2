from dataclasses import dataclass
from typing import Union, Optional

from ender.unit.unit_command import IUnitCommand
from sc2.position import Point2
from sc2.unit import Unit


@dataclass(frozen=True)
class MoveCommand(IUnitCommand):
    target: Union[Unit, Point2]
    origin: Optional[str] = None

    async def execute(self, unit: Unit, queue: bool = False):
        unit.move(self.target, queue)