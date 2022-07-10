# upgraded.py

from sc2.bot_ai import BotAI
from test.setup import ITestSetup


class UpgradedSetup(ITestSetup):
    upgrades = 0

    async def setup(self, bot_ai: BotAI):
        await bot_ai.client.debug_upgrade()
