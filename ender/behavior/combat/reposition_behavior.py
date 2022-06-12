from typing import List, Optional

from ender.behavior import IBehavior
from ender.job import Job
from ender.unit.move_command import MoveCommand
from ender.utils.unit_utils import range_vs
from sc2.ids.unit_typeid import UnitTypeId


class RepositionBehavior(IBehavior):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step(self):
        for unit in self.bot_ai.units:
            if unit.weapon_cooldown > self.bot_ai.client.game_step:
                if (not self.jobs or self.unit_interface.get_unit_job(unit) in self.jobs) and (
                        not self.unit_types or unit.type_id in self.unit_types):
                    enemies_around = self.bot_ai.enemy_units.filter(
                        lambda enemy: unit.target_in_range(enemy, unit.movement_speed))
                    if not enemies_around.empty:
                        closest_enemy = enemies_around.closest_to(unit)
                        if 0 < range_vs(closest_enemy, unit) < range_vs(unit, closest_enemy):
                            position = unit.position.towards(enemies_around.center, -unit.movement_speed)
                            self.unit_interface.set_command(unit, MoveCommand(position))
