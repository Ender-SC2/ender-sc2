from typing import List, Optional

from ender.unit import MoveCommand
from ender.utils.command_utils import CommandUtils
from ender.job import Job
from sc2.ids.unit_typeid import UnitTypeId
from ender.utils.unit_utils import range_vs

# move this unit forward a bit.
# on having less range
# also if the opponent cannot attack

class ForwardBehavior(CommandUtils):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step(self, iteration: int):
        self.frame = iteration * self.bot_ai.client.game_step
        myunits = self.bot_ai.units.filter(lambda unit:
            (not self.jobs or self.unit_interface.job_of_unit(unit) in self.jobs)
            and (not self.unit_types or unit.type_id in self.unit_types))

        for unit in myunits:
            enemies = self.bot_ai.enemy_units.filter (
                lambda ene: self.distance(ene.position, unit.position) < 8 )
            if len(enemies) > 0:
                if unit.weapon_cooldown > self.bot_ai.client.game_step:
                    target = enemies.closest_to(unit)
                    if 0 < range_vs(unit, target) < range_vs(target, unit): # I have less range
                        if abs(range_vs(unit, target) - range_vs(target, unit)) >= 0.5: # unequal range
                            touchdist = self.distance(unit.position, target.position) - (unit.radius + target.radius) 
                            if touchdist > 0:
                                step = min(1, touchdist)
                                goal = unit.position.towards(target.position, step)
                                self.unit_interface.set_command(unit, MoveCommand(goal, 'forward'))
                    else:
                        # dont block collegues while shooting a building
                        rangedist = 99999
                        for ene in enemies:
                            rd = self.distance(unit.position, ene.position) - range_vs(ene, unit)
                            rangedist = min(rd, rangedist)
                        if rangedist > 0:
                            touchdist = self.distance(unit.position, target.position) - (unit.radius + target.radius)
                            step = min(touchdist, rangedist) 
                            step = min(1, step)
                            goal = unit.position.towards(target.position, step)
                            self.unit_interface.set_command(unit, MoveCommand(goal, 'forward'))



