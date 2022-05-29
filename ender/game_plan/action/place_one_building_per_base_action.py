from ender.common import Common
from ender.game_plan.action.action import Action
from ender.game_plan.action.building_positioning import BuildingPositioning
from ender.game_plan.action.place_building_action import PlaceBuildingAction
from sc2.ids.unit_typeid import UnitTypeId


class PlaceOneBuildingPerBaseAction(Action):

    def __init__(self, unit_type: UnitTypeId, building_positioning: BuildingPositioning):
        self.common = None
        self.unit_type = unit_type
        self.building_positioning = building_positioning
        self.actions = {}

    def setup(self, common: Common):
        self.common = common
        self.building_positioning.setup(common)

    def execute(self):
        for base in self.common.townhalls:
            if base.tag not in self.actions:
                self.actions[base.tag] = PlaceBuildingAction(self.unit_type, self.building_positioning, 1,
                                                             base.position)
        for action in self.actions:
            action.execute()
