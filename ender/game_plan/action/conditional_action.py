from typing import Optional

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.game_plan.condition.condition import ICondition


class ConditionalAction(IAction):
    def __init__(self, condition: ICondition, action: IAction, else_action: Optional[IAction] = None):
        self.condition = condition
        self.action = action
        self.else_action = else_action

    def setup(self, common: Common):
        self.condition.setup(common)
        self.action.setup(common)
        if self.else_action:
            self.else_action.setup(common)

    """
    Will execute an action if the condition is true
    """

    def execute(self) -> bool:
        if self.condition.check():
            return self.action.execute()
        elif self.else_action:
            return self.else_action.execute()
        return False
