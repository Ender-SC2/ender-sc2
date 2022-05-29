from typing import Optional

from ender.game_plan.action.positioning import Positioning
from sc2.position import Point2


class MineralLinePositioning(Positioning):

    def placement(self, close_to: Point2, distance: Optional[int] = None) -> Point2:
        return close_to.towards(self.common.mineral_field.closer_than(11, close_to).center, distance)

