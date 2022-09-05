from loguru import logger

from ender.game_plan.action.action import IAction


class WaitUntil(IAction):
    def __init__(self, time: float):
        self.time = time

    def execute(self):
        if self.common.time < self.time:
            return False
        logger.info(f"Completed WaitUntil action {self.time}")
        return True
