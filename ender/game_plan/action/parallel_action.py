from typing import List

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.utils.type_utils import convert_into_iterable


class ParallelAction(IAction):
    def __init__(self, actions: List[IAction]):
        self.actions = convert_into_iterable(actions)

    def setup(self, common: Common):
        for action in self.actions:
            action.setup(common)

    """
    Self mutable, completed once all steps are completed
    """

    def execute(self) -> bool:
        self.actions = [step for step in self.actions if not step.execute()]
        return len(self.actions) == 0
