# strategy.py, Ender

import random
from enum import Enum, auto
from loguru import logger

from ender.game_plan import GamePlan
from ender.game_plan import Step
from ender.game_plan.action.mineral_building_positioning import MineralLinePositioning
from ender.game_plan.action.place_building_per_base import PlaceBuildingPerBase
from ender.game_plan.condition.any import Any
from ender.game_plan.condition.enemy_unit import EnemyUnit
from ender.tech import Tech
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


class Strategy(Tech):
    __did_step0 = False
    needhatches = {} # opening delay until a certain amount of hatches
    structype_order = []
    class Gameplan(Enum):
        TWELVEPOOL = auto()
        ONEBASE = auto()
        ONEBASE_NOGAS = auto()
        TWOBASE = auto()
        TWOBASE_NOGAS = auto()
        THREEBASE_NOGAS = auto()
        THREEBASE = auto()
        TO_LAIR = auto()
        MUTAS = auto()
        LINGBANEMUTA = auto()
        FIVEBASE = auto()
        TO_HIVE = auto()
        ENDGAME = auto()
        LINGWAVE = auto()
    gameplan = Gameplan.ENDGAME
    followup = Gameplan.ENDGAME
    last_bigattack_count = 0
    make_plan = {}
    new_plan = None
    structures_at_hatches = 0
    auto_upgrade = True
    auto_queen = True

    def __step0(self):
        if not self.new_plan:
            self.new_plan = GamePlan(Step(Any([EnemyUnit(UnitTypeId.BANSHEE),
                                               EnemyUnit(UnitTypeId.ORACLE),
                                               EnemyUnit(UnitTypeId.MUTALISK)]),
                                          PlaceBuildingPerBase(UnitTypeId.SPORECRAWLER, MineralLinePositioning())))
            self.new_plan.setup(self)

        #
        self.standard_structype_order()
        #
        choice = random.choice(list(self.Gameplan))
        while choice not in {self.Gameplan.TWELVEPOOL, self.Gameplan.ONEBASE_NOGAS, self.Gameplan.ONEBASE, self.Gameplan.TWOBASE_NOGAS, 
                            self.Gameplan.TWOBASE, self.Gameplan.THREEBASE_NOGAS, self.Gameplan.THREEBASE}:
            choice = random.choice(list(self.Gameplan))
        # choice = self.Gameplan.THREEBASE # debug
        self.set_gameplan(choice)
        #

    async def on_step(self, iteration: int):
        await Tech.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            logger.info('Tag:' + self.gameplan.name)
            await self._client.chat_send('Tag:' + self.gameplan.name, team_only=False)
            self.__did_step0 = True
        #
        if self.bigattack_count != self.last_bigattack_count:
            self.last_bigattack_count = self.bigattack_count
            # change strategy to followup
            plan = self.followup
            # alternatives
            if plan == self.Gameplan.ENDGAME:
                if self.minerals > 3000:
                    if self.gameplan != self.Gameplan.LINGWAVE:
                        plan = self.Gameplan.LINGWAVE
            # skips
            if plan == self.Gameplan.TO_LAIR:
                if len(self.structures(UnitTypeId.LAIR)) > 0:
                    plan = self.Gameplan.FIVEBASE
            if plan == self.Gameplan.FIVEBASE:
                if self.nbases >= 4:
                    plan = self.Gameplan.TO_HIVE
            if plan == self.Gameplan.TO_HIVE:
                if len(self.structures(UnitTypeId.HIVE)) > 0:
                    plan = self.Gameplan.ENDGAME
            logger.info('Transitioning to ' + plan.name)
            await self._client.chat_send('Transitioning to ' + plan.name, team_only=False)
            self.set_gameplan(plan)
        self.new_plan.execute()


    def set_gameplan(self, gameplan):
        self.gameplan = gameplan
        self.zero_make_plan()
        self.standard_needhatches()
        self.opening = []
        if gameplan == self.Gameplan.TWELVEPOOL:
            self.structures_at_hatches = 1
            self.make_plan[UnitTypeId.HATCHERY] = 1
            self.make_plan[UnitTypeId.ZERGLING] = 12
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(('supply',12, UnitTypeId.SPAWNINGPOOL, 1))
            self.followup = self.Gameplan.TWOBASE
        elif gameplan == self.Gameplan.ONEBASE_NOGAS:
            self.structures_at_hatches = 1
            self.make_plan[UnitTypeId.HATCHERY] = 2
            self.make_plan[UnitTypeId.ZERGLING] = 12
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(('supply',16, UnitTypeId.SPAWNINGPOOL, 1))
            self.opening.append(('supply',20, UnitTypeId.HATCHERY, 2))
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.ONEBASE:
            self.structures_at_hatches = 1
            self.make_plan[UnitTypeId.HATCHERY] = 2
            self.make_plan[UnitTypeId.EXTRACTOR] = 2
            self.make_plan[UnitTypeId.ZERGLING] = 2
            self.make_plan[UnitTypeId.ROACH] = 10
            self.make_plan[UnitTypeId.DRONE] = 16 * 1 + 3 * self.make_plan[UnitTypeId.EXTRACTOR] + 1
            self.opening.append(('supply',22, UnitTypeId.HATCHERY, 2))
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.TWOBASE_NOGAS:
            self.structures_at_hatches = 2
            self.make_plan[UnitTypeId.HATCHERY] = 3
            self.make_plan[UnitTypeId.EXTRACTOR] = 0
            self.make_plan[UnitTypeId.ZERGLING] = 36
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(('supply',25, UnitTypeId.HATCHERY, 3))
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.TWOBASE:
            self.structures_at_hatches = 2
            self.make_plan[UnitTypeId.HATCHERY] = 3
            self.make_plan[UnitTypeId.EXTRACTOR] = 3
            self.make_plan[UnitTypeId.ZERGLING] = 12
            self.make_plan[UnitTypeId.ROACH] = 16
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(('supply',25, UnitTypeId.HATCHERY, 3))
            self.followup = self.Gameplan.TO_LAIR
        elif gameplan == self.Gameplan.THREEBASE_NOGAS:
            self.structures_at_hatches = 3
            self.make_plan[UnitTypeId.HATCHERY] = 4
            self.make_plan[UnitTypeId.EXTRACTOR] = 0
            self.make_plan[UnitTypeId.ZERGLING] = 60
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(('supply',35, UnitTypeId.HATCHERY, 4))
            self.followup = self.Gameplan.TO_LAIR
        elif gameplan == self.Gameplan.THREEBASE:
            self.structures_at_hatches = 3
            self.make_plan[UnitTypeId.HATCHERY] = 4
            self.make_plan[UnitTypeId.EXTRACTOR] = 5
            self.make_plan[UnitTypeId.ZERGLING] = 16
            self.make_plan[UnitTypeId.BANELING] = 10
            self.make_plan[UnitTypeId.ROACH] = 16
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(('supply',75, UnitTypeId.HATCHERY, 4))
            self.followup = self.Gameplan.TO_LAIR
        elif gameplan == self.Gameplan.TO_LAIR:
            self.structures_at_hatches = 4
            self.make_plan[UnitTypeId.HATCHERY] = 4
            self.make_plan[UnitTypeId.LAIR] = 1
            self.make_plan[UnitTypeId.EXTRACTOR] = 7
            self.make_plan[UnitTypeId.BANELING] = 10
            self.make_plan[UnitTypeId.ROACH] = 20
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.MUTAS
            if random.random() < 0.5:
                self.followup = self.Gameplan.LINGBANEMUTA
            if random.random() < 0.33:
                self.followup = self.Gameplan.FIVEBASE
        elif gameplan == self.Gameplan.MUTAS:
            self.structures_at_hatches = 4
            self.make_plan[UnitTypeId.HATCHERY] = 4
            self.make_plan[UnitTypeId.EXTRACTOR] = 7
            self.make_plan[UnitTypeId.ZERGLING] = 20
            self.make_plan[UnitTypeId.MUTALISK] = 20
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.TO_HIVE
        elif gameplan == self.Gameplan.LINGBANEMUTA:
            self.structures_at_hatches = 4
            self.make_plan[UnitTypeId.HATCHERY] = 4
            self.make_plan[UnitTypeId.EXTRACTOR] = 7
            self.make_plan[UnitTypeId.ZERGLING] = 20
            self.make_plan[UnitTypeId.BANELING] = 20
            self.make_plan[UnitTypeId.MUTALISK] = 20
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.TO_HIVE
        elif gameplan == self.Gameplan.FIVEBASE:
            self.structures_at_hatches = 5
            self.make_plan[UnitTypeId.HATCHERY] = 5
            self.make_plan[UnitTypeId.EXTRACTOR] = 9
            self.make_plan[UnitTypeId.ZERGLING] = 20
            self.make_plan[UnitTypeId.BANELING] = 10
            self.make_plan[UnitTypeId.ROACH] = 5
            self.make_plan[UnitTypeId.HYDRALISK] = 30
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.TO_HIVE
        elif gameplan == self.Gameplan.TO_HIVE:
            self.structures_at_hatches = 6
            self.make_plan[UnitTypeId.HATCHERY] = 6
            self.make_plan[UnitTypeId.HIVE] = 1
            self.make_plan[UnitTypeId.EXTRACTOR] = 7
            self.make_plan[UnitTypeId.ZERGLING] = 15
            self.make_plan[UnitTypeId.BANELING] = 15
            self.make_plan[UnitTypeId.ROACH] = 15
            self.make_plan[UnitTypeId.HYDRALISK] = 15
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.ENDGAME:
            self.structures_at_hatches = len(self.expansion_locations_list)
            self.make_plan[UnitTypeId.HATCHERY] = len(self.expansion_locations_list)
            self.make_plan[UnitTypeId.EXTRACTOR] = len(self.expansion_locations_list) * 2
            self.make_plan[UnitTypeId.ULTRALISK] = 1
            self.make_plan[UnitTypeId.BANELING] = 4
            self.make_plan[UnitTypeId.ROACH] = 4
            self.make_plan[UnitTypeId.HYDRALISK] = 6
            self.make_plan[UnitTypeId.INFESTOR] = 4
            self.make_plan[UnitTypeId.CORRUPTOR] = 14
            self.make_plan[UnitTypeId.BROODLORD] = 8
            self.make_plan[UnitTypeId.VIPER] = 3
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.LINGWAVE:
            self.structures_at_hatches = len(self.expansion_locations_list)
            self.make_plan[UnitTypeId.HATCHERY] = len(self.expansion_locations_list)
            self.make_plan[UnitTypeId.EXTRACTOR] = len(self.expansion_locations_list) * 2
            self.make_plan[UnitTypeId.ZERGLING] = 2 * (self.supplycap_army - self.army_supply_used)
            self.make_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.ENDGAME
        self.add_morphers()
        self.tech_close()
        # debug
        logger.info('bigattack_count = ' + str(self.bigattack_count))
        logger.info('gameplan = ' + self.gameplan.name)
        lookat = set(self.make_plan.keys())
        for rava in lookat:
            if self.make_plan[rava] > 0:
                logger.info('make_plan: ' + rava.name + ' ' + str(self.make_plan[rava]))
        #
        self.needhatches_restrict(self.structures_at_hatches)

    def droneformula(self) -> int:
        dr = 16 * self.structures_at_hatches + 3 * self.make_plan[UnitTypeId.EXTRACTOR] + 1
        return min(dr, self.supplycap_drones)

    def add_morphers(self):
        # if 7 ravagers are in make_plan, 7 roaches are added
        lookat = set(self.make_plan.keys())
        for rava in lookat:
            if self.make_plan[rava] > 0:
                if rava in self.morph:
                    roach = self.morph[rava]
                    self.make_plan[roach] += self.make_plan[rava]

    def tech_close(self):
        # in make_plan, if roaches > 0, then roachwarrant will be made at least 1.
        changed = True
        while changed:
            changed = False
            lookat = set(self.make_plan.keys())
            for roach in lookat:
                if self.make_plan[roach] > 0:
                    for tech_chain in self.tech_chains:
                        if roach in tech_chain:
                            seen = False
                            for thing in tech_chain:
                                seen = seen or (thing == roach)
                                if not seen: # before
                                    if self.make_plan[thing] < 1:
                                        self.make_plan[thing] = 1
                                        changed = True

    def needhatches_restrict(self, hatches):
        for struc in self.needhatches:
            if struc in self.make_plan:
                if self.make_plan[struc] > 0:
                    self.needhatches[struc] = min(hatches, self.needhatches[struc])

    def zero_make_plan(self):
        self.make_plan = {}
        for unt in self.all_unittypes:
            self.make_plan[unt] = 0
        for stru in self.all_structuretypes:
            self.make_plan[stru] = 0
        for upg in self.all_upgrades:
            self.make_plan[upg] = 0

    def standard_structype_order(self):
        self.structype_order = []
        self.structype_order.append(UnitTypeId.HATCHERY)
        self.structype_order.append(UnitTypeId.SPAWNINGPOOL)
        self.structype_order.append(UnitTypeId.EXTRACTOR)
        self.structype_order.append(UnitTypeId.BANELINGNEST)
        self.structype_order.append(UnitTypeId.ROACHWARREN)
        self.structype_order.append(UnitTypeId.EVOLUTIONCHAMBER)
        self.structype_order.append(UnitTypeId.LAIR)
        self.structype_order.append(UnitTypeId.SPIRE)
        self.structype_order.append(UnitTypeId.INFESTATIONPIT)
        self.structype_order.append(UnitTypeId.NYDUSNETWORK)
        self.structype_order.append(UnitTypeId.NYDUSCANAL)
        self.structype_order.append(UnitTypeId.HIVE)
        self.structype_order.append(UnitTypeId.GREATERSPIRE)
        self.structype_order.append(UnitTypeId.HYDRALISKDEN)
        self.structype_order.append(UnitTypeId.LURKERDENMP)
        self.structype_order.append(UnitTypeId.ULTRALISKCAVERN)

    def standard_needhatches(self):
        self.needhatches = {}
        self.needhatches[UnitTypeId.HATCHERY] = 0
        self.needhatches[UnitTypeId.SPINECRAWLER] = 1
        self.needhatches[UnitTypeId.SPORECRAWLER] = 1
        self.needhatches[UnitTypeId.SPAWNINGPOOL] = 2
        self.needhatches[UnitTypeId.EXTRACTOR] = 3
        self.needhatches[UnitTypeId.BANELINGNEST] = 3
        self.needhatches[UnitTypeId.ROACHWARREN] = 4
        self.needhatches[UnitTypeId.EVOLUTIONCHAMBER] = 4
        self.needhatches[UnitTypeId.LAIR] = 4
        self.needhatches[UnitTypeId.SPIRE] = 4
        self.needhatches[UnitTypeId.INFESTATIONPIT] = 5
        self.needhatches[UnitTypeId.NYDUSNETWORK] = 5
        self.needhatches[UnitTypeId.NYDUSCANAL] = 5
        self.needhatches[UnitTypeId.HIVE] = 5
        self.needhatches[UnitTypeId.GREATERSPIRE] = 6
        self.needhatches[UnitTypeId.HYDRALISKDEN] = 6
        self.needhatches[UnitTypeId.LURKERDENMP] = 6
        self.needhatches[UnitTypeId.ULTRALISKCAVERN] = 6
        #
