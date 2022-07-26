from loguru import logger

from ender.common import Common
from ender.game_plan.action.action import IAction


class WaitUntil(IAction):
    def __init__(self, time: float):
        self.common = None
        self.time = time

    def setup(self, common: Common):
        self.common = common

    def execute(self):
        if self.common.time < self.time:
            return False
        logger.info(f"Completed WaitUntil action {self.time}")
        return True
