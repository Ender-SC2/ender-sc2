from abc import abstractmethod
from typing import Optional

from ender.common import Common
from sc2.position import Point2


class BuildingPositioning:

    def __init__(self):
        self.common: Optional[Common] = None

    def setup(self, common: Common):
        self.common = common

    @abstractmethod
    def placement(self, close_to: Optional[Point2]) -> Point2:
        pass
