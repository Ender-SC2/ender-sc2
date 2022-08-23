from ender.unit import MoveCommand
from ender.utils.command_utils import CommandUtils
from ender.utils.point_utils import distance
from ender.utils.unit_utils import range_vs
from sc2.units import Units


# move this unit forward a bit if the opponent cannot attack


class UprampBehavior(CommandUtils):
    async def on_step_units(self, units: Units):
        for unit in units:
            enemies = self.bot_ai.enemy_units.filter(lambda ene: distance(ene.position, unit.position) < 10)
            if len(enemies) > 0:
                if unit.weapon_cooldown > self.bot_ai.client.game_step:  # i shot
                    target = enemies.closest_to(unit)
                    rangedist = 99999
                    for ene in enemies:
                        rd = distance(unit.position, ene.position) - range_vs(ene, unit)
                        rangedist = min(rd, rangedist)
                    if rangedist > 0:  # they cant shoot me
                        touchdist = distance(unit.position, target.position) - (unit.radius + target.radius)
                        step = min(touchdist, rangedist)
                        step = min(1, step)
                        goal = unit.position.towards(target.position, step)
                        self.unit_interface.set_command(unit, MoveCommand(goal, "Upramp"))
