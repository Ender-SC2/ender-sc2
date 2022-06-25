from abc import abstractmethod

from ender.common import Common


class Requirement:

    @abstractmethod
    def setup(self, common: Common):
        pass

    @abstractmethod
    def check(self) -> bool:
        pass
