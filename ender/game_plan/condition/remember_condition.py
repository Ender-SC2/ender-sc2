from ender.game_plan.condition.condition import ICondition
from sc2.bot_ai import BotAI


class RememberCondition(ICondition):
    bot_ai: BotAI

    def __init__(self, condition: ICondition):
        self.condition_passed = False
        self.condition = condition

    def setup(self, bot_ai: BotAI):
        self.bot_ai = bot_ai
        self.condition.setup(bot_ai)

    def check(self) -> bool:
        if not self.condition_passed:
            self.condition_passed = self.condition.check()
        return self.condition_passed
