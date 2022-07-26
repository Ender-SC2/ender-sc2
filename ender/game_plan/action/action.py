from abc import abstractmethod

from ender.common import Common


class IAction:
    @abstractmethod
    def setup(self, common: Common):
        pass

    @abstractmethod
    def execute(self) -> bool:
        pass
