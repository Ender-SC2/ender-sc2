from typing import Optional

from loguru import logger

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.game_plan.action.positioning import Positioning
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class PlaceBuilding(IAction):
    common: Common
    BUILDING_TIMEOUT = 30

    def __init__(
        self, unit_type: UnitTypeId, building_positioning: Positioning, amount: int = 1, on_base: Point2 = None
    ):
        super().__init__()
        self.request_time = 0
        self.unit_type = unit_type
        self.building_positioning = building_positioning
        self.amount = amount
        self.on_base = on_base

    def setup(self, common: Common):
        self.common = common
        self.building_positioning.setup(common)

    def execute(self):
        if self.has_building() or self.request_time + self.BUILDING_TIMEOUT > self.common.time:
            return
        logger.info(f"Asking for {self.unit_type} on {self.get_position()}")
        self.common.emergency.add((self.unit_type, self.get_position()))
        self.request_time = self.common.time

    def has_building(self):
        if not self.on_base:
            return self.common.all_units.of_type(self.unit_type).amount >= self.amount
        return self.common.all_units.of_type(self.unit_type).closer_than(11, self.on_base).amount >= self.amount

    def get_position(self) -> Optional[Point2]:
        return self.building_positioning.position(self.on_base)
