from typing import Optional

from loguru import logger

from ender.game_plan.action.positioning import Positioning
from sc2.position import Point2


class MineralLinePositioning(Positioning):

    def position(self, close_to: Optional[Point2]) -> Optional[Point2]:
        if not close_to:
            raise Exception("Mineral line positioning needs a reference")
        logger.info(f"Looking for mineral position {close_to}")
        minerals = self.common.mineral_field.closer_than(11, close_to)
        minerals.append(self.common.vespene_geyser.closer_than(11, close_to))
        if minerals.empty:
            logger.info(f"No mineral close to {close_to}")
        else:
            return close_to.towards(self.common.mineral_field.closer_than(11, close_to).center, 6)
        return None
