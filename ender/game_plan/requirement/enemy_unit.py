from ender.common import Common
from ender.game_plan.requirement.requirement import Requirement
from sc2.ids.unit_typeid import UnitTypeId


class EnemyUnit(Requirement):
    def __init__(self, unit_type: UnitTypeId, amount: int = 1):
        self.common = None
        self.unit_type = unit_type
        self.amount = amount

    def setup(self, common: Common):
        super().setup(common)
        self.common = common

    def check(self) -> bool:
        enemy_units = self.common.enemy_units.of_type(self.unit_type)

        return enemy_units.amount >= self.amount
