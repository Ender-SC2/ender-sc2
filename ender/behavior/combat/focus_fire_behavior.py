# focus_fire_combat_behavior.py

from typing import List, Optional

from ender.job import Job
from ender.unit import AttackCommand
from ender.utils.command_utils import CommandUtils
from ender.utils.point_utils import distance
from ender.utils.unit_utils import range_vs
from sc2.ids.unit_typeid import UnitTypeId

from sc2.unit import Unit
from sc2.units import Units


# TODO: Consider enemies with high DPS or AoE
# TODO: Consider enemies that take more damage from unit
class FocusFireCombatBehavior(CommandUtils):
    UNIT_PRIORITY = {
        UnitTypeId.SIEGETANK: 5.0,
        UnitTypeId.SIEGETANKSIEGED: 5.0,
        UnitTypeId.MEDIVAC: 3.0,
        UnitTypeId.COLOSSUS: 5.0,
        UnitTypeId.WARPPRISM: 3.0,
        UnitTypeId.BANELING: 5.0,
        UnitTypeId.LURKERMP: 5.0,
        UnitTypeId.LURKERMPBURROWED: 5.0,
    }
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]
    enemy_health = {}  # permanent, for roach damage is delayed
    last_shot = {}  # enemies being shot; the frame the last shot started. Also, own units starting to shoot.

    async def on_step_units(self, units: Units):
        game_loop = self.bot_ai.state.game_loop
        for enemy in self.bot_ai.enemy_units:
            tag = enemy.tag
            if tag not in self.enemy_health:
                self.enemy_health[tag] = enemy.shield + enemy.health
            if tag not in self.last_shot:
                self.last_shot[tag] = -99999
            if game_loop >= self.last_shot[tag] + 10:
                # attach enemy_health to game value
                self.enemy_health[tag] = enemy.shield + enemy.health
        for unit in units:
            tag = unit.tag
            if tag not in self.last_shot:
                self.last_shot[tag] = -99999
            if game_loop >= self.last_shot[tag] + self.bot_ai.client.game_step * 2:
                if unit.weapon_cooldown < self.bot_ai.client.game_step:  # I can shoot (before next programrun)
                    enemies_around = self.bot_ai.enemy_units.filter(
                        lambda enemy: enemy.can_be_attacked
                        and (
                            distance(self.next_position(unit), self.next_position(enemy))
                            < range_vs(unit, enemy) + unit.radius + enemy.radius
                        )
                        and (self.enemy_health[enemy.tag] > -5)
                    )
                    if not enemies_around.empty:
                        target = enemies_around.sorted(lambda u: self.unit_priority(u, self.enemy_health[u.tag])).first
                        self.unit_priority(target, self.enemy_health[target.tag])
                        self.unit_interface.set_command(unit, AttackCommand(target, "FocusFire"))
                        self.last_shot[target.tag] = game_loop
                        self.last_shot[tag] = game_loop
                        self.enemy_health[target.tag] -= unit.calculate_damage_vs_target(target)[0]
        self.save_position()

    def unit_priority(self, unit: Unit, expected_health: int):
        priority = 1.0
        if unit.type_id in self.UNIT_PRIORITY:
            priority = self.UNIT_PRIORITY[unit.type_id]
        result = expected_health / (unit.health_max + unit.shield_max) / priority
        return result
