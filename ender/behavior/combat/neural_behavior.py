# neural_behavior.py
from ender.unit.ability_command import AbilityCommand
from ender.utils.command_utils import CommandUtils
from ender.utils.point_utils import distance
from sc2.ids.ability_id import AbilityId
from sc2.units import Units


class NeuralBehavior(CommandUtils):

    async def on_step_units(self, units: Units):
        if not self.bot_ai.enemy_units.empty:
            for unit in units:
                if unit.energy >= 100:
                    # neural enemy with highest energy
                    besteng = -1
                    target = None
                    for ene in self.bot_ai.enemy_units:
                        if distance(unit.position, ene.position) < 8:
                            if ene.energy > besteng:
                                besteng = ene.energy
                                target = ene
                    if target:
                        self.unit_interface.set_command(unit, AbilityCommand(AbilityId.NEURALPARASITE_NEURALPARASITE, target, "MoreRange"))
