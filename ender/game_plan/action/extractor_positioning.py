from typing import Optional

from ender.game_plan.action.positioning import Positioning
from sc2.position import Point2


class ExtractorPositioning(Positioning):
    def position(self, close_to: Optional[Point2]) -> Optional[Point2]:
        geysers = self.common.vespene_geyser.filter(
            lambda geyser: any(geyser.distance_to(base) <= 12 for base in self.common.townhalls.ready)
            and not any(geyser.position == structure.position for structure in self.common.structures)
        )
        if close_to:
            return geysers.closest_to(close_to).position
        return geysers.closest_to(self.common.start_location).position
