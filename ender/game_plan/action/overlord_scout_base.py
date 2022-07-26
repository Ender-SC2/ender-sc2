from enum import auto, Enum
from typing import Optional

from loguru import logger

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.job import Job
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class ScoutState(Enum):
    INITIAL = auto()
    SCOUT = auto()
    DONE = auto()


class OverlordScoutBase(IAction):
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

    def setup(self, common: Common):
        self.common = common

    """
    Completed once scouted
    """

    def execute(self) -> bool:
        self.behaviors[self.state]()
        return self.state == ScoutState.DONE

    def start(self):
        overlord = self.common.units.of_type(UnitTypeId.OVERLORD).closest_to(self.position)
        self.overlord_tag = overlord.tag
        self.common.set_job_of_unittag(self.overlord_tag, Job.SACRIFICIAL_SCOUT)
        self.state = ScoutState.SCOUT
        overlord.move(self.position, False)
        logger.info(f"Scouting {self.position}")
        pass

    def scout(self):
        overlord = self.get_scout()
        if overlord and overlord.is_idle:
            logger.info(f"Scouting {self.position} complete")
            self.state = ScoutState.DONE
            self.common.set_job_of_unit(overlord, Job.UNCLEAR)

    def do_nothing(self):
        pass

    def get_scout(self) -> Optional[Unit]:
        scout = self.common.units.find_by_tag(self.overlord_tag)
        if not scout:
            logger.info(f"Scout {self.position} killed")
            self.state = ScoutState.DONE
            return None
        return scout
