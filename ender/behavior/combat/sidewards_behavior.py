# sidewards_behavior.py

from ender.unit import MoveCommand
from ender.utils.command_utils import CommandUtils
from ender.utils.point_utils import distance
from sc2.units import Units


class SidewardsBehavior(CommandUtils):
    back = 1.5
    last_health = 0
    hitframe = -99999

    async def on_step_units(self, units: Units):
        if len(units) >= 2:
            loop = self.bot_ai.state.game_loop
            mygrouppos = units.center
            enemies = self.bot_ai.enemy_units.filter(lambda ene: distance(ene.position, mygrouppos) < 15)
            if len(enemies) > 0:
                health = 0
                for unit in units:
                    health += unit.health
                if health < self.last_health:
                    self.hitframe = loop
                self.last_health = health
                sumdist = 0
                for unit in units:
                    oppo = enemies.closest_to(unit)
                    dist = distance(unit.position, oppo.position)
                    sumdist += dist
                avgdist = sumdist / len(units)
                if loop > self.hitframe + 25:  # I have not been hit
                    for unit in units:
                        if distance(unit.position, mygrouppos) > 1:
                            oppo = enemies.closest_to(unit)
                            spread = unit.position.towards(mygrouppos, -2)
                            position = self.next_position(oppo).towards(spread, avgdist + self.back)
                            self.unit_interface.set_command(unit, MoveCommand(position, "Sidewards"))
        self.back = min(-0.5, self.back - 0.02 * self.bot_ai.client.game_step)
        self.save_position()
