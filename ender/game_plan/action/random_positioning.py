from typing import Optional

from ender.game_plan.action.positioning import Positioning
from sc2.position import Point2, Pointlike


class RandomPositioning(Positioning):
    def position(self, close_to: Optional[Point2]) -> Optional[Pointlike]:
        if close_to:
            return self.common.townhalls.closest_to(close_to).position.towards(self.common.map_center, 7)
        return self.common.townhalls.random.position.towards(self.common.map_center, 7)
