from abc import ABC, abstractmethod

from ender.map.influence_map import InfluenceMap
from sc2.bot_ai import BotAI


class IMapInterface(ABC):

    @abstractmethod
    def unit_map(self) -> InfluenceMap:
        raise NotImplementedError()

    @abstractmethod
    def spell_map(self) -> InfluenceMap:
        raise NotImplementedError()


# WIP: This should keep all map information. We should only process maps once per loop
class MapInterface(IMapInterface):

    def setup(self, bot_ai: BotAI):
        self._bot_ai = bot_ai

    def spell_map(self) -> InfluenceMap:
        pass

    def unit_map(self) -> InfluenceMap:
        pass
