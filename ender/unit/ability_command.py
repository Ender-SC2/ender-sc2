from dataclasses import dataclass
from typing import Union, Optional

from ender.unit.unit_command import IUnitCommand
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit


@dataclass(frozen=True)
class AbilityCommand(IUnitCommand):
    ability: AbilityId
    target: Union[Unit, Point2]
    origin: Optional[str] = None

    async def execute(self, unit: Unit, queue: bool = False):
        unit(self.ability, self.target, queue)
