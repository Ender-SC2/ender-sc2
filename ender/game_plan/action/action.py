from abc import abstractmethod, ABC

from ender.common import Common


class IAction(ABC):
    common: Common

    def setup(self, common: Common):
        self.common = common

    @abstractmethod
    def execute(self) -> bool:
        raise NotImplementedError()
