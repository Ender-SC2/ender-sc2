from dataclasses import dataclass

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


@dataclass(frozen=True)
class Emergency:
    unit_type: UnitTypeId


@dataclass(frozen=True)
class EmergencyStructure(Emergency):
    location: Point2


@dataclass(frozen=True)
class EmergencyUnit(Emergency):
    amount: int


class EmergencyQueue:
    """
    Holds emergency queue
    """
    emergency_queue = dict[int, Emergency]()

    def queue(self):
        return self.emergency_queue
