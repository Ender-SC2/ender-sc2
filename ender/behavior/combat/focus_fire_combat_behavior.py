# focus_fire_combat_behavior.py

from typing import List, Optional

from ender.job import Job
from ender.unit import AttackCommand
from ender.utils.command_utils import CommandUtils
from ender.utils.point_utils import distance
from ender.utils.unit_utils import range_vs
from sc2.ids.unit_typeid import UnitTypeId


# TODO: Consider enemies with high DPS or AoE
# TODO: Consider enemies that take more damage from unit
class FocusFireCombatBehavior(CommandUtils):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]
    enemy_health = {}  # permanent, for roach damage is delayed
    shot = {}  # enemies being shot; the frame the last shot started. Also, own units starting to shoot.

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step(self, iteration: int):
        self.frame = iteration * self.bot_ai.client.game_step
        myunits = self.bot_ai.units.filter(
            lambda unit: (not self.jobs or self.unit_interface.job_of_unit(unit) in self.jobs)
            and (not self.unit_types or unit.type_id in self.unit_types)
        )
        for enemy in self.bot_ai.enemy_units:
            tag = enemy.tag
            if tag not in self.enemy_health:
                self.enemy_health[tag] = enemy.shield + enemy.health
            if tag not in self.shot:
                self.shot[tag] = -99999
            if self.frame >= self.shot[tag] + 15:
                # attach enemy_health to game value
                self.enemy_health[tag] = enemy.shield + enemy.health
        for unit in myunits:
            tag = unit.tag
            if tag not in self.shot:
                self.shot[tag] = -99999
            if self.frame >= self.shot[tag] + 5:  # the last shoot command should have arrived
                if unit.weapon_cooldown < self.bot_ai.client.game_step:  # I can shoot (before next programrun)
                    enemies_around = self.bot_ai.enemy_units.filter(
                        lambda enemy: (
                            distance(self.next_position(unit), self.next_position(enemy))
                            < range_vs(unit, enemy) + unit.radius + enemy.radius
                        )
                        and (self.enemy_health[enemy.tag] > -5)
                    )
                    if not enemies_around.empty:
                        target = enemies_around.sorted(lambda u: self.enemy_health[u.tag]).first
                        self.unit_interface.set_command(unit, AttackCommand(target, "FocusFire"))
                        self.shot[target.tag] = self.frame
                        self.shot[tag] = self.frame
                        self.enemy_health[target.tag] = (
                            self.enemy_health[target.tag] - unit.calculate_damage_vs_target(target)[0]
                        )
        self.save_position()
