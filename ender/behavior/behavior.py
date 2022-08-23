from abc import abstractmethod, ABC
from typing import Optional, List

from ender.job import Job
from ender.unit.unit_interface import IUnitInterface
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


# TODO: Unify behavior with action
class IBehavior(ABC):
    bot_ai: BotAI
    unit_interface: IUnitInterface

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types: Optional[List[UnitTypeId]] = unit_types
        self.jobs: Optional[List[Job]] = jobs

    # TODO: Move unit behavior from common to UnitInterface
    def setup(self, bot_ai: BotAI, unit_interface: IUnitInterface):
        self.bot_ai = bot_ai
        self.unit_interface = unit_interface

    @abstractmethod
    async def on_step_units(self, units: Units):
        raise NotImplementedError()

    async def on_step(self, iteration: int):
        my_units = self.bot_ai.units.filter(
            lambda unit: (not self.jobs or self.unit_interface.job_of_unit(unit) in self.jobs)
            and (not self.unit_types or unit.type_id in self.unit_types)
        )
        await self.on_step_units(my_units)
