# making.py, Ender

import random
from loguru import logger

from ender.job import Job
from ender.map_if import Map_if
from ender.resources import Resources
from ender.strategy import Strategy
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class Making(Map_if, Resources, Strategy):

    creation = {} # per unittype the ability of making it. One source, so misses unburrows.
    #
    # upgrade_chain to start upgrades in this order (provided creatable)
    upgrade_chain = [UpgradeId.ZERGLINGMOVEMENTSPEED,
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
                     UpgradeId.EVOLVEMUSCULARAUGMENTS] 
    __did_step0 = False
    want_supply = True
    expansions = [] # of (pos,height,hasmin,hasgas,mybase,herbase,myblock,herblock,myarmy,herarmy)
    expansion_tried = {} # per expansionpos: the frame of the last hatchery create try
    importance = {} # When multiple claims, use importance
    subimportance = {} # per armytype: between 0 and 20
    ordids_stepcache = {} # speedup
    vespene_hist = 0 # sometimes gets the vespene value, to detect no mining
    minerals_hist = 0 # sometimes gets the minerals value, to detect no mining
    buildplan = {} # per typ: (histag, buildpos, expiration)
    walkers = set() # expanding with a drone prewalking
    expiration_of_builder = {} # it is a temporal job
    experience = [] # walktime for walkers
    example = UnitTypeId.SCV # for debugging, e.g. EXTRACTOR. To silence: SCV
    do_calc_groupclaim = False
    #

    def __step0(self):
        #
        self.importance['overlord'] = 100
        self.importance['emergency'] = 90
        self.importance['drone'] = 80
        self.importance['queen'] = 70
        self.importance['lone_building'] = 60
        self.importance['upgrade'] = 50
        self.importance['extractor'] = 40
        self.importance['hatchery'] = 30
        self.importance['army'] = 10 # leave room to add subimportance
        self.importance['sporespine'] = 0
        #
        for typ in self.all_armytypes:
            self.subimportance[typ] = 0
        self.subimportance[UnitTypeId.BROODLING] = 0 # do not wait for those
        self.subimportance[UnitTypeId.ZERGLING] = 1
        self.subimportance[UnitTypeId.QUEEN] = 2
        self.subimportance[UnitTypeId.ROACH] = 3
        self.subimportance[UnitTypeId.BANELING] = 4
        self.subimportance[UnitTypeId.INFESTOR] = 5
        self.subimportance[UnitTypeId.MUTALISK] = 6
        self.subimportance[UnitTypeId.SWARMHOSTMP] = 7
        self.subimportance[UnitTypeId.OVERSEER] = 8
        self.subimportance[UnitTypeId.HYDRALISK] = 9
        self.subimportance[UnitTypeId.LURKERMP] = 10
        self.subimportance[UnitTypeId.RAVAGER] = 11
        self.subimportance[UnitTypeId.OVERLORDTRANSPORT] = 12
        self.subimportance[UnitTypeId.CORRUPTOR] = 13
        self.subimportance[UnitTypeId.VIPER] = 14
        self.subimportance[UnitTypeId.BROODLORD] = 15
        self.subimportance[UnitTypeId.ULTRALISK] = 16
        #
        # creation
        for bartype in sc2.dicts.unit_research_abilities.RESEARCH_INFO:
            for martype in sc2.dicts.unit_research_abilities.RESEARCH_INFO[bartype]:
                abi = sc2.dicts.unit_research_abilities.RESEARCH_INFO[bartype][martype]['ability']
                self.creation[martype] = abi
        for bartype in sc2.dicts.unit_train_build_abilities.TRAIN_INFO:
            for martype in sc2.dicts.unit_train_build_abilities.TRAIN_INFO[bartype]:
                abi = sc2.dicts.unit_train_build_abilities.TRAIN_INFO[bartype][martype]['ability']
                self.creation[martype] = abi
        for typ in self.all_changelings:
            self.creation[typ] = AbilityId.BURROWDOWN_RAVAGER # intentionally wrong
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
        self.creation[UnitTypeId.BROODLING] = AbilityId.BURROWDOWN_RAVAGER # intentionally wrong
        #
        self.init_expansions()
        self.next_expansion = self.nowhere
        self.choose_next_expansion()

    async def on_step(self):
        await Map_if.on_step(self)
        await Resources.on_step(self)
        await Strategy.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        # stepcache
        self.ordids_stepcache = {}
        #
        for typ in self.all_armytypes:
            await self.make_army_unit(typ)
        await self.expand()
        await self.build_structure('spaw',UnitTypeId.SPAWNINGPOOL)
        await self.build_structure('roac',UnitTypeId.ROACHWARREN)
        await self.build_structure('bane',UnitTypeId.BANELINGNEST)
        await self.build_structure('lair',UnitTypeId.LAIR)
        await self.build_structure('hive',UnitTypeId.HIVE)
        await self.build_structure('infe',UnitTypeId.INFESTATIONPIT)
        await self.build_structure('hydr',UnitTypeId.HYDRALISKDEN)
        await self.build_structure('lurk',UnitTypeId.LURKERDENMP)
        await self.build_structure('spir',UnitTypeId.SPIRE)
        await self.build_structure('nydu',UnitTypeId.NYDUSNETWORK)
        await self.build_structure('grea',UnitTypeId.GREATERSPIRE)
        await self.build_structure('ultr',UnitTypeId.ULTRALISKCAVERN)
        await self.build_evolutionchambers()
        await self.sporespine()
        await self.emergency()
        await self.build_extractors()
        await self.make_overlords()
        for upg in self.all_upgrades:
            await self.upgrade(upg)
        await self.make_drones()
        #await self.prewalk()
        await self.builder_admin()
        await self.go_walk()
        await self.downroot()
        await self.destroyed()
        #
        if self.frame % 17 == 16:
            self.vespene_hist = self.vespene
            self.minerals_hist = self.minerals
        #
        await self.calc_groupclaim()

    async def calc_groupclaim(self):
        if self.do_calc_groupclaim:
            self.do_calc_groupclaim = False
            self.zero_groupclaim()
            for thing in self.make_plan:
                if self.make_plan[thing] > 0:
                    tomake = self.make_plan[thing] - self.atleast_started(thing)
                    if tomake > 0:
                        self.add_groupclaim(thing, tomake)
                        logger.info('I must still make ' + str(tomake) + ' ' + thing.name)

    def started(self, thing) -> int:
        sol = 0
        for claim in self.orderdelay:
            (typ,resources,importance,expiration) = claim
            if typ == thing:
                sol += 1
        cocoon = self.creator[thing]
        if cocoon == UnitTypeId.LARVA:
            cocoon = UnitTypeId.EGG # be aware: tagchange on ending cocoon state.
        if thing == UnitTypeId.OVERLORDTRANSPORT:
            cocoon = UnitTypeId.TRANSPORTOVERLORDCOCOON
        if thing == UnitTypeId.OVERSEER:
            cocoon = UnitTypeId.OVERLORDCOCOON
        if thing == UnitTypeId.LURKERMP:
            cocoon = UnitTypeId.LURKERMPEGG
        if thing == UnitTypeId.BROODLORD:
            cocoon = UnitTypeId.BROODLORDCOCOON
        if thing == UnitTypeId.RAVAGER:
            cocoon = UnitTypeId.RAVAGERCOCOON
        if thing == UnitTypeId.BANELING:
            cocoon = UnitTypeId.BANELINGCOCOON # be aware: tagchange on ending cocoon state.
        creation = self.creation[thing]
        if cocoon in self.ordids_stepcache: # speedup
            ordids = self.ordids_stepcache[cocoon]
        else:
            ordids = []
            for unt in self.units(cocoon) + self.structures(cocoon):
                for order in unt.orders:
                    ordids.append(order.ability.exact_id)
            self.ordids_stepcache[cocoon] = ordids
        for ordid in ordids:
            if ordid == creation:
                sol += 1
        return sol
                
    def atleast_started(self, thing) -> int:
        am = 0
        am += self.started(thing)
        if (thing in self.state.upgrades):
            am += 1
        if type(thing) == UnitTypeId:
            am += len(self.structures(thing))
            am += len(self.units(thing))
        if (thing == UnitTypeId.HATCHERY):
            am += len(self.units(UnitTypeId.LAIR))
            am += len(self.units(UnitTypeId.HIVE))
        if (thing == UnitTypeId.LAIR):
            am += len(self.units(UnitTypeId.HIVE))
        if (thing == UnitTypeId.SPIRE):
            am += len(self.units(UnitTypeId.GREATERSPIRE))
        if (thing == UnitTypeId.EXTRACTOR):
            am += len(self.units(UnitTypeId.EXTRACTORRICH))
        return am

    def atleast_some_started(self, thing) -> bool:
        # to speed up
        if (thing in self.state.upgrades):
            return True
        if type(thing) == UnitTypeId:
            if len(self.structures(thing)) > 0:
                return True
            if len(self.units(thing)) > 0:
                return True
        if (thing == UnitTypeId.HATCHERY):
            if len(self.units(UnitTypeId.LAIR)) > 0:
                return True
            if len(self.units(UnitTypeId.HIVE)) > 0:
                return True
        if (thing == UnitTypeId.LAIR):
            if len(self.units(UnitTypeId.HIVE)) > 0:
                return True
        if (thing == UnitTypeId.SPIRE):
            if len(self.units(UnitTypeId.GREATERSPIRE)) > 0:
                return True
        if (thing == UnitTypeId.EXTRACTOR):
            if len(self.units(UnitTypeId.EXTRACTORRICH)) > 0:
                return True
        if self.started(thing) > 0:
            return True
        return False

    def builder(self, pos):
        max_dist = 99999
        # give a default to not crash when few drones
        him = self.units(UnitTypeId.DRONE).first
        for unt in self.units(UnitTypeId.DRONE):
            if not self.get_unit_job(unt) in [Job.APPRENTICE, Job.WALKER, Job.BUILDER]:
                dist = self.distance(unt.position, pos)
                if dist < max_dist:
                    max_dist = dist
                    him = unt
        if max_dist == 99999:
            self.resign = True
        else:
            self.set_unit_job(him, Job.APPRENTICE)
            self.expiration_of_builder[him.tag] = self.frame + 80 * self.seconds
        return him

    async def sporespine(self):
        if self.minerals > (200 - self.supply_used) * 50: 
            spines = len(self.structures(UnitTypeId.SPINECRAWLER))
            spores = len(self.structures(UnitTypeId.SPORECRAWLER))
            if spores < spines:
                typ = UnitTypeId.SPORECRAWLER
            else:
                typ = UnitTypeId.SPINECRAWLER
            await self.build_structure('spor', typ)

    async def emergency(self):
        if self.frame < 6 * self.minutes:
            if self.function_listens('emergency',10):
                for stru in self.structures(UnitTypeId.HATCHERY):
                    strupos = stru.position
                    if stru.build_progress >= 0.5:
                        groundattackers = 0
                        flyingattackers = 0
                        for ene in self.enemy_units:
                            if ene.type_id not in {UnitTypeId.OVERLORD, UnitTypeId.OVERSEER}:
                                if self.distance(ene.position,strupos) < 10:
                                    anattacker = ene
                                    if ene.is_flying:
                                        flyingattackers += 1
                                    else:
                                        groundattackers += 1
                        # spore or spine
                        if (flyingattackers >= 1) or (groundattackers >= 2):
                            if 3 * flyingattackers > groundattackers:
                                typ = UnitTypeId.SPORECRAWLER
                                if self.atleast_started(typ) < groundattackers:
                                    await self.build_structure('emergency', typ)
                            else:
                                typ = UnitTypeId.SPINECRAWLER
                                if self.atleast_started(typ) < flyingattackers:
                                    await self.build_structure('emergency', typ)

    async def expand(self):
        if self.next_expansion == self.nowhere:
            if self.frame % 17 == 16:
                self.choose_next_expansion()
        typ = UnitTypeId.HATCHERY
        await self.build_structure('hatc',typ)

    async def make_overlords(self):
        queens = len(self.units(UnitTypeId.QUEEN))
        need_spare = 2 + 3 * (self.nbases - 1) + 2 * queens
        soon_supply = 0 # may be too high (for some seconds)
        soon_supply += 6 * self.started(UnitTypeId.OVERLORD)
        for stru in self.structures(UnitTypeId.HATCHERY):
            if stru not in self.structures(UnitTypeId.HATCHERY).ready:
                if (stru.build_progress > 0.75): # about 18 seconds
                    soon_supply += 6
        if (self.supply_left + soon_supply < need_spare) and (self.supply_cap + soon_supply < 220):
            importance = self.importance['overlord']
            importance += 1000 # overlords are implicit in make_plan
            typ = UnitTypeId.OVERLORD
            self.claim_resources(typ,importance)
            if self.check_resources(typ,importance):
                self.unclaim_resources(typ)
                self.larva.random.train(typ)
                self.do_calc_groupclaim = True

    async def make_army_unit(self,typ):
        if self.function_listens('make_' + typ.name, self.seconds):
            if typ == UnitTypeId.ROACH:
                if self.frame >= 4 * self.minutes:
                    breakthis = True
            if not self.structures.of_type(UnitTypeId.SPAWNINGPOOL).ready.exists:
                return
            if typ in {UnitTypeId.BROODLING, UnitTypeId.LOCUSTMP, UnitTypeId.LARVA}: # made automatic
                return
            if typ in self.all_changelings: # made automatic
                if typ != UnitTypeId.CHANGELING:
                    return
            if self.check_wannado_unit(typ):
                if typ == UnitTypeId.QUEEN:
                    importance = self.importance['queen']
                else:
                    importance = self.importance['army'] + self.subimportance[typ]
                # increase importance if in make_plan
                started = self.atleast_started(typ)
                if typ in self.morpher:
                    rava = self.morpher[typ]
                    started += self.atleast_started(rava)
                if (started < self.make_plan[typ]):
                    importance += 1000                    
                self.claim_resources(typ,importance)
                if self.check_resources(typ,importance):
                    self.unclaim_resources(typ)
                    self.do_calc_groupclaim = True
                    # make
                    crea = self.creator[typ]
                    if crea in {UnitTypeId.LARVA}:
                        self.train(typ)
                    elif typ == UnitTypeId.CHANGELING:
                        unt = self.units(crea).idle.random
                        unt(AbilityId.SPAWNCHANGELING_SPAWNCHANGELING)
                    elif len(self.structures(crea).idle) > 0:
                        # best make queen at a hatchery without queens
                        bestdist  = -1
                        for unt in self.structures(crea).idle:
                            itsdist = 9999
                            for que in self.units(typ):
                                dist = self.distance(que.position,unt.position)
                                itsdist = min(dist,itsdist)
                            if itsdist > bestdist:
                                bestdist = itsdist
                                bestunt = unt 
                        bestunt.train(typ)
                    else:
                        # best morph broodlord at home
                        bestdist = 9999
                        for unt in self.units(crea).idle:
                            itsdist = self.distance(unt.position,self.ourmain)
                            if itsdist < bestdist:
                                bestdist = itsdist
                                bestunt = unt
                        bestunt.train(typ)

    async def build_extractors(self):
        it = UnitTypeId.EXTRACTOR
        if len(self.freegeysers) > 0:
            if (len(self.freeexpos) <= 1) or (self.atleast_started(it) < self.nbases) \
            or (self.minerals > 1200) or (self.make_plan[it] > self.nbases):
                await self.build_structure('extr',it)

    async def build_evolutionchambers(self):
        it = UnitTypeId.EVOLUTIONCHAMBER
        if self.atleast_some_started(it):
            # second evo after 5 bases
            if self.nbases >= 5:
                await self.build_structure('evo2',it)
        else:
            await self.build_structure('evo1',it)
        
    async def build_structure(self,name,typ):
        if self.function_listens('build_structure_' + name, 2 * self.seconds):
            if self.check_wannado_structure(typ):
                if name == 'emergency':
                    importance = self.importance['emergency']
                    importance += 1000 # think those into make_plan
                elif typ == UnitTypeId.HATCHERY:
                    importance = self.importance['hatchery']
                elif typ == UnitTypeId.EXTRACTOR:
                    importance = self.importance['extractor']
                elif typ in self.all_sporetypes:
                    importance = self.importance['sporespine']
                else:
                    importance = self.importance['lone_building']
                if (self.atleast_started(typ) < self.make_plan[typ]):
                    importance += 1000                    
                self.claim_resources(typ,importance)
                if typ not in self.buildplan:
                    size = self.size_of_structure[typ]
                    if typ == UnitTypeId.EXTRACTOR:
                        gey = random.choice(self.freegeysers)
                        pos = gey.position
                        if self.map_can_plan_gas(pos, size):
                            self.map_plan_gas(pos, size)
                            him = self.builder(pos)
                            expiration = self.frame + self.minutes
                            self.buildplan[typ] = (him.tag, pos, expiration)
                    elif typ == UnitTypeId.HATCHERY:
                        pos = self.next_expansion
                        if self.map_can_plan(pos, size):
                            self.map_plan(pos, size)
                            him = self.builder(pos)
                            expiration = self.frame + self.minutes
                            self.buildplan[typ] = (him.tag, pos, expiration)
                            self.current_expandings[pos] = him.tag
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
                            self.buildplan[typ] = (self.notag, pos, expiration)
                    elif typ == UnitTypeId.HIVE:
                        if len(self.structures(UnitTypeId.LAIR).ready.idle) > 0:
                            stru = self.structures(UnitTypeId.LAIR).ready.idle.random
                            pos = stru.position
                            expiration = self.frame + self.minutes
                            self.buildplan[typ] = (self.notag, pos, expiration)
                    elif typ in self.all_sporetypes:
                        abasepos = self.structures(UnitTypeId.HATCHERY).random.position
                        # give extra chance to offensive placement
                        if self.distance(abasepos, self.ourmain) < self.distance(abasepos, self.enemymain):
                            abasepos = self.structures(UnitTypeId.HATCHERY).random.position
                        pos = abasepos.towards(self.map_center,3)
                        pos = self.map_around(pos,size)
                        self.map_plan(pos, size)
                        him = self.builder(pos)
                        expiration = self.frame + self.minutes
                        self.buildplan[typ] = (him.tag, pos, expiration)
                    else:
                        abasepos = self.structures(UnitTypeId.HATCHERY).ready.random.position
                        pos = abasepos.towards(self.map_center,5)
                        pos = self.map_around(pos, size)
                        self.map_plan(pos, size)
                        him = self.builder(pos)
                        expiration = self.frame + self.minutes
                        self.buildplan[typ] = (him.tag, pos, expiration)
                if self.check_resources(typ,importance):
                    if typ in self.buildplan:
                        # build
                        self.unclaim_resources(typ)
                        self.do_calc_groupclaim = True
                        (histag, buildpos, expiration) = self.buildplan[typ]
                        del self.buildplan[typ]
                        size = self.size_of_structure[typ]
                        if histag in self.living:
                            self.set_unit_job(histag, Job.BUILDER)
                            self.expiration_of_builder[histag] = self.frame + 8 * self.seconds # shortens it
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

    async def go_walk(self):
        mimminers = self.job_count(Job.MIMMINER)
        gasminers = self.job_count(Job.GASMINER)
        for typ in self.buildplan:
            (histag, buildpos, expir) = self.buildplan[typ]
            for unt in self.units(UnitTypeId.DRONE):
                if unt.tag == histag:
                    if self.get_unit_job(unt) == Job.APPRENTICE:
                        dist = self.distance(unt.position,buildpos)
                        mimgap = self.mineral_gap(typ)
                        gasgap = self.vespene_gap(typ)
                        if (mimminers > 0):
                            mimwait = mimgap / mimminers
                        elif mimgap > 0:
                            mimwait = 99999
                        else:
                            mimwait = 0
                        if (gasminers > 0):
                            gaswait = gasgap / gasminers
                        elif gasgap > 0:
                            gaswait = 99999
                        else:
                            gaswait = 0
                        resourcewait = max(mimwait, gaswait)
                        if resourcewait < dist * 0.5:
                            self.set_unit_job(unt, Job.WALKER)
                            unt.move(buildpos)
                        
    def we_finished_a(self, thing) -> bool:
        if thing in self.state.upgrades:
            return True
        if type(thing) == UnitTypeId:
            if len(self.structures(thing).ready) > 0:
                return True
            if len(self.units(thing)) > 0:
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
                    if not seen: # before
                        if not self.we_finished_a(thing):
                            canstart = False
                if (not canstart):
                    return False
        if self.resource_cost[the_thing][self.Resource.VESPENE] > 0:
            if self.vespene == 0:
                return False
        return True
        
    def check_wannado_upgrade(self, upg) -> bool:
        if self.atleast_some_started(upg):
            return False
        #
        if not self.tech_check(upg):
            return False
        #
        canstart = True
        seen = False
        for thing in self.upgrade_chain:
            seen = seen or (thing == upg)
            if not seen: # before
                if not self.atleast_some_started(thing):
                    if self.tech_check(thing):
                        canstart = False
        if (not canstart):
            return False
        #
        return True

    def check_wannado_unit(self, unty) -> bool:
        if not self.tech_check(unty):
            return False
        #
        max_count = 200
        if unty == UnitTypeId.DRONE:
            max_count = self.supplycap_drones
        if unty == {UnitTypeId.QUEEN, UnitTypeId.OVERSEERSIEGEMODE}:
            max_count = self.supplycap_queens / 2
        if unty == UnitTypeId.OVERLORD:
            max_count = 35
        if unty in {UnitTypeId.OVERSEER, UnitTypeId.OVERLORDTRANSPORT}:
            max_count = 20
        return True

    def check_wannado_structure(self, unty) -> bool:
        # tech demand
        if self.tech_requirement_progress(unty) < 0.5:
            if unty == self.example:
                logger.info('example ' + self.example.name + ' waits for tech')
            return False
        # the chosen amount of needed hatcheries
        if len(self.structures(UnitTypeId.HATCHERY)) < self.needhatches[unty]: # just-started hatcheries
            if unty == self.example:
                logger.info('example ' + self.example.name + ' waits for hatches')
                logger.info(str(len(self.structures(UnitTypeId.HATCHERY))), ' ' , str(self.needhatches[unty]))
            return False
        # the chosen structype order
        if unty in self.structype_order:
            canstart = True
            seen = False
            for thing in self.structype_order:
                seen = seen or (thing == unty)
                if not seen: # before
                    if not self.atleast_some_started(thing):
                        if self.make_plan[thing] > 0:
                            canstart = False
            if (not canstart):
                if unty == self.example:
                    logger.info('example ' + self.example.name + ' waits for structype_order')
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
                logger.info('example ' + self.example.name + ' is at maxcount.')
            return False
        return True

    async def upgrade(self, typ):
        if self.function_listens('upgrade_' + typ.name, 2 * self.seconds):
            importance = self.importance['upgrade']
            if self.atleast_some_started(typ):
                started = 1
            else:
                started = 0
            if (started < self.make_plan[typ]) or self.auto_upgrade:
                importance += 1000                    
            goon = True
            creator = self.creator[typ]
            resource = self.resource_of_buildingtype[creator]
            if not self.have_free_resource(resource, importance):
                goon = False
            if goon:
                if self.check_wannado_upgrade(typ):
                    self.claim_resources(typ, importance)
                    if self.check_resources(typ, importance):
                        self.unclaim_resources(typ)
                        self.do_calc_groupclaim = True
                        #logger.info('starting upgrade ' + typ.name + ' on a ' + creator.name)
                        evo = random.choice(self.structures(creator).ready.idle)
                        evo(self.creation[typ])

    async def make_drones(self):
        if self.function_listens('make_drones', self.seconds):
            typ = UnitTypeId.DRONE
            if self.check_wannado_unit(typ):
                lategame_max = 3 * len(self.extractors) + 2 * len(self.mineral_field) + 3
                if self.atleast_started(typ) < lategame_max:
                    # opening can delay making drones
                    delay = False
                    if self.bigattack_count == 0:
                        if len(self.opening) > 0:
                            todel = False
                            (kind, kind_am, thing, thing_am) = self.opening[0]
                            if kind == 'supply':
                                if self.supply_used >= kind_am:
                                    if self.atleast_started(thing) >= thing_am:
                                        todel = True
                                    else:
                                        delay = True
                            if todel:
                                del self.opening[0]
                    if not delay:
                        importance = self.importance['drone']
                        if (self.atleast_started(typ) < self.make_plan[typ]):
                            importance += 1000             
                        self.claim_resources(typ,importance)
                        if self.check_resources(typ, importance):
                            self.unclaim_resources(typ)
                            self.do_calc_groupclaim = True
                            self.larva.random.train(typ)

    def init_expansions(self):
        self.expansions = []
        for pos in self.expansion_locations_list:
            gridpos = Point2((round(pos.x-0.5),round(pos.y-0.5)))
            height = self.game_info.terrain_height[gridpos]
            hasmin = True
            hasgas = True
            mybase = (pos == self.ourmain)
            herbase = (pos == self.enemymain)
            myblock = False
            herblock = False
            myarmy = False
            herarmy = False
            self.expansions.append((pos,height,hasmin,hasgas,mybase,herbase,myblock,herblock,myarmy,herarmy))
            
    def choose_next_expansion(self):
        # update info
        for exix in range(0,len(self.expansions)):
            expansion = self.expansions[exix]
            (pos,height,hasmin,hasgas,mybase,herbase,myblock,herblock,myarmy,herarmy) = expansion
            mybase = False
            herbase = False
            for halltype in self.all_halltypes:
                for stru in self.structures(halltype):
                    dist = self.distance(stru.position,pos)
                    if dist < 3:
                        mybase = True
                for (ene,enepos) in self.enemy_struc_mem:
                    if ene == halltype:
                        dist = self.distance(enepos,pos)
                        if dist < 3:
                            herbase = True
            expansion = (pos,height,hasmin,hasgas,mybase,herbase,myblock,herblock,myarmy,herarmy)
            self.expansions[exix] = expansion
        # choose expansionposition with highest evalu
        bestevalu = -99999
        bestpos = self.nowhere
        for expansion in self.expansions:
            (pos,height,hasmin,hasgas,mybase,herbase,myblock,herblock,myarmy,herarmy) = expansion
            if (not herbase) and (not mybase):
                if hasgas or hasmin:
                    ago = 99999
                    if pos in self.expansion_tried:
                        ago = self.frame - self.expansion_tried[pos]
                    if ago >= 25 * self.seconds:
                        evalu = 0
                        evalu += height
                        if self.nbases == 1:
                            evalu -= self.distance(self.ourmain,pos)
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
        logger.info('next expansion '+str(bestpos.x)+','+str(bestpos.y))

    async def builder_admin(self):
        if self.function_listens('builder_admin',17):
            # current_expandings
            todel = set()
            for pos in self.current_expandings:
                tag = self.current_expandings[pos]
                seen = False
                for unt in self.workers:
                    if unt.tag == tag:
                        if self.get_unit_job(unt) in [Job.APPRENTICE, Job.WALKER, Job.BUILDER]:
                            seen = True
                if not seen:
                    todel.add(pos) 
            for pos in todel:
                del self.current_expandings[pos]
            # buildplan
            todel = set()
            for typ in self.buildplan:
                (histag,buildpos,expiration) = self.buildplan[typ]
                if self.frame >= expiration:
                    todel.add(typ)
            for typ in todel:
                (histag,buildpos,expiration) = self.buildplan[typ]
                del self.buildplan[typ]
                if histag in self.living:
                    if self.get_unit_job(histag) in [Job.APPRENTICE, Job.WALKER, Job.BUILDER]:
                        self.set_unit_job(histag, Job.UNCLEAR)
            # expiration_of_builder
            for unt in self.units(UnitTypeId.DRONE):
                if self.get_unit_job(unt) in [Job.APPRENTICE, Job.WALKER, Job.BUILDER]:
                    if self.frame >= self.expiration_of_builder[unt.tag]:
                        self.set_unit_job(unt, Job.UNCLEAR)
                    
    async def prewalk(self):
        if self.function_listens('prewalk',10):
            hatchclaim = False
            for claim in self.claims:
                (typ, resources, importance, expiration) = claim
                if typ == UnitTypeId.HATCHERY:
                    hatchclaim = True
            if hatchclaim:
                pos = self.next_expansion
                if pos not in self.walkers:
                    self.init_experience()
                    walkframe = 0
                    ix = len(self.walkers)
                    if ix < len(self.experience):
                        walkframe = self.experience[ix]
                    if self.frame > walkframe:
                        clodist = 99999
                        bestunt = None
                        for unt in self.units(UnitTypeId.DRONE):
                            if self.get_unit_job(unt) in [Job.UNCLEAR, Job.MIMMINER]:
                                dist = self.distance(unt.position, pos)
                                if dist < clodist:
                                    clodist = dist
                                    bestunt = unt
                        if bestunt:
                            unt = bestunt
                            self.walkers.add(pos)
                            self.set_unit_job(unt, Job.WALKER)
                            unt.move(pos)
                            self.expiration_of_builder[unt.tag] = self.frame + self.minutes

    def init_experience(self):
        if len(self.experience) == 0:
            self.experience.append(900)
            self.experience.append(1650)
            self.experience.append(5200)

    async def downroot(self):
        if self.function_listens('downroot',10):        
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

    async def destroyed(self):
        for stru in self.structures:
            if stru.tag in self.last_health:
                if stru.health < 0.67 * self.last_health[stru.tag]:
                    stru(AbilityId.CANCEL_BUILDINPROGRESS)

 

                
                
                
