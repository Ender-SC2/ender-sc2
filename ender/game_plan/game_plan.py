from abc import abstractmethod
from typing import List, Union

from ender.common import Common
from ender.game_plan.step import Step
from ender.utils.type_utils import convert_into_iterable


class GamePlan:
    def __init__(self, steps: Union[Step, List[Step]]):
        self.steps = convert_into_iterable(steps)

    def setup(self, common: Common):
        for step in self.steps:
            step.setup(common)

    @abstractmethod
    def execute(self):
        for step in self.steps:
            step.execute()
