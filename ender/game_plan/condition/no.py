from ender.game_plan.condition.condition import ICondition
from sc2.bot_ai import BotAI


class No(ICondition):
    def __init__(self, condition: ICondition):
        self.condition = condition

    def setup(self, bot_ai: BotAI):
        self.condition.setup(bot_ai)

    def check(self) -> bool:
        return not self.condition.check()
