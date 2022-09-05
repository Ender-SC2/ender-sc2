import math
from enum import auto, Enum
from typing import Optional

from loguru import logger

from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.job import Job
from ender.utils.point_utils import closest_n
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class WorkerScoutState(Enum):
    INITIAL = auto()
    SCOUTING_MAIN = auto()
    SCOUTING_EXPANSIONS = auto()
    MOVING_BACK = auto()
    DONE = auto()


class WorkerScoutAction(IAction):
    common: Common
    CIRCLE_STEPS = 12
    CIRCLE_RADIUS = 9
    SCOUT_TIME_LIMIT = 105

    def __init__(self):
        super().__init__()
        self.circle_points: list[Point2] = self.create_circle_points(self.CIRCLE_STEPS)
        self.worker_tag: Optional[int] = None
        self.state: WorkerScoutState = WorkerScoutState.INITIAL
        self.circle_step = 0

    def setup(self, common: Common):
        self.common = common

    def execute(self):
        if self.state == WorkerScoutState.INITIAL:
            self.start_scouting()
        elif self.state == WorkerScoutState.SCOUTING_MAIN:
            self.scouting_main()
        elif self.state == WorkerScoutState.SCOUTING_EXPANSIONS:
            self.scouting_expansions()
        elif self.state == WorkerScoutState.MOVING_BACK:
            self.moving_back()
        return self.state == WorkerScoutState.DONE

    def start_scouting(self):
        worker = self.common.workers.filter(
            lambda worker: self.common.job_of_unit(worker) in [Job.MIMMINER] and not worker.is_carrying_resource
        ).closest_to(self.common.enemymain)
        self.worker_tag = worker.tag
        self.common.set_job_of_unittag(worker.tag, Job.SCOUT)
        self.state = WorkerScoutState.SCOUTING_MAIN
        worker.move(self.next_point())

    def get_worker(self) -> Optional[Unit]:
        if not self.worker_tag:
            return None
        worker = self.common.units.find_by_tag(self.worker_tag)
        if not worker:
            self.state = WorkerScoutState.DONE
            return None
        return worker

    def scouting_main(self):
        worker = self.get_worker()
        if worker:
            if len(worker.orders) < 3:
                point = Point2(
                    (
                        self.common.enemymain[0] + self.CIRCLE_RADIUS * self.circle_points[self.circle_step][0],
                        self.common.enemymain[1] + self.CIRCLE_RADIUS * self.circle_points[self.circle_step][1],
                    )
                )
                self.circle_step = (self.circle_step + 1) % self.CIRCLE_STEPS
                worker.move(point, queue=True)
            if (
                self.common.time > self.SCOUT_TIME_LIMIT
                or not self.common.enemy_structures.of_type(UnitTypeId.BARRACKS).ready.empty
                or not self.common.enemy_structures.of_type(UnitTypeId.WARPGATE).ready.empty
                or not self.common.enemy_structures.of_type(UnitTypeId.SPAWNINGPOOL).ready.empty
            ):
                self.state = WorkerScoutState.SCOUTING_EXPANSIONS

    def scouting_expansions(self):
        worker = self.get_worker()
        if worker:
            logger.info("SCOUTING EXPANSION")
            closest = closest_n(self.common.expansion_locations_list, self.common.enemymain, 2)
            logger.info(f"{self.common.enemymain} -> {closest[0]} | {closest[1]}")
            worker.move(closest[0])
            worker.move(closest[1], True)
            worker.move(self.common.ourmain, True)
            self.state = WorkerScoutState.MOVING_BACK

    def moving_back(self):
        worker = self.get_worker()
        if worker:
            if worker.is_idle:
                self.common.set_job_of_unittag(worker.tag, Job.UNCLEAR)
                self.state = WorkerScoutState.DONE

    @staticmethod
    def create_circle_points(points: int) -> list[Point2]:
        circle_points = []
        for i in range(0, points):
            alfa = 2 * math.pi * i / points
            point = Point2((math.cos(alfa), math.sin(alfa)))
            circle_points.append(point)
        return circle_points

    def next_point(self) -> Point2:
        point = Point2(
            (
                self.common.enemymain[0] + self.CIRCLE_RADIUS * self.circle_points[self.circle_step][0],
                self.common.enemymain[1] + self.CIRCLE_RADIUS * self.circle_points[self.circle_step][1],
            )
        )

        self.circle_step = (self.circle_step + 1) % self.CIRCLE_STEPS
        return point
