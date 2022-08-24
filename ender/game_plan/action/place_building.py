from typing import Optional

from loguru import logger

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.game_plan.action.positioning import Positioning
from ender.game_plan.action.random_positioning import RandomPositioning
from ender.production.emergency import EmergencyStructure
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class PlaceBuilding(IAction):
    common: Common
    REQUEST_TIMEOUT = 30

    def __init__(
        self,
        unit_type: UnitTypeId,
        positioning: Positioning = RandomPositioning(),
        amount: int = 1,
        on_base: Point2 = None,
    ):
        super().__init__()
        self.request_time = 0
        self.unit_type = unit_type
        self.positioning = positioning
        self.amount = amount
        self.on_base = on_base

    def setup(self, common: Common):
        self.common = common
        self.positioning.setup(common)

    def execute(self):
        if self.has_building():
            return True
        if self.request_time + self.REQUEST_TIMEOUT > self.common.time:
            return False
        position = self.get_position()
        if position:
            logger.info(f"Asking for {self.unit_type} on {self.get_position()}")
            self.common.emergency.emergency_queue[id(self)] = EmergencyStructure(self.unit_type, self.get_position())
        self.request_time = self.common.time
        return False

    def has_building(self):
        if not self.on_base:
            return self.common.structures.of_type(self.unit_type).amount >= self.amount
        return self.common.structures.of_type(self.unit_type).closer_than(11, self.on_base).amount >= self.amount

    def get_position(self) -> Optional[Point2]:
        return self.positioning.position(self.on_base)
