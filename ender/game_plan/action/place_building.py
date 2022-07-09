from typing import Optional

from loguru import logger

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.game_plan.action.positioning import Positioning
from ender.job import Job
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class PlaceBuilding(IAction):
    common: Common

    def __init__(self, unit_type: UnitTypeId, building_positioning: Positioning, amount: int = 1,
                 on_base: Point2 = None):
        super().__init__()
        self.unit_type = unit_type
        self.building_positioning = building_positioning
        self.amount = amount
        self.on_base = on_base

    def setup(self, common: Common):
        self.common = common
        self.building_positioning.setup(common)

    def execute(self):
        if self.has_building():
            logger.info("Already have building")
            return
        if not self.common.can_afford(self.unit_type):
            logger.info("Can't afford")
            return
        position = self.get_position()
        if position:
            workers = self.common.workers.filter(
                lambda worker: self.common.job_of_unit(worker) in [Job.MIMMINER] and not worker.is_carrying_resource
            )
            logger.info(f"Placing {self.unit_type} at {position}")
            if not workers.empty:
                worker = workers.closest_to(position)
                self.common.set_job_of_unit(worker, Job.BUILDER)
                worker.build(self.unit_type, position)
            else:
                logger.info("Fail to find a worker")
        else:
            logger.info("Fail to find a good building position")

    def has_building(self):
        if not self.on_base:
            return self.common.all_units.of_type(self.unit_type).amount >= self.amount
        return self.common.all_units.of_type(self.unit_type).closer_than(11, self.on_base).amount >= self.amount

    def get_position(self) -> Optional[Point2]:
        logger.info(f"Getting position close to {self.on_base}")
        return self.building_positioning.position(self.on_base)
