from typing import Optional, Union, Iterable

from loguru import logger

from ender.game_plan.condition.condition import ICondition
from ender.utils.type_utils import convert_into_iterable
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class EnemyStructureReadyBefore(ICondition):
    bot_ai: BotAI

    def __init__(
        self,
        unit_type: Union[UnitTypeId, Iterable[UnitTypeId]],
        time_limit: float,
        amount: int = 1,
        position: Optional[Point2] = None,
        distance: float = 11,
    ):
        self.unit_type = convert_into_iterable(unit_type)
        self.time_limit = time_limit
        self.amount = amount
        self.position = position
        self.distance = distance

    def setup(self, bot_ai: BotAI):
        self.bot_ai = bot_ai

    def check(self) -> bool:
        if self.bot_ai.time > self.time_limit:
            return False
        enemy_units = self.bot_ai.enemy_structures.of_type(self.unit_type).filter(
            lambda structure: structure.is_ready
            or self.bot_ai.time + structure._type_data.cost.time * (1 - structure.build_progress) < self.time_limit
        )
        if self.position:
            enemy_units = enemy_units.closer_than(self.distance, self.position)
        return enemy_units.amount >= self.amount
