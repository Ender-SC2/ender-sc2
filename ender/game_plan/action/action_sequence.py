from typing import List

from loguru import logger

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.utils.type_utils import convert_into_iterable


class ActionSequence(IAction):
    def __init__(self, actions: List[IAction]):
        self.actions = convert_into_iterable(actions)
        self.current_action = 0

    def setup(self, common: Common):
        for action in self.actions:
            action.setup(common)

    """
    Self mutable, once a step is completed it will go into the next
    """

    def execute(self) -> bool:
        if self.actions[self.current_action].execute():
            logger.info(f"Completed action {self.current_action} out of {len(self.actions)}")
            self.current_action += 1
        return self.current_action >= len(self.actions)
