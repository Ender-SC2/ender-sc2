from ender.unit import MoveCommand
from ender.utils.command_utils import CommandUtils
from ender.utils.point_utils import distance
from ender.utils.unit_utils import range_vs
from sc2.units import Units


# move this unit forward a bit.
# on having less range


class LessRangeBehavior(CommandUtils):
    async def on_step_units(self, units: Units):
        for unit in units:
            if unit.weapon_cooldown > self.bot_ai.client.game_step:
                enemies = self.bot_ai.enemy_units.filter(
                    lambda enemy: distance(enemy.position, unit.position) <= range_vs(enemy, unit)
                )  # enemy can shoot
                if len(enemies) > 0:
                    target = enemies.closest_to(unit)
                    if range_vs(unit, target) < range_vs(target, unit) - 0.5:  # I have less range
                        touchdist = unit.radius + target.radius
                        if touchdist > 0:
                            step = min(1.0, touchdist)
                            goal = unit.position.towards(target.position, step)
                            self.unit_interface.set_command(unit, MoveCommand(goal, "LessRange"))
