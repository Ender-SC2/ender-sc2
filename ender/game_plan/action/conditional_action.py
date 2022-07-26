from typing import Optional

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.game_plan.condition.condition import ICondition


class ConditionalAction(IAction):
    def __init__(self, condition: Optional[ICondition], action: IAction):
        self.condition = condition
        self.action = action

    def setup(self, common: Common):
        if self.condition:
            self.condition.setup(common)
        self.action.setup(common)

    """
    Will execute an action if the condition is true
    """

    def execute(self) -> bool:
        if not self.condition or self.condition.check():
            return self.action.execute()
        return False
