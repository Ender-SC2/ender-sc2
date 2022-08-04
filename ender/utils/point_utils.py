from math import sqrt

from sc2.bot_ai import BotAI
from sc2.position import Point2


# Don't overuse it as it does a game request
async def closest_in_path(bot_ai: BotAI, point_list: list[Point2], reference: Point2, max_range: float) -> Point2:
    point_list = [
        point for point in point_list if point != reference and reference.distance_to_point2(point) <= max_range
    ]
    # NOTE: Offsetting the position trying to not be on top of buildings
    distances = [
        await bot_ai.client.query_pathing(point.towards(reference, 3), reference.towards(point, 3))
        for point in point_list
    ]
    dist_dict = {unit: dist for unit, dist in zip(point_list, distances) if dist}
    return min(dist_dict.items(), key=lambda item: item[1])[0]


def closest_n(point_list: list[Point2], reference: Point2, amount: int) -> list[Point2]:
    point_list = [point for point in point_list if point != reference]
    distances = [point.distance_to(reference) for point in point_list]
    dist_dict = {unit: dist for unit, dist in zip(point_list, distances)}
    sort = sorted(dist_dict.items(), key=lambda item: item[1])
    return [item[0] for item in sort[:amount]]


def distance(point1: Point2, point2: Point2) -> float:
    sd = (point1.x - point2.x) * (point1.x - point2.x) + (point1.y - point2.y) * (point1.y - point2.y)
    return sqrt(sd)


def center(point_list: list[Point2]) -> Point2:
    amount = len(point_list)
    return Point2(
        (
            sum(point.x for point in point_list) / amount,
            sum(point.y for point in point_list) / amount,
        )
    )
