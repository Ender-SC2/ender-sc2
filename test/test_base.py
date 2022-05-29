from abc import abstractmethod

from ender.common import Common


class TestBase:

    @abstractmethod
    def setup(self, common: Common):
        pass

    @abstractmethod
    async def on_step(self):
        pass
