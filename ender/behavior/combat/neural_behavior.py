# neural_behavior.py

from typing import List, Optional
from loguru import logger

from ender.job import Job
from ender.utils.command_utils import CommandUtils
from ender.utils.point_utils import distance
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.ids.ability_id import AbilityId
from ender.utils.unit_utils import range_vs


class NeuralBehavior(CommandUtils):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step(self, iteration: int):
        self.frame = iteration * self.bot_ai.client.game_step
        myunits = self.bot_ai.units.filter(
            lambda unit: (not self.jobs or self.unit_interface.job_of_unit(unit) in self.jobs) and (
                not self.unit_types or unit.type_id in self.unit_types)
            )
        logger.info('-------- ' + str(self.frame))
        for unt in self.bot_ai.units:
            logger.info('my unit ' + str(unt.tag) + ' eng ' + str(unt.energy))
        if not self.bot_ai.enemy_units.empty:
            for unit in myunits:
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
                        unit(AbilityId.NEURALPARASITE_NEURALPARASITE, target)

