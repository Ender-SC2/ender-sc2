from ender.unit import AttackCommand
from ender.utils.command_utils import CommandUtils
from sc2.units import Units


class AttackCenterBehavior(CommandUtils):
    async def on_step_units(self, units: Units):
        goal = self.bot_ai.game_info.map_center
        for unit in units.filter(lambda unit: unit.is_idle):
            self.unit_interface.set_command(unit, AttackCommand(goal, "AttackCenter"))
