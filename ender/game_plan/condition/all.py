from typing import List, Union

from ender.game_plan.condition.condition import ICondition
from ender.utils.type_utils import convert_into_iterable
from sc2.bot_ai import BotAI


class All(ICondition):
    def __init__(self, conditions: Union[List[ICondition], ICondition]):
        self.conditions = convert_into_iterable(conditions)

    def setup(self, bot_ai: BotAI):
        for requirement in self.conditions:
            requirement.setup(bot_ai)

    def check(self) -> bool:
        for condition in self.conditions:
            if not condition.check():
                return False

        return True
