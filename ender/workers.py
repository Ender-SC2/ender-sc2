# workers.py, Merkbot, Zerg sandbox bot
# 20 apr 2022

from ender.common import Common
from sc2.ids.unit_typeid import UnitTypeId


class Workers(Common):


    __did_step0 = False
    good_expos = set() # expansion_location with a near own base
    itsexpo = {} # per position of mineral or geyser, the closest expo
    herexpo = {} # per miner, the closest expo
    minings = {} # per expo, the amount of free miningspots
    last_world = -1 # hash of the mining situation
    gasminertags = set() # may be a workertag, may be in limbo
    miners_of_gas = {} # per gasposition: the set of 3 gasminertag

    def __step0(self):
        #
        self.initial_patches()
        self.organize_minerals()
        self.initials()
        #

    async def on_step(self):
        await Common.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.cleanup_workers()
        await self.distribute_workers_3()
        await self.volunteers()

    def organize_minerals(self):
        # itsexpo
        self.itsexpo = {}
        for mim in self.mineral_field:
            pos = mim.position
            closest = 99999
            for expo in self.expansion_locations_list:
                dist = self.distance(expo, pos)
                if dist < closest:
                    closest = dist
                    bestexpo = expo
            self.itsexpo[pos] = bestexpo
        for gey in self.vespene_geyser:
            pos = gey.position
            closest = 99999
            for expo in self.expansion_locations_list:
                dist = self.distance(expo, pos)
                if dist < closest:
                    closest = dist
                    bestexpo = expo
            self.itsexpo[pos] = bestexpo

    async def distribute_workers_3(self):
        all_expos = self.expansion_locations_list
        mimminers = self.workers.filter(lambda worker: self.job_of_unit[worker.tag] == self.Job.MIMMINER)
        visible_gasminers = self.workers.filter(lambda worker: self.job_of_unit[worker.tag] == self.Job.GASMINER)
        bases = self.townhalls.ready.filter(lambda hall: hall.health >= 500)
        if len(bases) == 0:
            bases = self.townhalls.ready
        # has the world changed?
        world = len(self.mineral_field) + 100 * len(bases) + 10000 * len(self.extractors) \
                + 1000000 * len(mimminers) + 100000000 * len(self.gasminertags)
        if world != self.last_world:
            self.last_world = world
            # good_expos
            self.good_expos = set()
            for expo in all_expos:
                usable = False
                for base in bases:
                    if self.distance(base.position,expo) < 4:
                        usable = True
                if usable:
                    self.good_expos.add(expo)
            # minings
            self.minings = {}
            for expo in all_expos:
                self.minings[expo] = 0
            for mim in self.mineral_field:
                pos = mim.position
                expo = self.itsexpo[pos]
                self.minings[expo] += 2
            for gab in self.extractors:
                pos = gab.position
                expo = self.itsexpo[pos]
                self.minings[expo] += 3
            for wor in mimminers:
                expo = self.herexpo[wor.tag]
                self.minings[expo] -= 1
            for pos in self.miners_of_gas:
                team = self.miners_of_gas[pos]
                expo = self.itsexpo[pos]
                self.minings[expo] -= len(team)                
            # fire miners of lost bases
            for wor in mimminers | visible_gasminers:
                expo = self.herexpo[wor.tag] # should be correct
                if expo not in self.good_expos:
                    self.job_of_unit[wor.tag] = self.Job.UNCLEAR
            # fire miners of lost minerals
            spots = {}
            for expo in all_expos:
                spots[expo] = 0
            for mim in self.mineral_field:
                pos = mim.position
                expo = self.itsexpo[pos]
                spots[expo] += 2
            for wor in mimminers:
                expo = self.herexpo[wor.tag]
                spots[expo] -= 1
                if spots[expo] < 0:
                    self.job_of_unit[wor.tag] = self.Job.UNCLEAR
            # fire miners of lost gasbuildings
            spots = {}
            for gey in self.vespene_geyser:
                pos = gey.position
                spots[pos] = 0
            for gab in self.extractors:
                pos = gab.position
                spots[pos] = 3
            for gey in self.vespene_geyser:
                pos = gey.position
                if spots[pos] == 0:
                    team = self.miners_of_gas[pos]
                    if len(team) > 0:
                        for tag in team:
                            self.job_of_unit[tag] = self.Job.UNCLEAR # may be done while in limbo!
                        self.gasminertags -= team
                        self.miners_of_gas[pos] = set()
        # employ
        unemployed = self.workers.filter(lambda worker: self.job_of_unit[worker.tag] == self.Job.UNCLEAR)
        work = 0
        for expo in self.good_expos:
            if self.minings[expo] > 0:
                work += self.minings[expo]
        if 0 < len(unemployed) <= work:
            # much work
            for wor in unemployed:
                pos = wor.position
                bestdist = 99999
                for expo in self.good_expos:
                    if self.minings[expo] > 0:
                        dist = self.distance(expo,pos)
                        if dist < bestdist:
                            bestdist = dist
                            bestexpo = expo
                self.herexpo[wor.tag] = bestexpo
                self.minings[bestexpo] -= 1
                self.detail(wor,bestexpo)
        elif 0 < work < len(unemployed):
            # many unemployed
            for expo in self.good_expos:
                while self.minings[expo] > 0:                    
                    bestdist = 99999
                    for wor in unemployed:
                        pos = wor.position
                        dist = self.distance(expo,pos)
                        if dist < bestdist:
                            bestdist = dist
                            bestwor = wor
                    self.herexpo[bestwor.tag] = expo
                    self.minings[expo] -= 1
                    self.detail(bestwor,expo)
                    
    def detail(self, wor, expo):
        # worker starts to work at expo
        gabs = self.extractors.filter(lambda gab: self.itsexpo[gab.position] == expo)
        mims = self.mineral_field.filter(lambda mim: self.itsexpo[mim.position] == expo)
        # find a working spot
        found = False
        if len(self.gasminertags) * 2 < self.jobcount(self.Job.MIMMINER):
            for gab in gabs:
                if not found:
                    if len(self.miners_of_gas[gab.position]) < 3:
                        found = True
                        wor.gather(gab)
                        self.miners_of_gas[gab.position].add(wor.tag)
                        self.gasminertags.add(wor.tag)
                        self.job_of_unit[wor.tag] = self.Job.GASMINER
        if len(mims) > 0:
            if not found:
                mim = mims.closest_to(wor.position)
                found = True
                wor.gather(mim)
                self.job_of_unit[wor.tag] = self.Job.MIMMINER
        
    async def cleanup_workers(self):
        # cleanup miners_of_gas and gasminertags
        if self.function_listens('cleanup_gas',50):
            # verify job
            todel = set()
            for wor in self.workers:
                tag = wor.tag
                if tag in self.gasminertags:
                    if self.job_of_unit[tag] != self.Job.GASMINER:
                        self.gasminertags.remove(tag)
                        todel.add(tag)
            if len(todel) > 0:
                for pos in self.miners_of_gas:
                    self.miners_of_gas[pos] -= todel
            # gasminertags
            todel = set()
            for tag in self.gasminertags:
                if tag not in self.living:
                    if tag not in self.limbo:
                        todel.add(tag)
            self.gasminertags -= todel
            # miners_of_gas
            for pos in self.miners_of_gas:
                todel = set()
                team = self.miners_of_gas[pos]
                for tag in team:
                    if tag not in self.living:
                        if tag not in self.limbo:
                            todel.add(tag)
                team -= todel
                if len(todel) > 0:
                    self.miners_of_gas[pos] = team

    def initials(self):
        # herexpo
        for wor in self.workers:
            self.herexpo[wor.tag] = self.ourmain
        # miners_of_gas
        for gey in self.vespene_geyser:
            pos = gey.position
            self.miners_of_gas[pos] = set()



    def initial_patches(self):
        # at the start of the game, move workers
        my_patches = [min   for min in self.mineral_field   if self.distance(min.position,self.ourmain) <= 10]
        count = dict((patch,0) for patch in my_patches)
        for worker in self.workers:
            lowest = min(count.values())
            good_patches = [patch   for patch in my_patches   if count[patch] == lowest]
            dists = dict((patch, self.distance(patch.position,worker.position))   for patch in good_patches)
            lowest = min(dists.values())
            best_patches = [patch   for patch in good_patches   if dists[patch] == lowest]
            best_patch = best_patches[0]
            worker.gather(best_patch)
            count[best_patch] += 1
        
    async def volunteers(self):
        # have nojob workers mine anywhere
        if self.function_listens('volunteers',30):
            # count, an_unemployed, a_volunteer
            unemployed = 0
            volunteers = 0
            for unt in self.units(UnitTypeId.DRONE):
                tag = unt.tag
                if self.job_of_unit[tag] == self.Job.UNCLEAR:
                    unemployed += 1
                    an_unemployed = unt
                if self.job_of_unit[tag] == self.Job.VOLUNTEER:
                    volunteers += 1
                    a_volunteer = unt
            # idling volunteers
            if volunteers > 0:
                for unt in self.units(UnitTypeId.DRONE).idle:
                    tag = unt.tag
                    if self.job_of_unit[tag] == self.Job.VOLUNTEER:
                        if self.frame >= self.listenframe_of_unit[tag]:
                            self.job_of_unit[tag] = self.Job.UNCLEAR
                            volunteers -= 1
            # new volunteer
            if unemployed >= 3:
                unemployed -= 1
                if len(self.mineral_field) > 0:
                    unt = an_unemployed
                    patch = self.mineral_field.random
                    self.job_of_unit[unt.tag] = self.Job.VOLUNTEER
                    unt.gather(patch)
                    self.listenframe_of_unit[unt.tag] = self.frame + self.seconds
                    volunteers += 1
                else:
                    unt = an_unemployed
                    goal = self.enemymain
                    for (typ,pos) in self.enemy_struc_mem:
                        if typ in self.all_halltypes:
                            goal = pos
                    unt.attack(goal)
                    self.job_of_unit[unt.tag] = self.Job.BERSERKER
                    # drone berserkers are separate from army berserkers
            if unemployed < 2:
                if volunteers > 0:
                    unt = a_volunteer
                    self.job_of_unit[unt.tag] = self.Job.UNCLEAR
                    volunteers -= 1
                    unemployed += 1
                
