import logging
import unittest

from ender.behavior.combat import (
    FocusFireCombatBehavior,
    RepositionBehavior,
    SidewardsBehavior,
    BackBehavior,
    ForwardBehavior,
    AttackCenterBehavior,
)
from ender.behavior.combat.attack_closest_enemy_behavior import (
    AttackClosestEnemyBehavior,
)
from ender.behavior.combat.spell_casting_behavior import SpellCastingBehavior
from ender.behavior.combat.spell_effect_dodging_behavior import (
    SpellEffectDodgingBehavior,
)
from ender.game_plan.condition import Any, No, HaveUnit, AfterTime
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from test.ender_test_bot import EnderTestBot
from test.setup import CreateUnitsTestSetup
from test.test_environment import TestEnvironment, battle_maps

logging.basicConfig(level=logging.DEBUG)


class TestHydraRavager(unittest.TestCase):
    def test_hydra_vs_ravager_6_supply(self):
        winner = EnderTestBot(
            [
                AttackCenterBehavior(),
                BackBehavior(),
                RepositionBehavior(),
                ForwardBehavior(),
                SidewardsBehavior(),
                FocusFireCombatBehavior(),
                SpellEffectDodgingBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.HYDRALISK, 3, Point2([-10, -10])),
            Any([No(HaveUnit()), AfterTime(60)]),
        )
        loser = EnderTestBot(
            [
                AttackCenterBehavior(),
                AttackClosestEnemyBehavior(),
                SpellCastingBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.RAVAGER, 2, Point2([10, 10])),
            No(HaveUnit()),
        )
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())

    def test_hydra_vs_ravager_30_supply(self):
        winner = EnderTestBot(
            [
                AttackCenterBehavior(),
                BackBehavior(),
                RepositionBehavior(),
                ForwardBehavior(),
                SidewardsBehavior(),
                FocusFireCombatBehavior(),
                SpellEffectDodgingBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.HYDRALISK, 15, Point2([-10, -10])),
            Any([No(HaveUnit()), AfterTime(180)]),
        )
        loser = EnderTestBot(
            [
                AttackCenterBehavior(),
                AttackClosestEnemyBehavior(),
                SpellCastingBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.RAVAGER, 10, Point2([10, 10])),
            No(HaveUnit()),
        )
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())

    def test_hydra_vs_ravager_60_supply(self):
        winner = EnderTestBot(
            [
                AttackCenterBehavior(),
                BackBehavior(),
                RepositionBehavior(),
                ForwardBehavior(),
                SidewardsBehavior(),
                FocusFireCombatBehavior(),
                SpellEffectDodgingBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.HYDRALISK, 30, Point2([-10, -10])),
            Any([No(HaveUnit()), AfterTime(180)]),
        )
        loser = EnderTestBot(
            [
                AttackCenterBehavior(),
                AttackClosestEnemyBehavior(),
                SpellCastingBehavior(),
            ],
            CreateUnitsTestSetup(UnitTypeId.RAVAGER, 20, Point2([10, 10])),
            No(HaveUnit()),
        )
        environment = TestEnvironment()
        environment.test(battle_maps[0], winner, loser)
        self.assertTrue(loser.stopped())


if __name__ == "__main__":
    unittest.main()
