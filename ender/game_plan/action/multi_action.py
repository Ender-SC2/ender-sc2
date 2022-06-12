from typing import List

from ender.common import Common
from ender.game_plan.action.action import IAction


class MultiAction:

    def __init__(self, action_list: List[IAction]):
        self.action_list = action_list

    def setup(self, common: Common):
        for action in self.action_list:
            action.setup(common)

    async def execute(self):
        for action in self.action_list:
            await action.execute()
