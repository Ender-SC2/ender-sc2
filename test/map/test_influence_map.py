import unittest
from unittest import IsolatedAsyncioTestCase

from ender.map.influence_map import InfluenceMap
from sc2.position import Point2


class TestInfluenceMap(IsolatedAsyncioTestCase):
    async def test_best_point(self):
        sut = InfluenceMap(0.5)
        sut.add_point(Point2((1, 1)), 0.5, 10)
        sut.add_point(Point2((0, 1)), 0.5, 5)
        best_point = sut.get_best_point(Point2((5, 5)), 10, 0)
        assert best_point
        assert best_point.x == 1
        assert best_point.y == 1

    async def test_closest_point(self):
        sut = InfluenceMap(0.5)
        sut.add_point(Point2((1, 1)), 0.5, 10)
        sut.add_point(Point2((2, 2)), 0.5, 10)
        sut.add_point(Point2((3, 3)), 0.5, 1)
        best_point = sut.get_closest_point(Point2((3, 3)), 0, 10, 0)
        assert best_point
        assert best_point.x == 3
        assert best_point.y == 3

    async def test_closest_point_above_minimum(self):
        sut = InfluenceMap(0.5)
        sut.add_point(Point2((1, 1)), 0.5, 10)
        sut.add_point(Point2((2, 2)), 0.5, 10)
        sut.add_point(Point2((3, 3)), 0.5, 1)
        best_point = sut.get_closest_point(Point2((3, 3)), 0, 10, 5)
        assert best_point
        assert best_point.x == 2
        assert best_point.y == 2


if __name__ == "__main__":
    unittest.main()
