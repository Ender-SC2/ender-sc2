from typing import Optional

from ender.game_plan.action.positioning import Positioning
from sc2.position import Point2


class BasePositioning(Positioning):
    def position(self, close_to: Optional[Point2]) -> Optional[Point2]:
        if close_to:
            return self.common.townhalls.closest_to(close_to).position
        return self.common.ourmain
