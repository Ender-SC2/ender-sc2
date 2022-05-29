from typing import Optional

from ender.common import Common
from ender.game_plan.action.action import Action
from ender.game_plan.action.building_positioning import BuildingPositioning
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class PlaceBuildingAction(Action):

    def __init__(self, unit_type: UnitTypeId, building_positioning: BuildingPositioning, amount: int = 1,
                 on_base: Point2 = None):
        self.common = None
        self.unit_type = unit_type
        self.building_positioning = building_positioning
        self.amount = amount
        self.on_base = on_base

    def setup(self, common: Common):
        self.common = common
        self.building_positioning.setup(common)

    def execute(self):
        if self.has_building():
            return
        position = self.get_position()
        unit = self.common.units.of_type(UnitTypeId.DRONE).idle.closest_to(position)
        if unit:
            unit.build()

    def has_building(self):
        if not self.on_base:
            return self.common.units.of_type(self.unit_type).amount >= self.amount
        return self.common.units.of_type(self.unit_type).closer_than(11, self.on_base).amount >= self.amount

    def get_position(self) -> Point2:
        return self.building_positioning.placement(self.on_base)
