from abc import abstractmethod, ABC

from ender.common import Common
from ender.unit.unit_interface import IUnitInterface
from sc2.bot_ai import BotAI


# TODO: Unify behavior with action
class IBehavior(ABC):
    bot_ai: BotAI
    unit_interface: IUnitInterface

    # TODO: Move unit behavior from common to UnitInterface
    def setup(self, bot_ai: BotAI, unit_interface: IUnitInterface):
        self.bot_ai = bot_ai
        self.unit_interface = unit_interface

    @abstractmethod
    async def on_step(self):
        raise NotImplementedError
