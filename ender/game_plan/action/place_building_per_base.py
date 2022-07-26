from ender.common import Common
from ender.game_plan.action.action import IAction
from ender.game_plan.action.place_building import PlaceBuilding
from ender.game_plan.action.positioning import Positioning
from ender.game_plan.action.random_positioning import RandomPositioning
from sc2.ids.unit_typeid import UnitTypeId


class PlaceBuildingPerBase(IAction):
    def __init__(
        self, unit_type: UnitTypeId, building_positioning: Positioning = RandomPositioning(), amount: int = 1
    ):
        self.common = None
        self.unit_type = unit_type
        self.building_positioning = building_positioning
        self.actions = {}
        self.amount = amount

    def setup(self, common: Common):
        self.common = common
        self.building_positioning.setup(common)

    def execute(self):
        for townhall in self.common.townhalls:
            if townhall.tag not in self.actions:
                action = PlaceBuilding(self.unit_type, self.building_positioning, self.amount, townhall.position)
                action.setup(self.common)
                self.actions[townhall.tag] = action
        self.actions = {tag: action for tag, action in self.actions.items() if tag in self.common.townhalls.tags}
        for action in self.actions.values():
            action.execute()
        return False
