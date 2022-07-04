# upgraded.py

from typing import List, Optional
from loguru import logger

from ender.job import Job
from ender.utils.command_utils import CommandUtils
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.ids.ability_id import AbilityId
from ender.utils.unit_utils import range_vs


class Upgraded(CommandUtils):
    unit_types: Optional[List[UnitTypeId]]
    jobs: Optional[List[Job]]
    upgrades = 0

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types = unit_types
        self.jobs = jobs

    async def on_step(self, iteration: int):
        self.frame = iteration * self.bot_ai.client.game_step
        if self.upgrades == 0:
            self.upgrades += 1
            await self.bot_ai.client.debug_upgrade()
