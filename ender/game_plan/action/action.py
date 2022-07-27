from abc import abstractmethod, ABC

from ender.common import Common


class IAction(ABC):
    @abstractmethod
    def setup(self, common: Common):
        pass

    @abstractmethod
    def execute(self) -> bool:
        pass
