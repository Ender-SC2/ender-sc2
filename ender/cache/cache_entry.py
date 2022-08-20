from dataclasses import dataclass

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


@dataclass(frozen=True)
class UnitInfo:
    unit_type: UnitTypeId
    position: Point2


@dataclass(frozen=True)
class CacheEntry:
    last_seen: float
    unit_info: UnitInfo
