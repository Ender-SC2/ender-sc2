from ender.common import Common
from ender.game_plan.action.action import Action
from ender.game_plan.action.positioning import Positioning
from ender.game_plan.action.place_building import PlaceBuilding
from sc2.ids.unit_typeid import UnitTypeId


class PlaceOneBuildingPerBase(Action):

    def __init__(self, unit_type: UnitTypeId, building_positioning: Positioning):
        self.common = None
        self.unit_type = unit_type
        self.building_positioning = building_positioning
        self.actions = {}

    def setup(self, common: Common):
        self.common = common
        self.building_positioning.setup(common)

    def execute(self):
        for townhall in self.common.townhalls:
            if townhall.tag not in self.actions:
                self.actions[townhall.tag] = PlaceBuilding(self.unit_type, self.building_positioning, 1,
                                                             townhall.position)
        for action in self.actions.values():
            action.execute()
