from typing import Optional

from ender.game_plan.condition.condition import ICondition
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class HaveUnit(ICondition):
    bot_ai: BotAI

    def __init__(
        self,
        unit_type: Optional[UnitTypeId] = None,
        amount: int = 1,
        position: Optional[Point2] = None,
        distance: float = 11,
    ):
        self.unit_type = unit_type
        self.amount = amount
        self.position = position
        self.distance = distance

    def setup(self, bot_ai: BotAI):
        self.bot_ai = bot_ai

    def check(self) -> bool:
        units = self.bot_ai.units
        if self.unit_type:
            units = units.of_type(self.unit_type)
        if self.position:
            units = units.closer_than(self.distance, self.position)
        return units.amount >= self.amount
