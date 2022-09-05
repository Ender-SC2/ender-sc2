import inspect
from typing import List

from ender.behavior import IBehavior
from ender.game_plan.condition import ICondition
from ender.unit import UnitInterface
from sc2.bot_ai import BotAI
from test.setup import ITestSetup


class EnderTestBot(BotAI):
    def __init__(
        self, behaviors: List[IBehavior], test_setup: ITestSetup, stop_condition: ICondition,
    ):
        super().__init__()
        self.setup = False
        self.behaviors = behaviors
        self.test_setup = test_setup
        self.stop_condition = stop_condition
        self.save_replay_as = inspect.stack()[1][3]
        self.unit_interface = UnitInterface()
        self.stop_triggered = False

    async def on_start(self):
        self.client.game_step = 4

    async def on_step(self, iteration: int):
        if not self.setup:
            self.setup = True
            await self.client.move_camera(self.game_info.map_center)
            await self.test_setup.setup(self)
            self.stop_condition.setup(self)
            for behavior in self.behaviors:
                behavior.setup(self, self.unit_interface)
            return
        elif self.stop_condition.check():
            self.stop_triggered = True
            await self.client.save_replay(f"{self.save_replay_as}.SC2Replay")
            await self.client.debug_leave()

        for behavior in self.behaviors:
            await behavior.on_step(iteration)
        await self.unit_interface.execute()

    def stopped(self):
        return self.stop_triggered
