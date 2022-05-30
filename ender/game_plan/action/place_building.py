from ender.common import Common
from ender.game_plan.action.action import Action
from ender.game_plan.action.positioning import Positioning
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class PlaceBuilding(Action):

    def __init__(self, unit_type: UnitTypeId, building_positioning: Positioning, amount: int = 1,
                 on_base: Point2 = None):
        super().__init__()
        self.common = None
        self.unit_type = unit_type
        self.building_positioning = building_positioning
        self.amount = amount
        self.on_base = on_base

    def setup(self, common: Common):
        super().setup(common)
        self.common = common
        self.building_positioning.setup(common)

    def execute(self):
        if self.has_building():
            print("Already have building")
            return
        if not self.common.can_afford(self.unit_type):
            print("Can't afford")
            return
        position = self.get_position()
        workers = self.common.units.of_type(UnitTypeId.DRONE).filter(lambda worker: self.common.job_of_unit[worker.tag] in [self.common.Job.MIMMINER, self.common.Job.MIMMINER])\

        print(f"Placing {self.unit_type} at {position}")
        if not workers.empty:
            worker = workers.closest_to(position)
            self.common.job_of_unit[worker.tag] = self.common.Job.BUILDER
            self.common.expiration_of_builder[worker.tag] = self.common.frame + 8 * self.common.seconds  # shortens it
            worker.build(self.unit_type, position)

    def has_building(self):
        if not self.on_base:
            return self.common.all_units.of_type(self.unit_type).amount >= self.amount
        return self.common.all_units.of_type(self.unit_type).closer_than(11, self.on_base).amount >= self.amount

    def get_position(self) -> Point2:
        print(f"Getting position close to {self.on_base}")
        return self.building_positioning.position(self.on_base)
