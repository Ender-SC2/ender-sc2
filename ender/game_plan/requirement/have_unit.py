from ender.common import Common
from ender.game_plan.requirement.requirement import Requirement
from sc2.ids.unit_typeid import UnitTypeId


class HaveUnit(Requirement):
    def __init__(self, unit_type: UnitTypeId, amount: int = 1, position: Optional[Point2] = None, distance: float = 11):
        self.common = None
        self.unit_type = unit_type
        self.amount = amount
        self.position = position
        self.distance = distance

    def setup(self, common: Common):
        super().setup(common)
        self.common = common

    def check(self) -> bool:
        units = self.common.units.of_type(self.unit_type)
        if self.position:
            units = units.closer_than(self.distance, self.position)
        return units.amount >= self.amount