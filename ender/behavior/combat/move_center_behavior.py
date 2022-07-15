from typing import List, Optional

from loguru import logger
from math import sqrt

from ender.utils.command_utils import CommandUtils
from ender.job import Job
from ender.unit import AttackCommand
from ender.utils.point_utils import distance
from sc2.ids.unit_typeid import UnitTypeId


class MoveCenterBehavior(CommandUtils):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]
    # should not interfere with sidewards_behaviour etc.
    # so command only after idling during a second.
    # also at the beginning, move center anyway.
    busy = {}  # When not idling: current frame. When idling: last frame not idling

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step(self, iteration: int):
        self.frame = iteration * self.bot_ai.client.game_step
        myunits = self.bot_ai.units.filter(
            lambda unit: (not self.jobs or self.unit_interface.job_of_unit(unit) in self.jobs)
            and (not self.unit_types or unit.type_id in self.unit_types)
        )
        goal = self.bot_ai.game_info.map_center
        for unit in myunits:
            tag = unit.tag
            if tag not in self.busy:
                self.busy[tag] = 0
            if len(unit.orders) > 0:
                self.busy[tag] = self.frame
            if self.frame >= self.busy[tag] + 20:
                if distance(unit.position, goal) > sqrt(len(myunits)):
                    self.nospam_pos("center", unit, "A", goal)
            if self.frame < 20:  # begin of testgame
                self.nospam_pos("center", unit, "A", goal)
