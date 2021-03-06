from typing import List, Union

from ender.common import Common

from ender.game_plan.action.action import IAction
from ender.utils.type_utils import convert_into_iterable


class GamePlan:
    def __init__(self, actions: Union[IAction, List[IAction]]):
        self.actions = convert_into_iterable(actions)

    def setup(self, common: Common):
        for step in self.actions:
            step.setup(common)

    """
    Self mutable, will remove completed actions
    """

    async def execute(self):
        self.actions = [step for step in self.actions if not step.execute()]
