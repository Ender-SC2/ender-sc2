import unittest

from ender.behavior.combat import (
    FocusFireCombatBehavior,
    AttackCenterBehavior,
    MoreRangeBehavior,
    SidewardsBehavior,
    SameRangeBehavior,
    LessRangeBehavior,
    UprampBehavior,
)
from ender.behavior.combat.attack_closest_enemy_behavior import AttackClosestEnemyBehavior
from ender.game_plan.condition import Any, No, HaveUnit, AfterTime
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from test.ender_test_bot import EnderTestBot
from test.setup import CreateUnitsTestSetup
from test.test_environment import TestEnvironment, battle_maps


class TestRoachHydra(unittest.TestCase):
    def test_roach_vs_hydralisk_2_supply(self):
        winner = EnderTestBot(
            [
                AttackCenterBehavior(),
                FocusFireCombatBehavior(),
                MoreRangeBehavior(),
                SameRangeBehavior(),
                SidewardsBehavior(),
                LessRangeBehavior(),
                UprampBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.ROACH, 1, Point2([-10, -10])),
            Any([No(HaveUnit()), AfterTime(180)]),
        )
        loser = EnderTestBot(
            [AttackCenterBehavior(), AttackClosestEnemyBehavior()],
            CreateUnitsTestSetup(UnitTypeId.HYDRALISK, 1, Point2([10, 10])),
            No(HaveUnit()),
        )
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())

    def test_roach_vs_hydralisk_20_supply(self):
        winner = EnderTestBot(
            [
                AttackCenterBehavior(),
                FocusFireCombatBehavior(),
                MoreRangeBehavior(),
                SameRangeBehavior(),
                SidewardsBehavior(),
                LessRangeBehavior(),
                UprampBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.ROACH, 10, Point2([-10, -10])),
            Any([No(HaveUnit()), AfterTime(180)]),
        )
        loser = EnderTestBot(
            [AttackCenterBehavior(), AttackClosestEnemyBehavior()],
            CreateUnitsTestSetup(UnitTypeId.HYDRALISK, 10, Point2([10, 10])),
            No(HaveUnit()),
        )
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())

    def test_roach_vs_hydralisk_50_supply(self):
        winner = EnderTestBot(
            [
                AttackCenterBehavior(),
                FocusFireCombatBehavior(),
                MoreRangeBehavior(),
                SameRangeBehavior(),
                SidewardsBehavior(),
                LessRangeBehavior(),
                UprampBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.ROACH, 25, Point2([-10, -10])),
            Any([No(HaveUnit()), AfterTime(180)]),
        )
        loser = EnderTestBot(
            [AttackCenterBehavior(), AttackClosestEnemyBehavior()],
            CreateUnitsTestSetup(UnitTypeId.HYDRALISK, 25, Point2([10, 10])),
            No(HaveUnit()),
        )
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())


if __name__ == "__main__":
    unittest.main()
