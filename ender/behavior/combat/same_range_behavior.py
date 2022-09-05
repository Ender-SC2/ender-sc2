from ender.unit import MoveCommand
from ender.utils.command_utils import CommandUtils
from ender.utils.point_utils import towards
from ender.utils.unit_utils import range_vs
from sc2.units import Units


class SameRangeBehavior(CommandUtils):
    maxcool = {}

    # move back a bit as soon as you shot.
    # cannot queue for the attack does not end after 1 shot.

    async def on_step_units(self, units: Units):
        if not self.bot_ai.enemy_units.empty:
            for unit in units:
                tag = unit.tag
                if tag not in self.maxcool:
                    self.maxcool[tag] = 2
                if unit.weapon_cooldown > self.maxcool[tag]:
                    self.maxcool[tag] = unit.weapon_cooldown
                target = self.bot_ai.enemy_units.closest_to(unit)
                if abs(range_vs(target, unit) - range_vs(unit, target)) < 0.5:  # equal range
                    if unit.weapon_cooldown >= self.maxcool[tag] / 2:
                        goal = towards(unit.position, target.position, -1)
                        self.unit_interface.set_command(unit, MoveCommand(goal, "back"))
