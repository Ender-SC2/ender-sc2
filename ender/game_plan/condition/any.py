from typing import List, Union

from ender.game_plan.condition.condition import ICondition
from ender.utils.type_utils import convert_into_iterable
from sc2.bot_ai import BotAI


class Any(ICondition):
    def __init__(self, conditions: Union[List[ICondition], ICondition]):
        self.conditions = convert_into_iterable(conditions)

    def setup(self, bot_ai: BotAI):
        for condition in self.conditions:
            condition.setup(bot_ai)

    def check(self) -> bool:
        for condition in self.conditions:
            if condition.check():
                return True

        return False
