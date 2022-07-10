import unittest

from ender.behavior.combat import AttackCenterBehavior, NeuralBehavior
from ender.behavior.combat.attack_closest_enemy_behavior import (
    AttackClosestEnemyBehavior,
)
from ender.game_plan.condition import Any, No, HaveUnit, AfterTime
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from test.ender_test_bot import EnderTestBot
from test.setup import CreateUnitsTestSetup, MultipleTestSetup
from test.setup import UpgradedSetup
from test.test_environment import TestEnvironment, battle_maps


class TestInfestorInfestor(unittest.TestCase):
    def test_infestor_vs_infestor_1v1(self):
        winner = EnderTestBot(
            [AttackCenterBehavior(), NeuralBehavior()],
            MultipleTestSetup(
                [
                    CreateUnitsTestSetup(UnitTypeId.INFESTOR, 1, Point2([-10, -10])),
                    UpgradedSetup(),
                ]
            ),
            Any([No(HaveUnit()), AfterTime(180)]),
        )
        loser = EnderTestBot(
            [AttackCenterBehavior(), AttackClosestEnemyBehavior()],
            MultipleTestSetup(
                [
                    CreateUnitsTestSetup(UnitTypeId.INFESTOR, 1, Point2([10, 10])),
                    UpgradedSetup(),
                ]
            ),
            No(HaveUnit()),
        )
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())

    def test_infestor_vs_infestor_1v6(self):
        winner = EnderTestBot(
            [AttackCenterBehavior(), NeuralBehavior()],
            MultipleTestSetup(
                [
                    CreateUnitsTestSetup(UnitTypeId.INFESTOR, 1, Point2([-10, -10])),
                    UpgradedSetup(),
                ]
            ),
            Any([No(HaveUnit()), AfterTime(180)]),
        )
        loser = EnderTestBot(
            [AttackCenterBehavior(), AttackClosestEnemyBehavior()],
            MultipleTestSetup(
                [
                    CreateUnitsTestSetup(UnitTypeId.INFESTOR, 6, Point2([10, 10])),
                    UpgradedSetup(),
                ]
            ),
            No(HaveUnit()),
        )
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())


if __name__ == "__main__":
    unittest.main()
