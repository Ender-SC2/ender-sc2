from typing import Optional

from ender.game_plan.action.positioning import Positioning
from sc2.position import Point2


class MineralLinePositioning(Positioning):

    def position(self, close_to: Optional[Point2]) -> Point2:
        if not close_to:
            raise Exception("Mineral line positioning needs a reference")
        print(f"Looking for mineral position {close_to}")
        print(f"Center is {self.common.mineral_field.closer_than(11, close_to).center}")
        return close_to.towards(self.common.mineral_field.closer_than(11, close_to).center, 6)
