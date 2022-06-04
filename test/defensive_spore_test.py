from ender.common import Common
from ender.game_plan.requirement.all import All
from ender.game_plan.requirement.have_structure import HaveStructure
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from test.test_base import TestBase


class DefensiveSporeTest(TestBase):

    def __init__(self):
        super().__init__()
        self.passed = False
        self.common = None
        self.created = False
        self.requirement = All(HaveStructure(UnitTypeId.SPORECRAWLER, 1))

    def setup(self, common: Common):
        self.common = common
        self.requirement.setup(common)

    async def on_step(self):
        if self.passed:
            return
        if self.created:
            self.passed = self.requirement.check()
            return
        await self.create_unit()

    async def create_unit(self):
        if self.common.enemy_units.empty:
            return
        closest_unit = self.common.enemy_units.first
        if not closest_unit:
            return
        if self.common.all_units.of_type(UnitTypeId.SPAWNINGPOOL).ready.empty:
            return
        self.created = True
        possible_units = {Race.Terran: UnitTypeId.BANSHEE, Race.Zerg: UnitTypeId.MUTALISK,
                          Race.Protoss: UnitTypeId.ORACLE}
        wanted_unit = possible_units[self.common.enemy_race]

        if self.common.enemy_units.of_type(wanted_unit).closer_than(11, self.common.ourmain).empty:
            await self.common.client.debug_create_unit(
                [[wanted_unit, 1, self.common.ourmain, closest_unit.owner_id]])

    def check(self) -> bool:
        return self.passed
