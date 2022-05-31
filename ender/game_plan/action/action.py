from abc import abstractmethod

from ender.common import Common


class Action:

    @abstractmethod
    def setup(self, common: Common):
        pass

    @abstractmethod
    async def execute(self):
        pass
