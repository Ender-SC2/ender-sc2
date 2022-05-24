# strategy.py, Merkbot, Zerg bot
# 23 may 2022

import random
from enum import Enum, auto

from ender.tech import Tech
from sc2.ids.unit_typeid import UnitTypeId


class Strategy(Tech):
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
    make_plan = {}
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
        choice = self.Gameplan.ONEBASE_NOGAS # test
        self.set_gameplan(choice)
        #
        if self.make_plan[UnitTypeId.HATCHERY] == 99:
            self.make_plan[UnitTypeId.HATCHERY] = random.randrange(4,10)

    async def on_step(self):
        await Tech.on_step(self)
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
                                    # make at least 1
                                    if thing in self.make_plan:
                                        if self.make_plan[thing] < 1:
                                            self.make_plan[thing] = 1
                                            changed = True
                                    else:
                                        self.make_plan[thing] = 1
                                        changed = True

    def set_gameplan(self, gameplan):
        self.gameplan = gameplan
        self.make_plan = {}
        self.standard_structype_order()
        self.standard_needhatches()
        if gameplan == self.Gameplan.ONEBASE_NOGAS:
            self.make_plan[UnitTypeId.HATCHERY] = 1
            self.make_plan[UnitTypeId.EXTRACTOR] = 0
            self.make_plan[UnitTypeId.ZERGLING] = 12
            self.followup = self.Gameplan.TWOBASE
        elif gameplan == self.Gameplan.ONEBASE:
            self.make_plan[UnitTypeId.HATCHERY] = 1
            self.make_plan[UnitTypeId.EXTRACTOR] = 2
            self.make_plan[UnitTypeId.ZERGLING] = 2
            self.make_plan[UnitTypeId.ROACH] = 10
            self.followup = self.Gameplan.TWOBASE
        elif gameplan == self.Gameplan.TWOBASE_NOGAS:
            self.make_plan[UnitTypeId.HATCHERY] = 2
            self.make_plan[UnitTypeId.EXTRACTOR] = 0
            self.make_plan[UnitTypeId.ZERGLING] = 36
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.TWOBASE:
            self.make_plan[UnitTypeId.HATCHERY] = 2
            self.make_plan[UnitTypeId.EXTRACTOR] = 2
            self.make_plan[UnitTypeId.ZERGLING] = 12
            self.make_plan[UnitTypeId.ROACH] = 16
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.THREEBASE_NOGAS:
            self.make_plan[UnitTypeId.HATCHERY] = 3
            self.make_plan[UnitTypeId.EXTRACTOR] = 0
            self.make_plan[UnitTypeId.ZERGLING] = 60
            self.followup = self.Gameplan.LINGBANEMUTA
        elif gameplan == self.Gameplan.THREEBASE:
            self.make_plan[UnitTypeId.HATCHERY] = 3
            self.make_plan[UnitTypeId.EXTRACTOR] = 3
            self.make_plan[UnitTypeId.ZERGLING] = 12
            self.make_plan[UnitTypeId.BANELING] = 10
            self.make_plan[UnitTypeId.ROACH] = 16
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.MUTAS:
            self.make_plan[UnitTypeId.HATCHERY] = 4
            self.make_plan[UnitTypeId.EXTRACTOR] = 5
            self.make_plan[UnitTypeId.ZERGLING] = 20
            self.make_plan[UnitTypeId.MUTALISK] = 20
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.LINGBANEMUTA:
            self.make_plan[UnitTypeId.HATCHERY] = 4
            self.make_plan[UnitTypeId.EXTRACTOR] = 5
            self.make_plan[UnitTypeId.ZERGLING] = 20
            self.make_plan[UnitTypeId.BANELING] = 20
            self.make_plan[UnitTypeId.MUTALISK] = 20
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.ENDGAME:
            self.make_plan[UnitTypeId.HATCHERY] = 99
            self.make_plan[UnitTypeId.EXTRACTOR] = 99
            self.make_plan[UnitTypeId.ULTRALISK] = 1
            self.make_plan[UnitTypeId.BANELING] = 4
            self.make_plan[UnitTypeId.MUTALISK] = 4
            self.make_plan[UnitTypeId.HYDRALISK] = 6
            self.make_plan[UnitTypeId.INFESTOR] = 6
            self.make_plan[UnitTypeId.CORRUPTOR] = 16
            self.make_plan[UnitTypeId.BROODLORD] = 8
            self.make_plan[UnitTypeId.VIPER] = 4
        elif gameplan == self.Gameplan.LINGWAVE:
            self.make_plan[UnitTypeId.HATCHERY] = 99
            self.make_plan[UnitTypeId.EXTRACTOR] = 99
            self.make_plan[UnitTypeId.ZERGLING] = 200
        self.tech_close()
        self.needhatches_restrict(self.make_plan[UnitTypeId.HATCHERY])

    def needhatches_restrict(self, hatches):
        for struc in self.needhatches:
            if struc in self.make_plan:
                if self.make_plan[struc] > 0:
                    self.needhatches[struc] = min(hatches, self.needhatches[struc])

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
