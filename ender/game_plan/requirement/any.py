from typing import List, Union

from ender.common import Common
from ender.game_plan.requirement.requirement import Requirement
from ender.utils.type_utils import convert_into_iterable


class Any(Requirement):
    def __init__(
            self,
            conditions: Union[List[Requirement], Requirement]
    ):
        self.conditions = convert_into_iterable(conditions)

    def setup(self, common: Common):
        super().setup(common)

        for condition in self.conditions:
            condition.setup(common)

    def check(self) -> bool:
        for condition in self.conditions:
            if condition.check():
                return True

        return False
