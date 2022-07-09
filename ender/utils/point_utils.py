from sc2.position import Point2


def closest_n(point_list: list[Point2], reference: Point2, amount: int) -> list:
    point_list = [point for point in point_list if point != reference]
    distances = [point.distance_to(reference) for point in point_list]
    dist_dict = {unit: dist for unit, dist in zip(point_list, distances)}
    sort = sorted(dist_dict.items(), key=lambda item: item[1])
    return [item[0] for item in sort[:amount]]
