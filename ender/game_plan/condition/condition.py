from abc import abstractmethod

from sc2.bot_ai import BotAI


class ICondition:

    @abstractmethod
    def setup(self, bot_ai: BotAI):
        pass

    @abstractmethod
    def check(self) -> bool:
        pass
