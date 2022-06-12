from typing import List, Optional

from ender.behavior.behavior import IBehavior
from ender.job import Job
from ender.unit import AttackCommand
from sc2.ids.unit_typeid import UnitTypeId


class FocusFireCombatBehavior(IBehavior):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step(self):
        enemy_health = {}
        for enemy in self.bot_ai.enemy_units:
            enemy_health[enemy.tag] = enemy.shield + enemy.health
        for unit in self.bot_ai.units:
            if unit.weapon_cooldown <= self.bot_ai.client.game_step:
                if (not self.jobs or self.unit_interface.get_unit_job(unit) in self.jobs) and (
                        not self.unit_types or unit.type_id in self.unit_types):
                    enemies_around = self.bot_ai.enemy_units.filter(
                        lambda enemy: unit.target_in_range(enemy, 0.2) and enemy_health[enemy.tag] > 0)
                    if not enemies_around.empty:
                        best_target = enemies_around.sorted(lambda u: u.shield_health_percentage).first
                        self.unit_interface.set_command(unit, AttackCommand(best_target))
                        enemy_health[best_target.tag] = enemy_health[best_target.tag] - \
                                                        unit.calculate_damage_vs_target(best_target)[0]
