from typing import List, Union

from ender.utils.type_utils import convert_into_iterable
from sc2.bot_ai import BotAI
from test.setup.test_setup import ITestSetup


class MultipleTestSetup(ITestSetup):
    def __init__(self, requirements: Union[List[ITestSetup], ITestSetup]):
        self.setups = convert_into_iterable(requirements)

    async def setup(self, bot_ai: BotAI):
        for setup in self.setups:
            await setup.setup(bot_ai)
