# strategy.py, Merkbot, Zerg bot
# 20 may 2022

import random
from enum import Enum, auto

from ender.common import Common
from sc2.ids.unit_typeid import UnitTypeId


class Strategy(Common):
    __did_step0 = False
    needhatches = {} # opening delay until a certain amount of hatches
    structype_order = []
    class Gameplan(Enum):
        ONEBASE = auto()
        ONEBASE_NOGAS = auto()
        TWOBASE = auto()
        TWOBASE_NOGAS = auto()
        THREEBASE_NOGAS = auto()
        THREEBASE = auto()
        MUTAS = auto()
        LINGBANEMUTA = auto()
        ENDGAME = auto()
        LINGWAVE = auto()
    gameplan = Gameplan.ENDGAME
    followup = Gameplan.ENDGAME
    last_bigattack_count = 0
    #

    def __step0(self):
        #
        # init:
        self.set_gameplan(self.Gameplan.ENDGAME)
        #
        # the choice:
        choice = random.choice(list(self.Gameplan))
        # choice must be an opening
        while choice in {self.Gameplan.LINGWAVE}:
            choice = random.choice(list(self.Gameplan))
        #choice = self.Gameplan.TWOBASE_NOGAS # test
        self.set_gameplan(choice)
        #
        if self.restrict_hatcheries == 99:
            self.restrict_hatcheries = random.randrange(4,10)

    async def on_step(self):
        await Common.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        if self.bigattack_count != self.last_bigattack_count:
            self.last_bigattack_count = self.bigattack_count
            # change strategy to followup
            plan = self.followup
            if plan == self.Gameplan.ENDGAME:
                if self.minerals > 2500:
                    plan = self.Gameplan.LINGWAVE
            self.set_gameplan(plan)
             
    def set_gameplan(self, gameplan):
        self.gameplan = gameplan
        self.armyplan = {}
        self.standard_structype_order()
        self.standard_needhatches()
        if gameplan == self.Gameplan.ONEBASE_NOGAS:
            self.restrict_hatcheries = 1
            self.restrict_extractors = 0
            self.needhatches[UnitTypeId.SPAWNINGPOOL] = 1
            self.armyplan[UnitTypeId.ZERGLING] = 12
            self.followup = self.Gameplan.TWOBASE
        elif gameplan == self.Gameplan.ONEBASE:
            self.restrict_hatcheries = 1
            self.restrict_extractors = 2
            self.needhatches[UnitTypeId.SPAWNINGPOOL] = 1
            self.needhatches[UnitTypeId.ROACHWARREN] = 1
            self.armyplan[UnitTypeId.ZERGLING] = 2
            self.armyplan[UnitTypeId.ROACH] = 10
            self.followup = self.Gameplan.TWOBASE
        elif gameplan == self.Gameplan.TWOBASE_NOGAS:
            self.restrict_hatcheries = 2
            self.restrict_extractors = 0
            self.armyplan[UnitTypeId.ZERGLING] = 36
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.TWOBASE:
            self.restrict_hatcheries = 2
            self.restrict_extractors = 2
            self.needhatches[UnitTypeId.EXTRACTOR] = 2
            self.needhatches[UnitTypeId.ROACHWARREN] = 2
            self.armyplan[UnitTypeId.ZERGLING] = 12
            self.armyplan[UnitTypeId.ROACH] = 16
            self.structype_order = []
            self.structype_order.append(UnitTypeId.HATCHERY)
            self.structype_order.append(UnitTypeId.SPAWNINGPOOL)
            self.structype_order.append(UnitTypeId.EXTRACTOR)
            self.structype_order.append(UnitTypeId.ROACHWARREN)
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.THREEBASE_NOGAS:
            self.restrict_hatcheries = 3
            self.restrict_extractors = 0
            self.armyplan[UnitTypeId.ZERGLING] = 60
            self.followup = self.Gameplan.LINGBANEMUTA
        elif gameplan == self.Gameplan.THREEBASE:
            self.restrict_hatcheries = 3
            self.restrict_extractors = 3
            self.needhatches[UnitTypeId.ROACHWARREN] = 3
            self.armyplan[UnitTypeId.ZERGLING] = 12
            self.armyplan[UnitTypeId.BANELING] = 10
            self.armyplan[UnitTypeId.ROACH] = 16
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.MUTAS:
            self.restrict_hatcheries = 4
            self.restrict_extractors = 5
            self.needhatches[UnitTypeId.EVOLUTIONCHAMBER] = 5
            self.structype_order = []
            self.structype_order.append(UnitTypeId.HATCHERY)
            self.structype_order.append(UnitTypeId.SPAWNINGPOOL)
            self.structype_order.append(UnitTypeId.EXTRACTOR)
            self.structype_order.append(UnitTypeId.LAIR)
            self.structype_order.append(UnitTypeId.SPIRE)
            self.armyplan[UnitTypeId.ZERGLING] = 20
            self.armyplan[UnitTypeId.MUTALISK] = 20
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.LINGBANEMUTA:
            self.restrict_hatcheries = 4
            self.restrict_extractors = 5
            self.structype_order = []
            self.structype_order.append(UnitTypeId.HATCHERY)
            self.structype_order.append(UnitTypeId.SPAWNINGPOOL)
            self.structype_order.append(UnitTypeId.EXTRACTOR)
            self.structype_order.append(UnitTypeId.BANELINGNEST)
            self.structype_order.append(UnitTypeId.EVOLUTIONCHAMBER)
            self.structype_order.append(UnitTypeId.LAIR)
            self.structype_order.append(UnitTypeId.SPIRE)
            self.armyplan[UnitTypeId.ZERGLING] = 20
            self.armyplan[UnitTypeId.BANELING] = 20
            self.armyplan[UnitTypeId.MUTALISK] = 20
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.ENDGAME:
            self.restrict_hatcheries = 99
            self.restrict_extractors = 99
            self.armyplan[UnitTypeId.ULTRALISK] = 1
            self.armyplan[UnitTypeId.BANELING] = 4
            self.armyplan[UnitTypeId.MUTALISK] = 4
            self.armyplan[UnitTypeId.HYDRALISK] = 6
            self.armyplan[UnitTypeId.INFESTOR] = 6
            self.armyplan[UnitTypeId.CORRUPTOR] = 16
            self.armyplan[UnitTypeId.BROODLORD] = 8
            self.armyplan[UnitTypeId.VIPER] = 4
        elif gameplan == self.Gameplan.LINGWAVE:
            self.restrict_hatcheries = 99
            self.restrict_extractors = 99
            self.armyplan[UnitTypeId.ZERGLING] = 100

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
