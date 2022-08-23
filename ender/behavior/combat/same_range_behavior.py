# back_behavior.py

from typing import List, Optional

from ender.job import Job
from ender.unit import MoveCommand
from ender.utils.command_utils import CommandUtils
from ender.utils.unit_utils import range_vs
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class SameRangeBehavior(CommandUtils):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]
    maxcool = {}

    # move back a bit as soon as you shot.
    # cannot queue for the attack does not end after 1 shot.

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step_units(self, units: Units):
        if not self.bot_ai.enemy_units.empty:
            for unit in units:
                tag = unit.tag
                if tag not in self.maxcool:
                    self.maxcool[tag] = 2
                if unit.weapon_cooldown > self.maxcool[tag]:
                    self.maxcool[tag] = unit.weapon_cooldown
                target = self.bot_ai.enemy_units.closest_to(unit)
                if abs(range_vs(target, unit) - range_vs(unit, target)) < 0.5:  # equal range
                    if unit.weapon_cooldown >= self.maxcool[tag] / 2:
                        goal = unit.position.towards(target.position, -1)
                        self.unit_interface.set_command(unit, MoveCommand(goal, "back"))
