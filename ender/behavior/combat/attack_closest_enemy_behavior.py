from ender.unit import AttackCommand
from ender.utils.command_utils import CommandUtils
from sc2.units import Units


class AttackClosestEnemyBehavior(CommandUtils):
    async def on_step_units(self, units: Units):
        if not self.bot_ai.enemy_units.empty:
            for unit in units:
                goal = self.bot_ai.enemy_units.closest_to(unit)
                self.unit_interface.set_command(unit, AttackCommand(goal, "AttackClosestEnemy"))
