from dataclasses import dataclass, field
from typing import Union, Optional

from ender.unit.unit_command import IUnitCommand
from sc2.position import Point2
from sc2.unit import Unit


@dataclass(frozen=True)
class AttackCommand(IUnitCommand):
    """Class for keeping track of an attack command."""

    target: Union[Unit, Point2]
    origin: Optional[str] = field(compare=False)

    async def execute(self, unit: Unit, queue: bool = False):
        unit.attack(self.target, queue)
