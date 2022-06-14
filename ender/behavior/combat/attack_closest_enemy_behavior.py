from typing import List, Optional

from ender.behavior.behavior import IBehavior
from ender.job import Job
from ender.unit import AttackCommand
from sc2.ids.unit_typeid import UnitTypeId


class AttackClosestEnemyBehavior(IBehavior):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step(self):
        if not self.bot_ai.enemy_units.empty:
            for unit in self.bot_ai.units:
                if (not self.jobs or self.unit_interface.job_of_unit(unit) in self.jobs) and (
                        not self.unit_types or unit.type_id in self.unit_types):
                    goal = self.bot_ai.enemy_units.closest_to(unit)
                    self.unit_interface.set_command(unit, AttackCommand(goal.position))
