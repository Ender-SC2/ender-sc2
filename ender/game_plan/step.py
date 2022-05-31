from abc import abstractmethod
from typing import Optional

from ender.common import Common
from ender.game_plan.action.action import Action
from ender.game_plan.requirement.requirement import Requirement


class Step:
    def __init__(self, requirement: Optional[Requirement], action: Action):
        self.requirement = requirement
        self.action = action

    def setup(self, common: Common):
        if self.requirement:
            self.requirement.setup(common)
        self.action.setup(common)

    @abstractmethod
    def execute(self):
        if self.requirement and self.requirement.check():
            self.action.execute()
