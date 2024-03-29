import unittest

from ender.behavior.combat import (
    FocusFireCombatBehavior,
    AttackCenterBehavior,
    MoreRangeBehavior,
    SidewardsBehavior,
    LessRangeBehavior,
    SameRangeBehavior,
)
from ender.behavior.combat.attack_closest_enemy_behavior import AttackClosestEnemyBehavior
from ender.game_plan.condition import Any, No, HaveUnit, AfterTime
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from test.ender_test_bot import EnderTestBot
from test.setup import CreateUnitsTestSetup
from test.test_environment import TestEnvironment, battle_maps


class TestRoachBuilding(unittest.TestCase):
    def test_roach_vs_building_30_supply(self):
        winner = EnderTestBot(
            [
                AttackCenterBehavior(),
                FocusFireCombatBehavior(),
                MoreRangeBehavior(),
                LessRangeBehavior(),
                SidewardsBehavior(),
                SameRangeBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.ROACH, 15, Point2([-10, -10])),
            Any([No(HaveUnit()), AfterTime(180)]),
        )
        loser = EnderTestBot(
            [AttackCenterBehavior(), AttackClosestEnemyBehavior()],
            CreateUnitsTestSetup(UnitTypeId.HATCHERY, 1, Point2([0, 0])),
            No(HaveUnit()),
        )
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())


if __name__ == "__main__":
    unittest.main()
