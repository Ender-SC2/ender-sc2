from typing import List, Optional

from ender.job import Job
from ender.unit import AttackCommand
from ender.utils.command_utils import CommandUtils
from sc2.ids.unit_typeid import UnitTypeId


class AttackCenterBehavior(CommandUtils):

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types: Optional[List[UnitTypeId]] = unit_types
        self.jobs: Optional[List[Job]] = jobs

    async def on_step(self, iteration: int):
        my_units = self.bot_ai.units.filter(
            lambda unit: (not self.jobs or self.unit_interface.job_of_unit(unit) in self.jobs) and (
                    not self.unit_types or unit.type_id in self.unit_types))
        goal = self.bot_ai.game_info.map_center
        for unit in my_units.filter(lambda unit: unit.is_idle):
            self.unit_interface.set_command(unit, AttackCommand(goal, 'AttackCenter'))
