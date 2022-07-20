from ender.game_plan.condition.condition import ICondition
from sc2.bot_ai import BotAI


class BeforeTime(ICondition):
    bot_ai: BotAI

    def __init__(self, time: float):
        self.time = time

    def setup(self, bot_ai: BotAI):
        self.bot_ai = bot_ai

    def check(self) -> bool:
        return self.bot_ai.time < self.time
