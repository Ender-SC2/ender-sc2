from enum import auto, Enum
from typing import Optional

from loguru import logger

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.job import Job
from ender.utils.point_utils import center
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class ScoutState(Enum):
    INITIAL = auto()
    SCOUT = auto()
    DONE = auto()


class OverlordScoutBase(IAction):
    scout_points: list[Point2]
    original_point: Point2

    def __init__(self, position: Point2):
        self.overlord_tag = None
        self.common: Optional[Common] = None
        self.position = position
        self.state: ScoutState = ScoutState.INITIAL
        self.behaviors: dict[ScoutState, ()] = {
            ScoutState.INITIAL: self.start,
            ScoutState.SCOUT: self.scout,
            ScoutState.DONE: self.do_nothing,
        }
        self.scout_points = []

    def setup(self, common: Common):
        self.common = common

    """
    Completed once scouted
    """

    def execute(self) -> bool:
        self.behaviors[self.state]()
        return self.state == ScoutState.DONE

    def start(self):
        overlord = (
            self.common.units.of_type(UnitTypeId.OVERLORD)
            .filter(lambda unit: self.common.job_of_unit(unit) == Job.HANGER)
            .closest_to(self.position)
        )
        self.overlord_tag = overlord.tag
        self.common.set_job_of_unittag(self.overlord_tag, Job.SACRIFICIAL_SCOUT)
        self.state = ScoutState.SCOUT
        if overlord.is_idle:
            self.original_point = overlord.position
        else:
            self.original_point = overlord.order_target
        self.scout_points.append(self.position)
        for geyser in self.common.vespene_geyser:
            if geyser.distance_to(self.position) <= 12:
                self.scout_points.append(geyser.position)
        point_center = center(self.scout_points)
        overlord.move(point_center, False)
        logger.info(f"Scouting {self.position} -> {point_center}")

    def scout(self):
        overlord = self.get_scout()
        if overlord:
            for point in self.scout_points:
                if not self.common.is_visible(point):
                    return

            logger.info(f"Scouting {self.position} complete")
            overlord.move(self.original_point)
            self.state = ScoutState.DONE
            self.common.set_job_of_unit(overlord, Job.HANGER)

    def do_nothing(self):
        pass

    def get_scout(self) -> Optional[Unit]:
        scout = self.common.units.find_by_tag(self.overlord_tag)
        if not scout:
            logger.info(f"Scout {self.position} killed")
            self.state = ScoutState.DONE
            return None
        return scout
