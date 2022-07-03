import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from sc2.position import Point2


@dataclass(frozen=True)
class InfluenceMapPoint2:
    x: int
    y: int

    def distance_to(self, other) -> float:
        if not isinstance(other, InfluenceMapPoint2):
            return NotImplemented
        sd = (other.x - self.x) * (other.x - self.x) + (other.y - self.y) * (other.y - self.y)
        return math.sqrt(sd)

    def is_closer_than(self, distance: float, other) -> bool:
        return self.distance_to(other) < distance

    def in_range(self, distance: float, other) -> bool:
        return self.distance_to(other) <= distance

    def offset(self, other):
        if not isinstance(other, InfluenceMapPoint2):
            return NotImplemented
        return InfluenceMapPoint2(self.x + other.x, self.y + other.y)


# TODO: Have an option that can consider walkable positions
class InfluenceMap:
    # TODO: Check actual max map size
    MAX_MAP_SIZE: int = 512

    def __init__(self, map_radius: float):
        self._map_radius = map_radius
        self._map_size = int(math.ceil(self.MAX_MAP_SIZE / self._map_radius))
        self._map = np.ndarray(shape=(self._map_size, self._map_size), dtype=np.float32)

    def reset(self):
        self._map.fill(0)

    def add_point(self, center: Point2, radius: float, weight: float):
        local_radius = self._radius_to_local(radius)
        local_center = self._point_to_local(center)
        for x in range(-local_radius, local_radius):
            for y in range(-local_radius, local_radius):
                check_position = InfluenceMapPoint2(local_center.x + x, local_center.y + y)
                if self._in_bounds(check_position) and check_position.is_closer_than(local_radius, local_center):
                    np.add.at(self._map, (check_position.x, check_position.y), weight)

    def get_best_point(self, center: Point2, radius: float, minimum: float) -> Optional[Point2]:
        local_radius = self._radius_to_local(radius)
        local_center = self._point_to_local(center)
        result = None
        value = minimum
        for distance in range(0, local_radius):
            possible_positions = set([
                p.offset(local_center) for p in (
                        [InfluenceMapPoint2(dx, -distance) for dx in range(-distance, distance + 1)] +
                        [InfluenceMapPoint2(dx, distance) for dx in range(-distance, distance + 1)] +
                        [InfluenceMapPoint2(-distance, dy) for dy in range(-distance, distance + 1)] +
                        [InfluenceMapPoint2(distance, dy) for dy in range(-distance, distance + 1)]
                )
            ])
            for position in possible_positions:
                if self._in_bounds(position) and \
                        value < self._map[position.x][position.y] and \
                        local_center.in_range(local_radius, position):
                    result = self._local_to_global(position)
                    value = self._map[position.x][position.y]
        return result

    def get_closest_point(self, center: Point2, dodge_radius: float, radius: float, minimum: float) -> Optional[Point2]:
        local_radius = self._radius_to_local(radius)
        local_center = self._point_to_local(center)
        for distance in range(0, local_radius):
            possible_positions = set([
                p.offset(local_center) for p in (
                        [InfluenceMapPoint2(dx, -distance) for dx in range(-distance, distance + 1)] +
                        [InfluenceMapPoint2(dx, distance) for dx in range(-distance, distance + 1)] +
                        [InfluenceMapPoint2(-distance, dy) for dy in range(-distance, distance + 1)] +
                        [InfluenceMapPoint2(distance, dy) for dy in range(-distance, distance + 1)]
                )
            ])
            for position in possible_positions:
                if self._in_bounds(position) and \
                        minimum < self._map[position.x][position.y] and \
                        local_center.in_range(local_radius, position):
                    result = self._local_to_global(position)
                    if result != center:
                        return result.towards(center, -dodge_radius)
                    else:
                        return result
        return None

    def max_value(self) -> float:
        return self._map.argmax()

    def _to_global(self, x: int, y: int) -> Point2:
        return Point2((x * self._map_radius, y * self._map_radius))

    def _local_to_global(self, point: InfluenceMapPoint2) -> Point2:
        return self._to_global(point.x, point.y)

    def _radius_to_local(self, radius: float) -> int:
        return round(radius / self._map_radius)

    def _to_local(self, x: float, y: float) -> InfluenceMapPoint2:
        return InfluenceMapPoint2(round(x / self._map_radius), round(y / self._map_radius))

    def _point_to_local(self, point: Point2) -> InfluenceMapPoint2:
        return self._to_local(point.x, point.y)

    def _in_bounds(self, point: InfluenceMapPoint2) -> bool:
        return 0 <= point.x < self._map_size and 0 <= point.y < self._map_size
