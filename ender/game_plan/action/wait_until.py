from ender.common import Common
from ender.game_plan.action.action import IAction


class WaitUntil(IAction):
    def __init__(self, time: float, action: IAction):
        self.common = None
        self.time = time
        self.action = action

    def setup(self, common: Common):
        self.common = common
        self.action.setup(common)

    def execute(self):
        if self.common.time < self.time:
            return
        self.action.execute()
