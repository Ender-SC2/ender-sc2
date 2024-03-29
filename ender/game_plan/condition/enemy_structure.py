from typing import Optional, Union

from ender.game_plan.condition.condition import ICondition
from ender.utils.type_utils import convert_into_iterable
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class EnemyStructure(ICondition):
    bot_ai: BotAI

    def __init__(
        self,
        unit_type: Union[UnitTypeId, list[UnitTypeId]],
        amount: int = 1,
        position: Optional[Point2] = None,
        distance: float = 11,
    ):
        self.unit_type = convert_into_iterable(unit_type)
        self.amount = amount
        self.position = position
        self.distance = distance

    def setup(self, bot_ai: BotAI):
        self.bot_ai = bot_ai

    def check(self) -> bool:
        enemy_units = self.bot_ai.enemy_structures.of_type(self.unit_type)
        if self.position:
            enemy_units = enemy_units.closer_than(self.distance, self.position)
        return enemy_units.amount >= self.amount
