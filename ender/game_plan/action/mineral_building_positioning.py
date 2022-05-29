from typing import Optional

from ender.game_plan.action.building_positioning import BuildingPositioning
from sc2.position import Point2


class MineralBuildingPositioning(BuildingPositioning):

    def placement(self, close_to: Point2, distance: Optional[int] = None, limit: Optional[int] = None) -> Point2:
        return close_to.towards(self.common.mineral_field.closer_than(11, close_to).center, distance)

