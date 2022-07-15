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
    WORKER_MOVEMENT_DELAY = 1
    CIRCLE_STEPS = 12
    CIRCLE_RADIUS = 11

    def __init__(self):
        super().__init__()
        self.circle_points: list[Point2] = self.create_circle_points(self.CIRCLE_STEPS)
        self.next_action_time = 0
        self.worker_tag: Optional[int] = None
        self.state: WorkerScoutState = WorkerScoutState.INITIAL
        self.states: dict[WorkerScoutState, ()] = {
            WorkerScoutState.INITIAL: self.start_scouting,
            WorkerScoutState.SCOUTING_MAIN: self.scouting_main,
            WorkerScoutState.SCOUTING_EXPANSIONS: self.scouting_expansions,
            WorkerScoutState.MOVING_BACK: self.moving_back,
            WorkerScoutState.DONE: self.do_nothing,
        }
        self.circle_step = 0

    def setup(self, common: Common):
        self.common = common

    def execute(self):
        self.states[self.state]()

    def start_scouting(self):
        self.worker_tag = self.common.workers.filter(
            lambda worker: self.common.job_of_unit(worker) in [Job.MIMMINER] and not worker.is_carrying_resource
        ).closest_to(self.common.enemymain).tag
        self.common.set_job_of_unittag(self.worker_tag, Job.SCOUT)
        self.state = WorkerScoutState.SCOUTING_MAIN

    def get_worker(self) -> Optional[Unit]:
        worker = self.common.units.by_tag(self.worker_tag)
        if not worker:
            self.state = WorkerScoutState.DONE
            return None
        return self.common.units.by_tag(self.worker_tag)

    def scouting_main(self):
        worker = self.get_worker()
        if worker:
            if len(worker.orders) < 2:
                point = (Point2((self.common.enemymain.x + self.CIRCLE_RADIUS * self.circle_points[self.circle_step].x,
                                 self.common.enemymain.y + self.CIRCLE_RADIUS * self.circle_points[self.circle_step].y)))
                self.next_action_time = self.common.time + self.WORKER_MOVEMENT_DELAY
                self.circle_step = (self.circle_step + 1) % self.CIRCLE_STEPS
                worker.move(point, queue=True)
            if self.common.time > 90 or not self.common.enemy_structures.of_type(
                    UnitTypeId.BARRACKS).ready.empty or not self.common.enemy_structures.of_type(
                    UnitTypeId.WARPGATE).ready.empty or not self.common.enemy_structures.of_type(UnitTypeId.SPAWNINGPOOL).ready.empty:
                self.state = WorkerScoutState.SCOUTING_EXPANSIONS

    def scouting_expansions(self):
        worker = self.get_worker()
        if worker:
            logger.info("SCOUTING EXPANSION")
            closest = closest_n(self.common.expansion_locations_list, self.common.enemymain, 2)
            logger.info(f"{self.common.enemymain} -> {closest[0]} | {closest[1]}")
            worker.move(closest[0])
            worker.move(closest[1], True)
            self.state = WorkerScoutState.MOVING_BACK

    def moving_back(self):
        worker = self.get_worker()
        if worker:
            logger.info(len(worker.orders))
            if worker.is_idle:
                logger.info("MOVE BACK")
                self.common.set_job_of_unittag(self.worker_tag, Job.UNCLEAR)
                self.state = WorkerScoutState.DONE

    def do_nothing(self):
        pass

    @staticmethod
    def create_circle_points(points: int) -> list[Point2]:
        circle_points = []
        for i in range(0, points):
            alfa = 2 * math.pi * i / points
            point = Point2((math.cos(alfa), math.sin(alfa)))
            circle_points.append(point)
        return circle_points