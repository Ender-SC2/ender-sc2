from abc import abstractmethod, ABC
from typing import Optional

from ender.common import Common
from sc2.position import Point2


class Positioning(ABC):
    common: Common

    def setup(self, common: Common):
        self.common = common

    @abstractmethod
    def position(self, close_to: Optional[Point2]) -> Optional[Point2]:
        pass
