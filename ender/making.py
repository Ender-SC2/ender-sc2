# making.py, Ender

import random
from loguru import logger

from ender.job import Job
from ender.map_if import Map_if
from ender.resources import Resources
from ender.strategy import Strategy
from ender.utils.point_utils import distance
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class Making(Map_if, Resources, Strategy):

    creation = {}  # per unittype the ability of making it. One source, so misses unburrows.
    #
    # upgrade_chain to start upgrades in this order (provided creatable)
    upgrade_chain = [
        UpgradeId.ZERGLINGMOVEMENTSPEED,
        UpgradeId.BURROW,
        UpgradeId.OVERLORDSPEED,
        UpgradeId.GLIALRECONSTITUTION,
        UpgradeId.ZERGLINGATTACKSPEED,
        UpgradeId.LURKERRANGE,
        UpgradeId.CENTRIFICALHOOKS,
        UpgradeId.NEURALPARASITE,
        UpgradeId.CHITINOUSPLATING,
        UpgradeId.EVOLVEGROOVEDSPINES,
        UpgradeId.ZERGFLYERARMORSLEVEL1,
        UpgradeId.ZERGFLYERARMORSLEVEL2,
        UpgradeId.ZERGFLYERARMORSLEVEL3,
        UpgradeId.ZERGFLYERWEAPONSLEVEL1,
        UpgradeId.ZERGFLYERWEAPONSLEVEL2,
        UpgradeId.ZERGFLYERWEAPONSLEVEL3,
        UpgradeId.ZERGMISSILEWEAPONSLEVEL1,
        UpgradeId.ZERGMELEEWEAPONSLEVEL1,
        UpgradeId.ZERGMISSILEWEAPONSLEVEL2,
        UpgradeId.ZERGMELEEWEAPONSLEVEL2,
        UpgradeId.ZERGGROUNDARMORSLEVEL1,
        UpgradeId.ZERGGROUNDARMORSLEVEL2,
        UpgradeId.ZERGMISSILEWEAPONSLEVEL3,
        UpgradeId.ZERGMELEEWEAPONSLEVEL3,
        UpgradeId.ZERGGROUNDARMORSLEVEL3,
        UpgradeId.EVOLVEMUSCULARAUGMENTS,
    ]
    __did_step0 = False
    somedrone = -2  # constant
    want_supply = True
    expansions = []  # of (pos,height,hasmin,hasgas,mybase,herbase,myblock,herblock,myarmy,herarmy)
    expansion_tried = {}  # per expansionpos: the frame of the last hatchery create try
    importance = {}  # When multiple claims, use importance
    subimportance = {}  # per armytype: between 0 and 20
    make_plan = {}  # result_plan - atleast_started. Can be changed for supplytricking.
    vespene_hist = 0  # sometimes gets the vespene value, to detect no mining
    minerals_hist = 0  # sometimes gets the minerals value, to detect no mining
    buildplan = {}  # per typ: (histag, buildpos, expiration)
    prewalkers = set()  # expanding with a drone prewalking
    expiration_of_builder = {}  # it is a temporal job
    experience = []  # walktime for prewalkers
    example = UnitTypeId.SPORECRAWLER  # for debugging, e.g. EXTRACTOR. To silence: SCV
    # emergency in common.py
    # supplytricking in common.py
    supplytrick_phase = "no"
    supplytrick_end = 0
    rallied = set()
    i_am_making_a = set()  # recently issued build commands
    i_am_making_a_building = set()  # recently issued build commands
    # current_expandings is in common.py. The expand positions with a walker or builder.
    #

    def __step0(self):
        #
        self.importance["overlord"] = 100
        self.importance["drone"] = 90
        self.importance["queen"] = 80
        self.importance["hive_building"] = 70
        self.importance["lone_building"] = 60
        self.importance["upgrade"] = 50
        self.importance["extractor"] = 40
        self.importance["hatchery"] = 30
        self.importance["army"] = 10  # leave room to add subimportance
        self.importance["sporespine"] = 0
        #
        for typ in self.all_armytypes:
            self.subimportance[typ] = 0
        self.subimportance[UnitTypeId.BROODLING] = 0  # do not wait for those
        self.subimportance[UnitTypeId.ZERGLING] = 1
        self.subimportance[UnitTypeId.QUEEN] = 2
        self.subimportance[UnitTypeId.ROACH] = 3
        self.subimportance[UnitTypeId.BANELING] = 4
        self.subimportance[UnitTypeId.INFESTOR] = 5
        self.subimportance[UnitTypeId.MUTALISK] = 6
        self.subimportance[UnitTypeId.SWARMHOSTMP] = 7
        self.subimportance[UnitTypeId.HYDRALISK] = 8
        self.subimportance[UnitTypeId.LURKERMP] = 9
        self.subimportance[UnitTypeId.OVERLORDTRANSPORT] = 10
        self.subimportance[UnitTypeId.RAVAGER] = 11
        self.subimportance[UnitTypeId.OVERSEER] = 12
        self.subimportance[UnitTypeId.CORRUPTOR] = 13
        self.subimportance[UnitTypeId.VIPER] = 14
        self.subimportance[UnitTypeId.BROODLORD] = 15
        self.subimportance[UnitTypeId.ULTRALISK] = 16
        #
        # creation
        for bartype in sc2.dicts.unit_research_abilities.RESEARCH_INFO:
            for martype in sc2.dicts.unit_research_abilities.RESEARCH_INFO[bartype]:
                abi = sc2.dicts.unit_research_abilities.RESEARCH_INFO[bartype][martype]["ability"]
                self.creation[martype] = abi
        for bartype in sc2.dicts.unit_train_build_abilities.TRAIN_INFO:
            for martype in sc2.dicts.unit_train_build_abilities.TRAIN_INFO[bartype]:
                abi = sc2.dicts.unit_train_build_abilities.TRAIN_INFO[bartype][martype]["ability"]
                self.creation[martype] = abi
        for typ in self.all_changelings:
            self.creation[typ] = AbilityId.BURROWDOWN_RAVAGER  # intentionally wrong
        self.creation[UnitTypeId.CHANGELING] = AbilityId.SPAWNCHANGELING_SPAWNCHANGELING
        self.creation[UnitTypeId.LURKERMPBURROWED] = AbilityId.BURROWDOWN_LURKER
        self.creation[UnitTypeId.ULTRALISKBURROWED] = AbilityId.BURROWDOWN_ULTRALISK
        self.creation[UnitTypeId.DRONEBURROWED] = AbilityId.BURROWDOWN_DRONE
        self.creation[UnitTypeId.CREEPTUMOR] = AbilityId.BUILD_CREEPTUMOR_TUMOR
        self.creation[UnitTypeId.OVERSEERSIEGEMODE] = AbilityId.MORPH_OVERSIGHTMODE
        self.creation[UnitTypeId.OVERSEER] = AbilityId.MORPH_OVERSEER
        self.creation[UnitTypeId.OVERLORDTRANSPORT] = AbilityId.MORPH_OVERLORDTRANSPORT
        self.creation[UnitTypeId.QUEENBURROWED] = AbilityId.BURROWDOWN_QUEEN
        self.creation[UnitTypeId.RAVAGERBURROWED] = AbilityId.BURROWDOWN_RAVAGER
        self.creation[UnitTypeId.ROACHBURROWED] = AbilityId.BURROWDOWN_ROACH
        self.creation[UnitTypeId.SPINECRAWLERUPROOTED] = AbilityId.SPINECRAWLERUPROOT_SPINECRAWLERUPROOT
        self.creation[UnitTypeId.SPORECRAWLERUPROOTED] = AbilityId.SPORECRAWLERUPROOT_SPORECRAWLERUPROOT
        self.creation[UnitTypeId.SWARMHOSTBURROWEDMP] = AbilityId.BURROWDOWN_SWARMHOST
        self.creation[UnitTypeId.ULTRALISKBURROWED] = AbilityId.BURROWDOWN_ULTRALISK
        self.creation[UnitTypeId.ZERGLINGBURROWED] = AbilityId.BURROWDOWN_ZERGLING
        self.creation[UnitTypeId.BANELINGBURROWED] = AbilityId.BURROWDOWN_BANELING
        self.creation[UnitTypeId.LOCUSTMP] = AbilityId.EFFECT_LOCUSTSWOOP
        self.creation[UnitTypeId.BROODLING] = AbilityId.BURROWDOWN_RAVAGER  # intentionally wrong
        #
        self.init_expansions()
        self.next_expansion = self.nowhere
        self.choose_next_expansion()

    async def on_step(self, iteration: int):
        await Map_if.on_step(self, iteration)
        await Resources.on_step(self, iteration)
        await Strategy.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.do_make_plan()
        #
        for typ in self.all_armytypes:
            await self.make_army_unit(typ)
        await self.expand()
        await self.build_evolutionchambers()
        for typ in {
            UnitTypeId.EXTRACTOR,
            UnitTypeId.SPAWNINGPOOL,
            UnitTypeId.ROACHWARREN,
            UnitTypeId.BANELINGNEST,
            UnitTypeId.LAIR,
            UnitTypeId.HIVE,
            UnitTypeId.INFESTATIONPIT,
            UnitTypeId.HYDRALISKDEN,
            UnitTypeId.LURKERDENMP,
            UnitTypeId.SPIRE,
            UnitTypeId.NYDUSNETWORK,
            UnitTypeId.GREATERSPIRE,
            UnitTypeId.ULTRALISKCAVERN,
            UnitTypeId.SPORECRAWLER,
            UnitTypeId.SPINECRAWLER,
        }:
            await self.build_structure(typ.name, typ)
        await self.make_overlords()
        for upg in self.all_upgrades:
            await self.upgrade(upg)
        await self.make_drones()
        # await self.prewalk()
        await self.builder_admin()
        await self.go_walk()
        await self.downroot()
        await self.plant_freespine()
        await self.destroyed()
        await self.do_supplytrick()
        await self.rallypoints()
        await self.check_making()
        #
        if self.frame % 17 == 16:
            self.vespene_hist = self.vespene
            self.minerals_hist = self.minerals
        #
        await self.calc_groupclaim()

    async def check_making(self):
        if self.function_listens("check_making", 9):
            todel = set()
            for tuple in self.i_am_making_a:
                (typ, started, wasmaking) = tuple
                if self.started(typ) > wasmaking:
                    todel.add(tuple)
                if self.frame >= started + self.seconds:
                    todel.add(tuple)
                    if self.started(typ) == 0:  # conservative
                        logger.info("Error making a " + typ.name)
            self.i_am_making_a -= todel
            for tuple in todel:
                (typ, started, wasmaking) = tuple
                self.unclaim_resources(typ)
            #
            todel = set()
            for tuple in self.i_am_making_a_building:
                (typ, started, histag, buildpos, wasmaking) = tuple
                if self.started(typ) > wasmaking:
                    todel.add(tuple)
                if self.frame >= started + 4 * self.seconds:
                    if self.started(typ) == 0:  # conservative
                        logger.info("Error making a " + typ.name + ", retrying.")
                        self.makecommand_building(typ, histag, buildpos)
                if self.frame >= started + 5 * self.seconds:
                    todel.add(tuple)
            self.i_am_making_a_building -= todel
            for tuple in todel:
                (typ, started, histag, buildpos, wasmaking) = tuple
                self.unclaim_resources(typ)

    def now_make_a(self, typ):
        # within the protocol, just after check_resources
        wasmaking = self.started(typ)
        self.i_am_making_a.add((typ, self.frame, wasmaking))
        self.makecommand(typ)

    def makecommand(self, typ):
        # called by now_make_a
        if typ in {UnitTypeId.DRONE, UnitTypeId.OVERLORD}:
            larf = self.larva.random
            larf.train(typ)
            self.listenframe_of_unit[larf.tag] = self.frame + 5
        if typ in self.all_armytypes:
            crea = self.creator[typ]
            for unt in self.units(crea) | self.structures(crea):
                if unt.tag in self.resourcetags(typ):
                    justone = unt
            if crea in {UnitTypeId.LARVA}:
                larf = self.larva.random
                larf.train(typ)
                self.listenframe_of_unit[larf.tag] = self.frame + 5
            elif crea == UnitTypeId.OVERSEER:
                if typ == UnitTypeId.CHANGELING:
                    justone(AbilityId.SPAWNCHANGELING_SPAWNCHANGELING)
                    self.listenframe_of_unit[justone.tag] = self.frame + 5
                else:
                    justone.train(typ)
                    self.listenframe_of_unit[justone.tag] = self.frame + 5
            elif typ == UnitTypeId.QUEEN:
                # queenhatchery, not just any hatchery.
                for halltype in self.all_halltypes:
                    for hall in self.structures(halltype).ready.idle:
                        if hall.tag not in self.queen_of_hall:
                            justone = hall
                justone.train(typ)
                self.listenframe_of_structure[justone.tag] = self.frame + 5
                self.queen_of_hall[justone.tag] = self.notag
            elif len(self.structures(crea).ready.idle) > 0:
                # best at a distance
                bestdist = -1
                for unt in self.structures(crea).idle:
                    if unt.tag in self.resourcetags(typ):
                        itsdist = 9999
                        for que in self.units(typ):
                            dist = distance(que.position, unt.position)
                            itsdist = min(dist, itsdist)
                        if itsdist > bestdist:
                            bestdist = itsdist
                            bestunt = unt
                bestunt.train(typ)
                self.listenframe_of_structure[bestunt.tag] = self.frame + 5
            elif crea == UnitTypeId.SWARMHOSTMP:
                justone.train(typ)
                self.cooldown_sh[justone.tag] = self.frame + 43 * self.seconds + 10
                self.listenframe_of_unit[justone.tag] = self.frame + 5
            else:
                justone.train(typ)
                self.listenframe_of_unit[justone.tag] = self.frame + 5
        if typ in self.all_upgrades:
            crea = self.creator[typ]
            for unt in self.structures(crea).idle:
                if unt.tag in self.resourcetags(typ):
                    justone = unt
            justone(self.creation[typ])
            self.listenframe_of_structure[justone.tag] = self.frame + 5

    def now_make_a_building(self, typ, histag, buildpos):
        # within the protocoll, just after check_resources
        wasmaking = self.started(typ)
        self.i_am_making_a_building.add((typ, self.frame, histag, buildpos, wasmaking))
        self.makecommand_building(typ, histag, buildpos)

    def makecommand_building(self, typ, histag, buildpos):
        # called by now_make_a_building
        size = self.size_of_structure[typ]
        if histag in self.living:
            self.set_job_of_unittag(histag, Job.BUILDER)
            self.expiration_of_builder[histag] = self.frame + 8 * self.seconds  # shortens it
        if typ == UnitTypeId.EXTRACTOR:
            for gey in self.freegeysers:
                if gey.position == buildpos:
                    if self.map_can_build(buildpos, size):
                        for him in self.units(UnitTypeId.DRONE):
                            if him.tag == histag:
                                self.map_build(buildpos, size, typ)
                                him.build(typ, gey)
        elif typ == UnitTypeId.HATCHERY:
            if self.map_can_build(buildpos, size):
                for him in self.units(UnitTypeId.DRONE):
                    if him.tag == histag:
                        self.map_build(buildpos, size, typ)
                        him.build(typ, buildpos)
        elif typ == UnitTypeId.GREATERSPIRE:
            for stru in self.structures(UnitTypeId.SPIRE).ready.idle:
                if stru.position == buildpos:
                    stru.train(typ)
        elif typ == UnitTypeId.LAIR:
            for stru in self.structures(UnitTypeId.HATCHERY).ready.idle:
                if stru.position == buildpos:
                    stru.train(typ)
        elif typ == UnitTypeId.HIVE:
            for stru in self.structures(UnitTypeId.LAIR).ready.idle:
                if stru.position == buildpos:
                    stru.train(typ)
        else:
            if self.map_can_build(buildpos, size):
                for him in self.units(UnitTypeId.DRONE):
                    if him.tag == histag:
                        self.map_build(buildpos, size, typ)
                        him.build(typ, buildpos)

    async def do_make_plan(self):
        self.make_plan = self.zero_plan.copy()
        for thing in self.result_plan:
            amount = self.result_plan[thing]
            if amount > 0:
                tomake = amount - self.atleast_started(thing)
                if tomake > 0:
                    self.make_plan[thing] = tomake
        if self.supplytricking:
            self.make_plan[UnitTypeId.ZERGLING] += 40
            self.make_plan[UnitTypeId.SPORECRAWLER] += 20
        # log
        for thing in self.make_plan:
            amount = self.make_plan[thing]
            if amount > 0:
                pass
                # logger.info('I must still make ' + str(amount) + ' ' + thing.name)

    async def calc_groupclaim(self):
        self.zero_groupclaim()
        for thing in self.make_plan:
            amount = self.make_plan[thing]
            if amount > 0:
                self.add_groupclaim(thing, amount)

    def started(self, thing) -> int:
        sol = 0
        for claim in self.orderdelay:
            (typ, resources, importance, expiration) = claim
            if typ == thing:
                sol += 1
        cocoon = self.creator[thing]
        if cocoon == UnitTypeId.LARVA:
            cocoon = UnitTypeId.EGG  # be aware: tagchange on ending cocoon state.
            # an egg can become different units; check its order.ability.exact_id
        if thing == UnitTypeId.OVERLORDTRANSPORT:
            cocoon = UnitTypeId.TRANSPORTOVERLORDCOCOON
            return sol + len(self.units(cocoon))
        if thing == UnitTypeId.OVERSEER:
            cocoon = UnitTypeId.OVERLORDCOCOON
            return sol + len(self.units(cocoon))
        if thing == UnitTypeId.LURKERMP:
            cocoon = UnitTypeId.LURKERMPEGG
            return sol + len(self.units(cocoon))
        if thing == UnitTypeId.BROODLORD:
            cocoon = UnitTypeId.BROODLORDCOCOON
            return sol + len(self.units(cocoon))
        if thing == UnitTypeId.RAVAGER:
            cocoon = UnitTypeId.RAVAGERCOCOON
            return sol + len(self.units(cocoon))
        if thing == UnitTypeId.BANELING:
            cocoon = UnitTypeId.BANELINGCOCOON  # be aware: tagchange on ending cocoon state.
            return sol + len(self.units(cocoon))
        if thing == UnitTypeId.CHANGELING:
            # can change automatic
            for chtyp in self.all_changelings:
                for unt in self.units(chtyp):
                    if unt.age_in_frames < self.seconds:
                        sol += 1
        creation = self.creation[thing]
        for unt in self.units(cocoon) + self.structures(cocoon):
            for order in unt.orders:
                if creation == order.ability.exact_id:
                    sol += 1
        return sol

    def atleast_started(self, thing) -> int:
        am = 0
        am += self.started(thing)
        if thing in self.state.upgrades:
            am += 1
        if type(thing) == UnitTypeId:
            am += len(self.structures(thing))
            am += len(self.units(thing))
        if thing == UnitTypeId.HATCHERY:
            am += len(self.structures(UnitTypeId.LAIR))
            am += len(self.structures(UnitTypeId.HIVE))
        if thing == UnitTypeId.LAIR:
            am += len(self.structures(UnitTypeId.HIVE))
        if thing == UnitTypeId.SPIRE:
            am += len(self.structures(UnitTypeId.GREATERSPIRE))
        if thing == UnitTypeId.EXTRACTOR:
            am += len(self.structures(UnitTypeId.EXTRACTORRICH))
        for mor in self.morph:
            if self.morph[mor] == thing:
                am += len(self.units(mor))
        return am

    def atleast_some_started(self, thing) -> bool:
        # to speed up
        if thing in self.state.upgrades:
            return True
        if type(thing) == UnitTypeId:
            if len(self.structures(thing)) > 0:
                return True
            if len(self.units(thing)) > 0:
                return True
        if thing == UnitTypeId.HATCHERY:
            if len(self.structures(UnitTypeId.LAIR)) > 0:
                return True
            if len(self.structures(UnitTypeId.HIVE)) > 0:
                return True
        if thing == UnitTypeId.LAIR:
            if len(self.structures(UnitTypeId.HIVE)) > 0:
                return True
        if thing == UnitTypeId.SPIRE:
            if len(self.structures(UnitTypeId.GREATERSPIRE)) > 0:
                return True
        if thing == UnitTypeId.EXTRACTOR:
            if len(self.structures(UnitTypeId.EXTRACTORRICH)) > 0:
                return True
        if self.started(thing) > 0:
            return True
        return False

    async def expand(self):
        if self.next_expansion == self.nowhere:
            if self.frame % 17 == 16:
                self.choose_next_expansion()
        typ = UnitTypeId.HATCHERY
        await self.build_structure("hatc", typ)

    async def make_overlords(self):
        queens = len(self.units(UnitTypeId.QUEEN))
        need_spare = 2 + 3 * (self.nbases - 1) + 2 * queens
        soon_supply = 0  # may be too high (for some seconds)
        soon_supply += 6 * self.started(UnitTypeId.OVERLORD)
        for stru in self.structures(UnitTypeId.HATCHERY):
            if stru not in self.structures(UnitTypeId.HATCHERY).ready:
                if stru.build_progress > 0.75:  # about 18 seconds
                    soon_supply += 6
        if (self.supply_left + soon_supply < need_spare) and (self.supply_cap + soon_supply < 220):
            importance = self.importance["overlord"]
            importance += 1000  # overlords are implicit in make_plan
            typ = UnitTypeId.OVERLORD
            self.claim_resources(typ, importance)
            if self.check_resources(typ, importance):
                self.now_make_a(typ)

    async def make_army_unit(self, typ):
        if self.function_listens("make_" + typ.name, 10):
            if typ == self.example:
                if len(self.structures(UnitTypeId.HYDRALISKDEN).ready) > 0:
                    breakthis = True
            if not self.structures.of_type(UnitTypeId.SPAWNINGPOOL).ready.exists:
                if typ == self.example:
                    logger.info("example " + self.example.name + " waits for spawningpool")
                return
            if typ in {UnitTypeId.BROODLING, UnitTypeId.LOCUSTMP, UnitTypeId.LARVA}:  # made automatic
                if typ == self.example:
                    logger.info("example " + self.example.name + " has no explict making")
                return
            if typ in self.all_changelings:  # made automatic
                if typ != UnitTypeId.CHANGELING:
                    if typ == self.example:
                        logger.info("example " + self.example.name + " has no explict making")
                    return
            if self.check_wannado_unit(typ):
                if typ == UnitTypeId.QUEEN:
                    importance = self.importance["queen"]
                else:
                    importance = self.importance["army"] + self.subimportance[typ]
                # increase importance if in make_plan
                if (self.make_plan[typ] > 0) or ((typ == UnitTypeId.QUEEN) and self.auto_queen):
                    importance += 1000
                for (emerg_typ, emerg_pos) in self.emergency:
                    if emerg_typ == typ:
                        importance = 2000
                        break
                self.claim_resources(typ, importance)
                if self.check_resources(typ, importance):
                    self.now_make_a(typ)
                else:
                    if typ == self.example:
                        logger.info("example " + self.example.name + " waits for resources")

    async def build_evolutionchambers(self):
        if self.function_listens("build_evos", 30):
            it = UnitTypeId.EVOLUTIONCHAMBER
            have = self.atleast_started(it)
            if have == 0:
                await self.build_structure("evo1", it)
            elif have == 1:
                if self.nbases >= 5:
                    await self.build_structure("evo2", it)
            elif have == 2:
                if self.supply_used >= 190:
                    await self.build_structure("evo3", it)

    async def build_structure(self, name, typ):
        patience = self.seconds
        if self.supplytricking:
            patience = 5
        if self.function_listens("build_structure_" + name, patience):
            if self.check_wannado_structure(typ):
                if typ == UnitTypeId.HATCHERY:
                    importance = self.importance["hatchery"]
                elif typ == UnitTypeId.EXTRACTOR:
                    importance = self.importance["extractor"]
                elif typ in self.all_sporetypes:
                    importance = self.importance["sporespine"]
                elif typ in {
                    UnitTypeId.LAIR,
                    UnitTypeId.HIVE,
                    UnitTypeId.INFESTATIONPIT,
                    UnitTypeId.SPIRE,
                    UnitTypeId.GREATERSPIRE,
                    UnitTypeId.SPAWNINGPOOL,
                }:
                    importance = self.importance["hive_building"]
                else:
                    importance = self.importance["lone_building"]
                if self.make_plan[typ] > 0:
                    importance += 1000
                for (emerg_typ, emerg_pos) in self.emergency:
                    if emerg_typ == typ:
                        importance = 2000
                        break
                self.claim_resources(typ, importance)
                if typ not in self.buildplan:
                    size = self.size_of_structure[typ]
                    if typ == UnitTypeId.EXTRACTOR:
                        gey = random.choice(self.freegeysers)
                        pos = gey.position
                        if self.map_can_plan_gas(pos, size):
                            self.map_plan_gas(pos, size)
                            expiration = self.frame + self.minutes
                            self.buildplan[typ] = (self.somedrone, pos, expiration)
                    elif typ == UnitTypeId.HATCHERY:
                        pos = self.next_expansion
                        if self.map_can_plan(pos, size):
                            self.map_plan(pos, size)
                            expiration = self.frame + 2 * self.minutes
                            self.buildplan[typ] = (self.somedrone, pos, expiration)
                        self.expansion_tried[pos] = self.frame
                        self.choose_next_expansion()
                    elif typ == UnitTypeId.GREATERSPIRE:
                        if len(self.structures(UnitTypeId.SPIRE).ready.idle) > 0:
                            stru = self.structures(UnitTypeId.SPIRE).ready.idle.random
                            pos = stru.position
                            expiration = self.frame + self.minutes
                            self.buildplan[typ] = (self.notag, pos, expiration)
                    elif typ == UnitTypeId.LAIR:
                        if len(self.structures(UnitTypeId.HATCHERY).ready.idle) > 0:
                            stru = self.structures(UnitTypeId.HATCHERY).ready.idle.random
                            pos = stru.position
                            expiration = self.frame + self.minutes
                            self.buildplan[typ] = (self.somedrone, pos, expiration)
                    elif typ == UnitTypeId.HIVE:
                        if len(self.structures(UnitTypeId.LAIR).ready.idle) > 0:
                            stru = self.structures(UnitTypeId.LAIR).ready.idle.random
                            pos = stru.position
                            expiration = self.frame + self.minutes
                            self.buildplan[typ] = (self.notag, pos, expiration)
                    elif typ in self.all_sporetypes:
                        abasepos = self.structures(UnitTypeId.HATCHERY).random.position
                        # give extra chance to offensive placement
                        if distance(abasepos, self.ourmain) < distance(abasepos, self.enemymain):
                            abasepos = self.structures(UnitTypeId.HATCHERY).random.position
                        pos = abasepos.towards(self.map_center, 3)
                        # for supplytrick, place spores under a miner
                        if self.supplytricking:
                            for drone in self.units(UnitTypeId.DRONE):
                                if self.job_of_unit(drone) == Job.MIMMINER:
                                    gooddrone = drone
                            pos = gooddrone.position
                            self.set_job_of_unit(gooddrone, Job.UNCLEAR)
                        # emergency position
                        emergency = False
                        for (emerg_typ, emerg_pos) in self.emergency:
                            if emerg_typ == typ:
                                logger.info(f"{emerg_typ} at {emerg_pos}")
                                pos = emerg_pos
                                emergency = True
                                break
                        if emergency:
                            self.emergency.remove((typ, pos))
                        pos = self.map_around(pos, size)
                        self.map_plan(pos, size)
                        expiration = self.frame + self.minutes
                        self.buildplan[typ] = (self.somedrone, pos, expiration)
                    else:
                        abasepos = self.structures(UnitTypeId.HATCHERY).ready.random.position
                        pos = abasepos.towards(self.map_center, 5)
                        pos = self.map_around(pos, size)
                        self.map_plan(pos, size)
                        expiration = self.frame + self.minutes
                        self.buildplan[typ] = (self.somedrone, pos, expiration)
                if typ in self.buildplan:
                    if self.walk_finished(typ):
                        (histag, buildpos, expiration) = self.buildplan[typ]
                        if expiration > self.frame + self.minutes:
                            expiration = self.frame + self.minutes
                            self.buildplan[typ] = (histag, buildpos, expiration)
                        if self.check_resources(typ, importance):
                            self.now_make_a_building(typ, histag, buildpos)
                            del self.buildplan[typ]

    def walk_finished(self, typ) -> bool:
        (histag, buildpos, expiration) = self.buildplan[typ]
        if histag == self.notag:
            return True
        for drone in self.units(UnitTypeId.DRONE):
            if drone.tag == histag:
                if distance(drone.position, buildpos) < 4:
                    return True
        return False

    async def go_walk(self):
        # fill somedrone if you decide to start walking
        mimminers = self.job_count(Job.MIMMINER)
        gasminers = self.job_count(Job.GASMINER)
        for typ in self.buildplan:
            (histag, buildpos, expir) = self.buildplan[typ]
            if histag == self.somedrone:
                # get closest drone (not yet a walker)
                bestdist = 99999
                for drone in self.units(UnitTypeId.DRONE):
                    tag = drone.tag
                    if self.job_of_unittag(tag) not in {Job.WALKER, Job.BUILDER}:
                        dist = distance(drone.position, buildpos)
                        if dist < bestdist:
                            bestdist = dist
                            bestdrone = drone
                if bestdist < 99999:
                    drone = bestdrone
                    tag = drone.tag
                    dist = distance(drone.position, buildpos)
                    mimgap = self.mineral_gap(typ)
                    gasgap = self.vespene_gap(typ)
                    if mimminers > 0:
                        mimwait = mimgap / mimminers
                    elif mimgap > 0:
                        mimwait = 99999
                    else:
                        mimwait = 0
                    if gasminers > 0:
                        gaswait = gasgap / gasminers
                    elif gasgap > 0:
                        gaswait = 99999
                    else:
                        gaswait = 0
                    resourcewait = max(mimwait, gaswait)
                    if resourcewait < dist * 0.5:
                        self.set_job_of_unit(drone, Job.WALKER)
                        if expir > self.frame + self.minutes:  # lower to minute
                            expir = self.frame + self.minutes
                        self.expiration_of_builder[tag] = expir
                        drone.move(buildpos)
                        self.buildplan[typ] = (tag, buildpos, expir)
                        self.current_expandings[buildpos] = tag

    def we_finished_a(self, thing) -> bool:
        if thing in self.state.upgrades:
            return True
        if type(thing) == UnitTypeId:
            if len(self.structures(thing).ready) > 0:
                return True
            if len(self.units(thing)) > 0:
                return True
        if thing == UnitTypeId.HATCHERY:
            if len(self.structures(UnitTypeId.LAIR)) > 0:
                return True
            if len(self.structures(UnitTypeId.HIVE)) > 0:
                return True
        if thing == UnitTypeId.LAIR:
            if len(self.structures(UnitTypeId.HIVE)) > 0:
                return True
        if thing == UnitTypeId.SPIRE:
            if len(self.structures(UnitTypeId.GREATERSPIRE)) > 0:
                return True
        if thing == UnitTypeId.EXTRACTOR:
            if len(self.structures(UnitTypeId.EXTRACTORRICH)) > 0:
                return True
        for mor in self.morph:
            if self.morph[mor] == thing:
                if len(self.units(mor)) > 0:
                    return True
        return False

    def tech_check(self, the_thing) -> bool:
        creator = self.creator[the_thing]
        if not self.we_finished_a(creator):
            return False
        for tech_chain in self.tech_chains:
            if the_thing in tech_chain:
                canstart = True
                seen = False
                for thing in tech_chain:
                    seen = seen or (thing == the_thing)
                    if not seen:  # before
                        if not self.we_finished_a(thing):
                            canstart = False
                if not canstart:
                    return False
        if self.resource_cost[the_thing][self.Resource.VESPENE] > 0:
            if self.vespene == 0:
                return False
        return True

    def check_wannado_unit(self, unty) -> bool:
        if not self.tech_check(unty):
            return False
        #
        if unty == UnitTypeId.QUEEN:
            if self.auto_queen:
                now = False
                for typ in self.all_halltypes:
                    for base in self.structures(typ).ready.idle:
                        if base.tag not in self.queen_of_hall:
                            now = True
                if not now:
                    if unty == self.example:
                        logger.info("example " + self.example.name + " waits for hall without queen")
                    return False
        #
        max_count = 200
        if unty == UnitTypeId.DRONE:
            max_count = self.supplycap_drones
        if unty == UnitTypeId.QUEEN:
            max_count = self.supplycap_queens / 2
        if unty == UnitTypeId.OVERSEERSIEGEMODE:
            max_count = 5
        if unty == UnitTypeId.OVERLORD:
            max_count = 35
        if unty in {UnitTypeId.OVERSEER, UnitTypeId.OVERLORDTRANSPORT}:
            max_count = 15
        if not (self.atleast_started(unty) < max_count):
            if unty == self.example:
                logger.info("example " + self.example.name + " is stuck on max_count")
            return False
        return True

    def check_wannado_structure(self, unty) -> bool:
        # tech demand
        if self.tech_requirement_progress(unty) < 0.5:
            if unty == self.example:
                logger.info("example " + self.example.name + " waits for tech")
            return False
        # the chosen amount of needed hatcheries
        if len(self.structures(UnitTypeId.HATCHERY)) < self.needhatches[unty]:  # just-started hatcheries
            # this shouldnt get everything stuck forever
            if self.minerals < 2000:
                if unty == self.example:
                    logger.info("example " + self.example.name + " waits for hatches")
                    logger.info(str(len(self.structures(UnitTypeId.HATCHERY))), " ", str(self.needhatches[unty]))
                return False
        # building_order.  E.g. [hatch pool hatch extractor]
        if unty in self.building_order:
            frontdone = True
            ordered = {}
            for build in self.building_order:
                if frontdone:
                    if build in ordered:
                        ordered[build] += 1
                    else:
                        ordered[build] = 1
                    if self.atleast_started(build) < ordered[build]:
                        # build is at the front
                        frontdone = False
                        if unty != build:
                            return False
        # the chosen structype order
        if unty in self.structype_order:
            seen = False
            for thing in self.structype_order:
                seen = seen or (thing == unty)
                if not seen:  # before
                    if not self.atleast_some_started(thing):
                        if (self.make_plan[thing] > 0) or (self.make_plan[unty] == 0):
                            if unty == self.example:
                                logger.info(
                                    "example " + self.example.name + " waits for structype_order " + thing.name
                                )
                            return False
        # the chosen maximum amount
        max_count = 1
        if unty in {UnitTypeId.HATCHERY, UnitTypeId.EXTRACTOR}:
            max_count = 99
        if unty in {UnitTypeId.EVOLUTIONCHAMBER, UnitTypeId.SPAWNINGPOOL}:
            if len(self.structures(UnitTypeId.HATCHERY)) >= 4:
                max_count = 2
        if unty in self.all_sporetypes:
            max_count = 70
        if not (self.atleast_started(unty) < max_count):
            if unty == self.example:
                logger.info("example " + self.example.name + " is at maxcount.")
            return False
        # free geyser
        if unty == UnitTypeId.EXTRACTOR:
            if len(self.freegeysers) == 0:
                return False
        return True

    def i_could_upgrade(self, typ, importance) -> bool:
        if not self.atleast_some_started(typ):
            if self.tech_check(typ):
                creator = self.creator[typ]
                resource = self.resource_of_buildingtype[creator]
                if self.have_free_resource(resource, importance):
                    return True
        return False

    def check_wannado_upgrade(self, upg, importance) -> bool:
        if self.i_could_upgrade(upg, importance):
            canstart = True
            seen = False
            for thing in self.upgrade_chain:
                seen = seen or (thing == upg)
                if not seen:  # before
                    if self.i_could_upgrade(thing, importance):
                        logger.info("upgrade " + thing.name + " makes wait " + upg.name)
                        canstart = False
            if canstart:
                return True
        #
        return False

    async def upgrade(self, typ):
        if self.function_listens("upgrade_" + typ.name, 2 * self.seconds):
            if typ == UpgradeId.EVOLVEGROOVEDSPINES:
                breaktodebug = True
            importance = self.importance["upgrade"]
            if (self.make_plan[typ] > 0) or self.auto_upgrade:
                importance += 1000
            if self.check_wannado_upgrade(typ, importance):
                self.claim_resources(typ, importance)
                if self.check_resources(typ, importance):
                    self.now_make_a(typ)

    async def make_drones(self):
        if self.function_listens("make_drones", self.seconds):
            typ = UnitTypeId.DRONE
            if self.check_wannado_unit(typ):
                lategame_max = 3 * len(self.extractors) + 2 * len(self.mineral_field) + 3
                if self.atleast_started(typ) < lategame_max:
                    # opening can delay making drones
                    delay = False
                    if self.wave_count == 0:
                        if len(self.opening) > 0:
                            todel = False
                            (kind, kind_am, thing, thing_am) = self.opening[0]
                            if kind == "supply":
                                if self.supply_used >= kind_am:
                                    if self.atleast_started(thing) >= thing_am:
                                        todel = True
                                    else:
                                        delay = True
                            if todel:
                                del self.opening[0]
                    if not delay:
                        importance = self.importance["drone"]
                        if self.make_plan[typ] > 0:
                            importance += 1000
                        self.claim_resources(typ, importance)
                        if self.check_resources(typ, importance):
                            self.now_make_a(typ)

    def init_expansions(self):
        self.expansions = []
        for pos in self.expansion_locations_list:
            gridpos = Point2((round(pos.x - 0.5), round(pos.y - 0.5)))
            height = self.game_info.terrain_height[gridpos]
            hasmin = True
            hasgas = True
            mybase = pos == self.ourmain
            herbase = pos == self.enemymain
            myblock = False
            herblock = False
            myarmy = False
            herarmy = False
            self.expansions.append((pos, height, hasmin, hasgas, mybase, herbase, myblock, herblock, myarmy, herarmy))

    def choose_next_expansion(self):
        # update info
        for exix in range(0, len(self.expansions)):
            expansion = self.expansions[exix]
            (pos, height, hasmin, hasgas, mybase, herbase, myblock, herblock, myarmy, herarmy) = expansion
            mybase = False
            herbase = False
            for halltype in self.all_halltypes:
                for stru in self.structures(halltype):
                    dist = distance(stru.position, pos)
                    if dist < 3:
                        mybase = True
                for postag in self.enemy_struc_mem:
                    (enetyp, enepos) = self.enemy_struc_mem[postag]
                    if enetyp == halltype:
                        dist = distance(enepos, pos)
                        if dist < 3:
                            herbase = True
            expansion = (pos, height, hasmin, hasgas, mybase, herbase, myblock, herblock, myarmy, herarmy)
            self.expansions[exix] = expansion
        # choose expansionposition with highest evalu
        bestevalu = -99999
        bestpos = self.nowhere
        for expansion in self.expansions:
            (pos, height, hasmin, hasgas, mybase, herbase, myblock, herblock, myarmy, herarmy) = expansion
            if (not herbase) and (not mybase):
                if hasgas or hasmin:
                    ago = 99999
                    if pos in self.expansion_tried:
                        ago = self.frame - self.expansion_tried[pos]
                    if ago >= 25 * self.seconds:
                        evalu = 0
                        evalu += height
                        if self.nbases == 1:
                            evalu -= distance(self.ourmain, pos)
                        if herblock:
                            evalu -= 10
                        if herarmy:
                            evalu -= 50
                        if myarmy:
                            evalu += 50
                        #
                        if evalu > bestevalu:
                            bestevalu = evalu
                            bestpos = pos
        self.next_expansion = bestpos
        logger.info("next expansion " + str(bestpos.x) + "," + str(bestpos.y))

    async def builder_admin(self):
        if self.function_listens("builder_admin", 17):
            # current_expandings
            todel = set()
            for pos in self.current_expandings:
                tag = self.current_expandings[pos]
                seen = False
                for unt in self.workers:
                    if unt.tag == tag:
                        if self.job_of_unit(unt) in [Job.WALKER, Job.BUILDER]:
                            seen = True
                if not seen:
                    todel.add(pos)
            for pos in todel:
                del self.current_expandings[pos]
            # buildplan
            todel = set()
            for typ in self.buildplan:
                (histag, buildpos, expiration) = self.buildplan[typ]
                if self.frame >= expiration:
                    todel.add(typ)
            for typ in todel:
                (histag, buildpos, expiration) = self.buildplan[typ]
                del self.buildplan[typ]
                if histag in self.living:
                    if self.job_of_unittag(histag) in [Job.WALKER, Job.BUILDER]:
                        self.set_job_of_unittag(histag, Job.UNCLEAR)
            # expiration_of_builder
            for unt in self.units(UnitTypeId.DRONE):
                if self.job_of_unit(unt) in [Job.WALKER, Job.BUILDER]:
                    if self.frame >= self.expiration_of_builder[unt.tag]:
                        self.set_job_of_unit(unt, Job.UNCLEAR)
            # the builder may still work after the buildplan is deleted

    async def prewalk(self):
        if self.function_listens("prewalk", 10):
            hatchclaim = False
            for claim in self.claims:
                (typ, resources, importance, expiration) = claim
                if typ == UnitTypeId.HATCHERY:
                    hatchclaim = True
            if hatchclaim:
                pos = self.next_expansion
                if pos not in self.prewalkers:
                    self.init_experience()
                    walkframe = 0
                    ix = len(self.prewalkers)
                    if ix < len(self.experience):
                        walkframe = self.experience[ix]
                    if self.frame > walkframe:
                        clodist = 99999
                        bestunt = None
                        for unt in self.units(UnitTypeId.DRONE):
                            if self.job_of_unit(unt) in [Job.UNCLEAR, Job.MIMMINER]:
                                dist = distance(unt.position, pos)
                                if dist < clodist:
                                    clodist = dist
                                    bestunt = unt
                        if bestunt:
                            unt = bestunt
                            self.prewalkers.add(pos)
                            self.set_job_of_unit(unt, Job.WALKER)
                            unt.move(pos)
                            self.expiration_of_builder[unt.tag] = self.frame + self.minutes
                            self.current_expandings[pos] = unt.tag

    def init_experience(self):
        if len(self.experience) == 0:
            self.experience.append(900)
            self.experience.append(1650)
            self.experience.append(5200)

    async def downroot(self):
        if self.function_listens("downroot", 10):
            for typ in {UnitTypeId.SPINECRAWLERUPROOTED, UnitTypeId.SPORECRAWLERUPROOTED}:
                for stru in self.structures(typ).idle:
                    tag = stru.tag
                    if self.frame >= self.listenframe_of_structure[tag]:
                        if tag in self.to_root:
                            self.to_root.remove(tag)
                            if typ == UnitTypeId.SPINECRAWLERUPROOTED:
                                down = AbilityId.SPINECRAWLERROOT_SPINECRAWLERROOT
                            else:
                                down = AbilityId.SPORECRAWLERROOT_SPORECRAWLERROOT
                            pos = stru.position
                            size = 2
                            pos = self.map_around(pos, size)
                            if self.map_can_plan(pos, size):
                                self.map_plan(pos, size)
                                self.map_build_nodel(pos, size)
                                stru(down, pos)
                                self.listenframe_of_structure[stru.tag] = self.frame + self.seconds * 10

    async def plant_freespine(self):
        if self.function_listens("plant_freespine", 11):
            for unt in self.units(UnitTypeId.DRONE):
                if self.job_of_unit(unt) == Job.FREESPINE:
                    if self.listenframe_of_unit[unt.tag] < self.frame:
                        if self.minerals >= 100:
                            pos = unt.position
                            size = 2
                            pos = self.map_around(pos, size)
                            if self.map_can_plan(pos, size):
                                self.map_plan(pos, size)
                                self.map_build_nodel(pos, size)
                                unt.build(UnitTypeId.SPINECRAWLER, pos)
                                self.listenframe_of_unit[unt.tag] = self.frame + 4 * self.seconds

    async def destroyed(self):
        for stru in self.structures:
            if stru.tag in self.last_health:
                if stru.health < 0.67 * self.last_health[stru.tag]:
                    stru(AbilityId.CANCEL_BUILDINPROGRESS)

    async def do_supplytrick(self):
        if self.function_listens("do_supplytrick", 10):
            # logger.info(self.supplytrick_phase)
            if self.supplytrick_phase == "no":
                if 195 <= self.supply_used <= 200:
                    # A zerglingpair temporarily costs 125; 2500 = 125 * 20; 20 zerglingpairs
                    if self.minerals >= 3500:
                        if len(self.units(UnitTypeId.DRONE)) >= 25:
                            if not self.bigattacking:
                                self.supplytricking = True
                                self.supplytrick_phase = "sporing"
                                self.supplycap_army += 20
                                self.supplycap_drones -= 20
                                self.supplytrick_end = self.frame + 20 * self.seconds
            if self.supplytrick_phase == "sporing":
                if self.frame >= self.supplytrick_end:
                    self.supplytrick_phase = "canceling"
                    for crawlegg in self.structures(UnitTypeId.SPORECRAWLER):
                        if not crawlegg.is_ready:
                            crawlegg(AbilityId.CANCEL)
                    self.supplytrick_end = self.frame + self.seconds
            if self.supplytrick_phase == "canceling":
                if self.frame >= self.supplytrick_end:
                    self.supplytricking = False
                    self.supplytrick_phase = "no"
                    self.supplycap_army -= 20
                    self.supplycap_drones += 20

    async def rallypoints(self):
        if self.function_listens("rallypoints", 6 * self.seconds):
            for hat in self.structures(UnitTypeId.HATCHERY):
                if hat.tag not in self.rallied:
                    self.rallied.add(hat.tag)
                    point = hat.position.towards(self.map_center, 3)
                    hat(AbilityId.RALLY_BUILDING, point)
