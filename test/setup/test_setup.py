from abc import abstractmethod, ABC

from sc2.bot_ai import BotAI


class ITestSetup(ABC):

    @abstractmethod
    async def setup(self, bot_ai: BotAI):
        raise NotImplementedError()
