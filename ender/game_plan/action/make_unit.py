from loguru import logger

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.production.emergency import EmergencyUnit
from sc2.ids.unit_typeid import UnitTypeId


class MakeUnit(IAction):
    common: Common

    def __init__(self, reference_unit: UnitTypeId, unit_type: UnitTypeId, ratio: float = 1):
        super().__init__()
        self.request_time = 0
        self.reference_unit = reference_unit
        self.unit_type = unit_type
        self.ratio = ratio

    def setup(self, common: Common):
        self.common = common

    def execute(self):
        wanted_amount = self.wanted_amount()
        if wanted_amount <= self.count_units():
            return False
        logger.info(f"Asking for {self.unit_type}:{wanted_amount}")
        self.common.emergency.emergency_queue[id(self)] = EmergencyUnit(self.unit_type, wanted_amount)
        self.request_time = self.common.time
        return False

    def wanted_amount(self) -> int:
        return int(len(self.common.enemy_units.of_type(self.reference_unit)) * self.ratio)

    def count_units(self) -> int:
        return len(self.common.units.of_type(self.unit_type))
