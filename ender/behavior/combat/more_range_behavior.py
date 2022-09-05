from math import sqrt

from ender.unit import MoveCommand
from ender.utils.command_utils import CommandUtils
from ender.utils.point_utils import towards
from ender.utils.unit_utils import range_vs
from sc2.position import Point2
from sc2.units import Units


class MoreRangeBehavior(CommandUtils):
    async def on_step_units(self, units: Units):
        for unit in units:
            if unit.weapon_cooldown > self.bot_ai.client.game_step:  # I shot
                enemies_around = self.bot_ai.enemy_units.filter(lambda enemy: unit.target_in_range(enemy, 6))
                if not enemies_around.empty:
                    closest_enemy = enemies_around.closest_to(unit)
                    if 0 < range_vs(closest_enemy, unit) < range_vs(unit, closest_enemy) - 0.5:  # I have more range
                        position = towards(unit.position, enemies_around.center, -1)
                        position = self.circling(position)
                        self.unit_interface.set_command(unit, MoveCommand(position, "MoreRange"))

    def circling(self, point: Point2) -> Point2:
        # for a point, return a point a bit further on the circle around mapcenter
        mid = self.bot_ai.game_info.map_center
        rad = point - mid
        perp = Point2((rad.y, -rad.x))
        norm = sqrt(perp.x * perp.x + perp.y * perp.y)
        if norm > 0:
            perp = perp / norm
        return point + perp
