from typing import List, Union

from ender.common import Common
from ender.game_plan.requirement.requirement import Requirement
from ender.utils.type_utils import convert_into_iterable


class All(Requirement):
    def __init__(self, requirements: Union[List[Requirement], Requirement]):
        self.requirements = convert_into_iterable(requirements)

    def setup(self, common: Common):
        super().setup(common)
        for requirement in self.requirements:
            requirement.setup(common)

    def check(self) -> bool:
        for requirement in self.requirements:
            if not requirement.check():
                return False

        return True
