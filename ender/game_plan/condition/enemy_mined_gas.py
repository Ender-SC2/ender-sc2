from loguru import logger

from ender.game_plan.condition.condition import ICondition
from sc2.bot_ai import BotAI


class EnemyMinedGas(ICondition):
    bot_ai: BotAI
    DEFAULT_GAS = 2250

    def __init__(self, amount: int):
        self.amount = amount

    def setup(self, bot_ai: BotAI):
        self.bot_ai = bot_ai

    def check(self) -> bool:
        mined_gas = sum(map(lambda unit: self.DEFAULT_GAS - unit.vespene_contents, self.bot_ai.vespene_geyser.enemy))
        logger.info(f"Mined gas {mined_gas}")
        return mined_gas > self.amount
