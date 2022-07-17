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
from ender.game_plan.action.worker_scout_action import WorkerScoutAction
from ender.game_plan.condition import HaveUnit
from ender.tech import Tech
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


class Strategy(Tech):
    __did_step0 = False
    needhatches = {}  # opening delay until a certain amount of hatches
    building_order = []  # opening buildings order explicit
    structype_order = []

    class Gameplan(Enum):
        TWELVEPOOL = auto()
        ONEBASE = auto()
        ONEBASE_NOGAS = auto()
        TWOBASE = auto()
        TWOBASE_NOGAS = auto()
        THREEBASE_NOGAS = auto()
        THREEBASE = auto()
        RAVATHREE = auto()
        REACTIVE = auto()
        SWARM = auto()
        FOURBASE = auto()
        TO_LAIR = auto()
        # with lair:
        TO_SPIRE = auto()
        MUTAS = auto()
        LINGBANEMUTA = auto()
        FIVEBASE = auto()
        TO_HIVE = auto()
        # with hive:
        ENDGAME = auto()
        LINGWAVE = auto()
        ULTRAWAVE = auto()

    openingplans = {
        Gameplan.TWELVEPOOL,
        Gameplan.ONEBASE_NOGAS,
        Gameplan.ONEBASE,
        Gameplan.TWOBASE_NOGAS,
        Gameplan.TWOBASE,
        Gameplan.THREEBASE_NOGAS,
        Gameplan.THREEBASE,
        Gameplan.RAVATHREE,
        Gameplan.REACTIVE,
    }
    gameplan = Gameplan.ENDGAME
    followup = Gameplan.ENDGAME
    last_wave_count = 0
    zero_plan = {}  # 0 for every unit, structure, or upgrade
    result_plan = {}
    new_plan = None
    structures_at_hatches = 0
    auto_upgrade = True
    auto_queen = True

    def __step0(self):
        #
        self.new_plan = GamePlan(
            [
                Step(
                    Any([EnemyUnit(UnitTypeId.BANSHEE), EnemyUnit(UnitTypeId.ORACLE), EnemyUnit(UnitTypeId.MUTALISK)]),
                    PlaceBuildingPerBase(UnitTypeId.SPORECRAWLER, MineralLinePositioning()),
                ),
                Step(HaveUnit(UnitTypeId.DRONE, 13), WorkerScoutAction()),
            ]
        )
        self.new_plan.setup(self)
        #
        self.init_zero_plan()
        #
        self.standard_structype_order()
        #
        choice = random.choice(list(self.Gameplan))
        while choice not in self.openingplans:
            choice = random.choice(list(self.Gameplan))
        #
        # here you can fix a choice to debug an opening
        choice = self.Gameplan.REACTIVE
        self.set_gameplan(choice)
        #

    async def on_step(self, iteration: int):
        await Tech.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            logger.info("Tag:" + self.gameplan.name)
            await self._client.chat_send("Tag:" + self.gameplan.name, team_only=False)
            self.__did_step0 = True
        #
        if self.wave_count != self.last_wave_count:
            self.last_wave_count = self.wave_count
            # change strategy to followup
            plan = self.followup
            # alternatives
            if plan == self.Gameplan.ENDGAME:
                if self.minerals > 3000:
                    if self.gameplan != self.Gameplan.LINGWAVE:
                        plan = self.Gameplan.LINGWAVE
                if (self.minerals > 4500) and (self.vespene >= 3000):
                    if len(self.structures(UnitTypeId.ULTRALISKCAVERN).ready) > 0:
                        if self.gameplan != self.Gameplan.ULTRAWAVE:
                            plan = self.Gameplan.ULTRAWAVE
            # skip on goal reached
            if plan == self.Gameplan.TO_LAIR:
                if len(self.structures(UnitTypeId.LAIR)) > 0:
                    plan = self.Gameplan.TO_SPIRE
            if plan == self.Gameplan.FIVEBASE:
                if self.nbases >= 5:
                    plan = self.Gameplan.TO_HIVE
            if plan == self.Gameplan.TO_HIVE:
                if len(self.structures(UnitTypeId.HIVE)) > 0:
                    plan = self.Gameplan.ENDGAME
            logger.info("Transitioning to " + plan.name)
            await self._client.chat_send("Transitioning to " + plan.name, team_only=False)
            self.set_gameplan(plan)
        #
        self.new_plan.execute()
        #
        await self.react()

    def set_gameplan(self, gameplan):
        self.gameplan = gameplan
        self.result_plan = self.zero_plan.copy()
        self.standard_needhatches()
        self.building_order = []
        self.opening = []
        if gameplan == self.Gameplan.TWELVEPOOL:
            self.structures_at_hatches = 1
            self.result_plan[UnitTypeId.HATCHERY] = 1
            self.result_plan[UnitTypeId.ZERGLING] = 12
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(("supply", 12, UnitTypeId.SPAWNINGPOOL, 1))
            self.followup = self.Gameplan.TWOBASE
        elif gameplan == self.Gameplan.ONEBASE_NOGAS:
            self.structures_at_hatches = 1
            self.result_plan[UnitTypeId.HATCHERY] = 2
            self.result_plan[UnitTypeId.ZERGLING] = 12
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(("supply", 16, UnitTypeId.SPAWNINGPOOL, 1))
            self.opening.append(("supply", 20, UnitTypeId.HATCHERY, 2))
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.ONEBASE:
            self.structures_at_hatches = 1
            self.result_plan[UnitTypeId.HATCHERY] = 2
            self.result_plan[UnitTypeId.EXTRACTOR] = 2
            self.result_plan[UnitTypeId.ZERGLING] = 2
            self.result_plan[UnitTypeId.ROACH] = 10
            self.result_plan[UnitTypeId.DRONE] = 16 * 1 + 3 * self.result_plan[UnitTypeId.EXTRACTOR] + 1
            self.opening.append(("supply", 22, UnitTypeId.HATCHERY, 2))
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.TWOBASE_NOGAS:
            self.structures_at_hatches = 2
            self.result_plan[UnitTypeId.HATCHERY] = 3
            self.result_plan[UnitTypeId.EXTRACTOR] = 0
            self.result_plan[UnitTypeId.ZERGLING] = 45
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(("supply", 25, UnitTypeId.HATCHERY, 3))
            self.followup = self.Gameplan.THREEBASE
        elif gameplan == self.Gameplan.TWOBASE:
            self.structures_at_hatches = 2
            self.result_plan[UnitTypeId.HATCHERY] = 3
            self.result_plan[UnitTypeId.EXTRACTOR] = 3
            self.result_plan[UnitTypeId.ZERGLING] = 12
            self.result_plan[UnitTypeId.ROACH] = 16
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(("supply", 25, UnitTypeId.HATCHERY, 3))
            self.followup = self.Gameplan.TO_LAIR
        elif gameplan == self.Gameplan.THREEBASE_NOGAS:
            self.structures_at_hatches = 3
            self.result_plan[UnitTypeId.HATCHERY] = 4
            self.result_plan[UnitTypeId.EXTRACTOR] = 0
            self.result_plan[UnitTypeId.ZERGLING] = 65
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(("supply", 35, UnitTypeId.HATCHERY, 4))
            self.followup = self.Gameplan.FOURBASE
        elif gameplan == self.Gameplan.THREEBASE:
            self.structures_at_hatches = 3
            self.result_plan[UnitTypeId.HATCHERY] = 4
            self.result_plan[UnitTypeId.EXTRACTOR] = 5
            self.result_plan[UnitTypeId.ZERGLING] = 16
            self.result_plan[UnitTypeId.BANELING] = 10
            self.result_plan[UnitTypeId.ROACH] = 20
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(("supply", 75, UnitTypeId.HATCHERY, 4))
            self.followup = self.Gameplan.TO_LAIR
        elif gameplan == self.Gameplan.RAVATHREE:
            self.structures_at_hatches = 3
            self.result_plan[UnitTypeId.HATCHERY] = 4
            self.result_plan[UnitTypeId.EXTRACTOR] = 5
            self.result_plan[UnitTypeId.ZERGLING] = 5
            self.result_plan[UnitTypeId.RAVAGER] = 16
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.opening.append(("supply", 75, UnitTypeId.HATCHERY, 4))
            self.followup = self.Gameplan.TO_LAIR
        elif gameplan == self.Gameplan.REACTIVE:
            self.structures_at_hatches = 5
            self.result_plan[UnitTypeId.HATCHERY] = 6
            self.result_plan[UnitTypeId.EXTRACTOR] = 12
            self.result_plan[UnitTypeId.ZERGLING] = 10
            self.result_plan[UnitTypeId.BANELING] = 10
            self.result_plan[UnitTypeId.ROACH] = 20
            self.result_plan[UnitTypeId.RAVAGER] = 20
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.building_order = [
                UnitTypeId.HATCHERY,
                UnitTypeId.HATCHERY,
                UnitTypeId.SPAWNINGPOOL,
                UnitTypeId.HATCHERY,
                UnitTypeId.HATCHERY,
                UnitTypeId.HATCHERY,
                UnitTypeId.ROACHWARREN,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.HATCHERY,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.BANELINGNEST,
                UnitTypeId.EXTRACTOR,
                UnitTypeId.EXTRACTOR,
            ]
            self.structype_order = []
            self.followup = self.Gameplan.TO_LAIR
        elif gameplan == self.Gameplan.FOURBASE:
            # wants to reach max
            self.structures_at_hatches = 4
            self.result_plan[UnitTypeId.HATCHERY] = 6
            self.result_plan[UnitTypeId.EXTRACTOR] = 8
            self.result_plan[UnitTypeId.ZERGLING] = 10
            self.result_plan[UnitTypeId.BANELING] = 20
            self.result_plan[UnitTypeId.ROACH] = 30
            self.result_plan[UnitTypeId.RAVAGER] = 10
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.TO_LAIR
        elif gameplan == self.Gameplan.TO_LAIR:
            self.structures_at_hatches = 4
            self.result_plan[UnitTypeId.HATCHERY] = 4
            self.result_plan[UnitTypeId.LAIR] = 1
            self.result_plan[UnitTypeId.EXTRACTOR] = 7
            self.result_plan[UnitTypeId.BANELING] = 10
            self.result_plan[UnitTypeId.ROACH] = 20
            self.result_plan[UnitTypeId.RAVAGER] = 10
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.TO_SPIRE
            if random.random() * 2 < 1:
                self.followup = self.Gameplan.FIVEBASE
            if random.random() * 3 < 1:
                self.followup = self.Gameplan.SWARM
        elif gameplan == self.Gameplan.SWARM:
            self.structures_at_hatches = 4
            self.result_plan[UnitTypeId.HATCHERY] = 5
            self.result_plan[UnitTypeId.EXTRACTOR] = 7
            self.result_plan[UnitTypeId.SWARMHOSTMP] = 20
            self.result_plan[UnitTypeId.BANELING] = 2
            self.result_plan[UnitTypeId.OVERLORDTRANSPORT] = 2
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.TO_HIVE
        elif gameplan == self.Gameplan.TO_SPIRE:
            self.structures_at_hatches = 4
            self.result_plan[UnitTypeId.HATCHERY] = 5
            self.result_plan[UnitTypeId.EXTRACTOR] = 8
            self.result_plan[UnitTypeId.ZERGLING] = 20
            self.result_plan[UnitTypeId.BANELING] = 10
            self.result_plan[UnitTypeId.ROACH] = 10
            self.result_plan[UnitTypeId.RAVAGER] = 5
            self.result_plan[UnitTypeId.OVERLORDTRANSPORT] = 2
            self.iffadd_result(UnitTypeId.LURKERDENMP, UnitTypeId.LURKER, 2)
            self.result_plan[UnitTypeId.SPIRE] = 1
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.MUTAS
            if random.random() * 2 < 1:
                self.followup = self.Gameplan.LINGBANEMUTA
        elif gameplan == self.Gameplan.MUTAS:
            self.structures_at_hatches = 5
            self.result_plan[UnitTypeId.HATCHERY] = 4
            self.result_plan[UnitTypeId.EXTRACTOR] = 7
            self.result_plan[UnitTypeId.ZERGLING] = 18
            self.result_plan[UnitTypeId.MUTALISK] = 20
            self.result_plan[UnitTypeId.BANELING] = 2
            self.result_plan[UnitTypeId.OVERLORDTRANSPORT] = 2
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.TO_HIVE
        elif gameplan == self.Gameplan.LINGBANEMUTA:
            self.structures_at_hatches = 5
            self.result_plan[UnitTypeId.HATCHERY] = 4
            self.result_plan[UnitTypeId.EXTRACTOR] = 7
            self.result_plan[UnitTypeId.ZERGLING] = 20
            self.result_plan[UnitTypeId.BANELING] = 20
            self.result_plan[UnitTypeId.MUTALISK] = 20
            self.result_plan[UnitTypeId.OVERLORDTRANSPORT] = 2
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.TO_HIVE
        elif gameplan == self.Gameplan.FIVEBASE:
            self.structures_at_hatches = 5
            self.result_plan[UnitTypeId.HATCHERY] = 5
            self.result_plan[UnitTypeId.EXTRACTOR] = 9
            self.result_plan[UnitTypeId.ZERGLING] = 20
            self.result_plan[UnitTypeId.BANELING] = 10
            self.result_plan[UnitTypeId.ROACH] = 10
            self.result_plan[UnitTypeId.RAVAGER] = 5
            self.result_plan[UnitTypeId.HYDRALISK] = 20
            self.result_plan[UnitTypeId.OVERLORDTRANSPORT] = 2
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.TO_HIVE
        elif gameplan == self.Gameplan.TO_HIVE:
            self.structures_at_hatches = 6
            self.result_plan[UnitTypeId.HATCHERY] = 6
            self.result_plan[UnitTypeId.HIVE] = 1
            self.result_plan[UnitTypeId.EXTRACTOR] = 7
            self.result_plan[UnitTypeId.ZERGLING] = 6
            self.result_plan[UnitTypeId.BANELING] = 16
            self.result_plan[UnitTypeId.ROACH] = 16
            self.result_plan[UnitTypeId.RAVAGER] = 6
            self.result_plan[UnitTypeId.HYDRALISK] = 16
            self.result_plan[UnitTypeId.INFESTOR] = 3
            self.result_plan[UnitTypeId.OVERLORDTRANSPORT] = 2
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.ENDGAME:
            self.structures_at_hatches = 99
            self.result_plan[UnitTypeId.HATCHERY] = len(self.freeexpos) + self.nbases
            self.result_plan[UnitTypeId.EXTRACTOR] = len(self.freegeysers) + len(self.extractors)
            self.iffadd_result(UnitTypeId.ULTRALISKCAVERN, UnitTypeId.ULTRALISK, 1)
            self.iffadd_result(UnitTypeId.BANELINGNEST, UnitTypeId.BANELING, 5)
            self.iffadd_result(UnitTypeId.ROACHWARREN, UnitTypeId.ROACH, 5)
            self.iffadd_result(UnitTypeId.HYDRALISKDEN, UnitTypeId.HYDRALISK, 5)
            self.iffadd_result(UnitTypeId.INFESTATIONPIT, UnitTypeId.INFESTOR, 4)
            self.iffadd_result(UnitTypeId.SPIRE, UnitTypeId.CORRUPTOR, 14)
            self.iffadd_result(UnitTypeId.GREATERSPIRE, UnitTypeId.BROODLORD, 8)
            self.iffadd_result(UnitTypeId.SPIRE, UnitTypeId.VIPER, 3)
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.LINGWAVE:
            self.structures_at_hatches = 99
            self.result_plan[UnitTypeId.HATCHERY] = len(self.freeexpos) + self.nbases
            self.result_plan[UnitTypeId.EXTRACTOR] = len(self.freegeysers) + len(self.extractors)
            self.result_plan[UnitTypeId.ZERGLING] = 2 * (self.supplycap_army - self.army_supply_used)
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.ENDGAME
        elif gameplan == self.Gameplan.ULTRAWAVE:
            self.structures_at_hatches = 99
            self.result_plan[UnitTypeId.HATCHERY] = len(self.freeexpos) + self.nbases
            self.result_plan[UnitTypeId.EXTRACTOR] = len(self.freegeysers) + len(self.extractors)
            self.result_plan[UnitTypeId.ULTRALISK] = 10
            self.result_plan[UnitTypeId.MUTALISK] = 15
            self.result_plan[UnitTypeId.DRONE] = self.droneformula()
            self.followup = self.Gameplan.ENDGAME
        self.add_morphers()
        self.tech_close()
        # debug
        logger.info("wave_count = " + str(self.wave_count))
        logger.info("gameplan = " + self.gameplan.name)
        lookat = set(self.result_plan.keys())
        for rava in lookat:
            if self.result_plan[rava] > 0:
                logger.info("result_plan: " + rava.name + " " + str(self.result_plan[rava]))
        #
        self.needhatches_restrict(self.structures_at_hatches)
        #

    def iffadd_result(self, cond, typ, amount):
        if len(self.structures(cond)) > 0:
            self.result_plan[typ] = amount
        else:
            self.result_plan[cond] = 1

    def droneformula(self) -> int:
        dr = 16 * self.structures_at_hatches + 3 * self.result_plan[UnitTypeId.EXTRACTOR] + 1
        return min(dr, self.supplycap_drones)

    def add_morphers(self):
        # if 7 ravagers are in result_plan, 7 roaches are added
        lookat = set(self.result_plan.keys())
        for rava in lookat:
            if self.result_plan[rava] > 0:
                if rava in self.morph:
                    roach = self.morph[rava]
                    self.result_plan[roach] += self.result_plan[rava]

    def tech_close(self):
        # in result_plan, if roaches > 0, then roachwarrant will be made at least 1.
        changed = True
        while changed:
            changed = False
            lookat = set(self.result_plan.keys())
            for roach in lookat:
                if self.result_plan[roach] > 0:
                    for tech_chain in self.tech_chains:
                        if roach in tech_chain:
                            seen = False
                            for thing in tech_chain:
                                seen = seen or (thing == roach)
                                if not seen:  # before
                                    if self.result_plan[thing] < 1:
                                        self.result_plan[thing] = 1
                                        changed = True

    def needhatches_restrict(self, hatches):
        for struc in self.needhatches:
            if struc in self.result_plan:
                if self.result_plan[struc] > 0:
                    self.needhatches[struc] = min(hatches, self.needhatches[struc])

    def init_zero_plan(self):
        self.zero_plan = {}
        for unt in self.all_unittypes:
            self.zero_plan[unt] = 0
        for stru in self.all_structuretypes:
            self.zero_plan[stru] = 0
        for upg in self.all_upgrades:
            self.zero_plan[upg] = 0

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
        # self.structype_order.append(UnitTypeId.NYDUSCANAL) not a required building
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

    async def react(self):
        if self.function_listens("react", 50):
            if self.gameplan == self.Gameplan.REACTIVE:
                # my started bases
                mybases = 0
                for halltype in self.all_halltypes:
                    for stru in self.structures(halltype):
                        mybases += 1
                mydronedbases = len(self.units(UnitTypeId.DRONE)) // 14
                mybases = min(mydronedbases, mybases)
                # danger
                danger = False
                for halltype in self.all_halltypes:
                    for stru in self.structures(halltype):
                        if stru.tag in self.last_health:
                            if stru.health < self.last_health[stru.tag]:
                                danger = True
                if self.nenemybases == 1:
                    if self.frame > 2.5 * self.minutes:
                        danger = True
                if self.nenemybases == 2:
                    if self.frame > 5 * self.minutes:
                        danger = True
                ene_worth = 0
                for tag in self.enemy_unit_mem:
                    (typ, pos) = self.enemy_unit_mem[tag]
                    if typ not in self.all_workertypes:
                        if typ not in {UnitTypeId.QUEEN, UnitTypeId.OVERLORD}:
                            ene_worth += self.worth(typ)
                my_worth = 0
                for unt in self.units:
                    typ = unt.type_id
                    if typ in self.all_armytypes:
                        if typ not in {UnitTypeId.QUEEN, UnitTypeId.OVERLORD}:
                            my_worth += self.worth(typ)
                if ene_worth >= my_worth + 1000:
                    danger = True
                if danger:
                    # choose plan
                    if self.vespene == 0:
                        if mybases == 1:
                            plan = self.Gameplan.ONEBASE_NOGAS
                        elif mybases == 2:
                            plan = self.Gameplan.TWOBASE_NOGAS
                        elif mybases >= 3:
                            plan = self.Gameplan.THREEBASE_NOGAS
                    else:
                        if mybases == 1:
                            plan = self.Gameplan.ONEBASE
                        elif mybases == 2:
                            plan = self.Gameplan.TWOBASE
                        elif mybases == 3:
                            plan = self.Gameplan.THREEBASE
                        elif mybases >= 4:
                            plan = self.Gameplan.FOURBASE
                    logger.info("Downgrading to " + plan.name)
                    await self._client.chat_send("Downgrading to " + plan.name, team_only=False)
                    self.set_gameplan(plan)
