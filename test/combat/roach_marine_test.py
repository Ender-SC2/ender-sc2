import unittest

from ender.behavior.combat import FocusFireCombatBehavior, MoveCenterBehavior, AttackClosestEnemyBehavior, \
    RepositionBehavior
from ender.game_plan.condition import No, AfterTime
from ender.game_plan.condition.any import Any
from ender.game_plan.condition.have_unit import HaveUnit
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from test.ender_test_bot import EnderTestBot
from test.setup import CreateUnitsTestSetup
from test.test_environment import TestEnvironment, battle_maps


class RoachMarineTests(unittest.TestCase):

    def test_roach_marine_20_supply(self):
        winner = EnderTestBot(
            [MoveCenterBehavior(), AttackClosestEnemyBehavior(), FocusFireCombatBehavior(), RepositionBehavior()],
            CreateUnitsTestSetup(UnitTypeId.ROACH, 10, Point2([-10, -10])),
            Any([No(HaveUnit()), AfterTime(60)]))
        loser = EnderTestBot([MoveCenterBehavior()], CreateUnitsTestSetup(UnitTypeId.MARINE, 20, Point2([10, 10])),
                             No(HaveUnit()))
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())

    def test_roach_marine_50_supply(self):
        winner = EnderTestBot([MoveCenterBehavior(), AttackClosestEnemyBehavior(), FocusFireCombatBehavior()],
                              CreateUnitsTestSetup(UnitTypeId.ROACH, 25, Point2([-10, -10])),
                              Any([No(HaveUnit()), AfterTime(60)]))
        loser = EnderTestBot([MoveCenterBehavior()], CreateUnitsTestSetup(UnitTypeId.MARINE, 50, Point2([10, 10])),
                             No(HaveUnit()))
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())

    def test_roach_marine_100_supply(self):
        winner = EnderTestBot([MoveCenterBehavior(), AttackClosestEnemyBehavior(), FocusFireCombatBehavior()],
                              CreateUnitsTestSetup(UnitTypeId.ROACH, 50, Point2([-10, -10])),
                              Any([No(HaveUnit()), AfterTime(60)]))
        loser = EnderTestBot([MoveCenterBehavior()], CreateUnitsTestSetup(UnitTypeId.MARINE, 100, Point2([10, 10])),
                             No(HaveUnit()))
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())


if __name__ == '__main__':
    unittest.main()
