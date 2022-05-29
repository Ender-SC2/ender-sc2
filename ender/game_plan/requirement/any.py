from typing import List

from ender.common import Common
from ender.game_plan.requirement.requirement import Requirement


class Any(Requirement):
    def __init__(
            self,
            conditions: List[Requirement]
    ):
        self.conditions = conditions

    def setup(self, common: Common):
        super().setup(common)

        for condition in self.conditions:
            condition.setup(common)

    def check(self) -> bool:
        for condition in self.conditions:
            if condition.check():
                return True

        return False
