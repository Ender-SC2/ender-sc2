# sidewards_behavior.py

from typing import List, Optional

from ender.utils.command_utils import CommandUtils
from ender.job import Job
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class SidewardsBehavior(CommandUtils):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]
    back = 1.5
    last_health = 0
    hitframe = -99999

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step(self, iteration: int):
        self.frame = iteration * self.bot_ai.client.game_step
        myunits = self.bot_ai.units.filter(
            lambda unit: (not self.jobs or self.unit_interface.job_of_unit(unit) in self.jobs) and (
                not self.unit_types or unit.type_id in self.unit_types)
            )
        if len(myunits) >= 2:
            mygrouppos = myunits.center
            enemies = self.bot_ai.enemy_units.filter (
                lambda ene: self.distance(ene.position, mygrouppos) < 15 )
            if len(enemies) > 0:
                health = 0
                for unit in myunits:
                    health += unit.health
                if health < self.last_health:
                    self.hitframe = self.frame
                self.last_health = health
                sumdist = 0
                for unit in myunits:
                    oppo = enemies.closest_to(unit)
                    dist = self.distance(unit.position, oppo.position)
                    sumdist += dist
                avgdist = sumdist / len(myunits)
                if self.frame > self.hitframe + 25: # I have not been hit
                    for unit in myunits:
                        if self.distance(unit.position, mygrouppos) > 1:
                            oppo = enemies.closest_to(unit)
                            spread = unit.position.towards(mygrouppos, -2)
                            position = self.next_position(oppo).towards(spread, avgdist + self.back)
                            self.nospam_pos('sidewards', unit, 'M', position)
        self.back = min(-0.5, self.back - 0.02 * self.bot_ai.client.game_step)
        self.save_position()

