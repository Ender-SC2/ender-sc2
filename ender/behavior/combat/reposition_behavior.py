from typing import List, Optional

from math import sqrt
from ender.job import Job
from ender.utils.unit_utils import range_vs
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from ender.utils.command_utils import CommandUtils

class RepositionBehavior(CommandUtils):
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
            if unit.weapon_cooldown > self.bot_ai.client.game_step: # I shot
                enemies_around = self.bot_ai.enemy_units.filter(
                    lambda enemy: unit.target_in_range(enemy, 6))
                if not enemies_around.empty:
                    closest_enemy = enemies_around.closest_to(unit)
                    if 0 < range_vs(closest_enemy, unit) < range_vs(unit, closest_enemy): # I have more range
                        if abs(range_vs(closest_enemy, unit) - range_vs(unit, closest_enemy)) >= 0.5: # unequal range
                            position = unit.position.towards(enemies_around.center, -1)
                            position = self.circling(position)
                            self.nospam_pos('reposition', unit, 'M', position)

    def circling(self, point: Point2) -> Point2:
        # for a point, return a point a bit further on the circle around mapcenter
        mid = self.bot_ai.game_info.map_center
        rad = point - mid
        perp = Point2((rad.y, -rad.x))
        norm = sqrt(perp.x*perp.x + perp.y*perp.y)
        if norm > 0:
            perp = perp / norm
        return point + perp
    
