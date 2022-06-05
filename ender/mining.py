# mining.py, Ender
#
# Mining.py administrates a connection between miners and mineralpatches or extractors.
#
# Position-tag.
# When walking to a mineralpatch out of sight, its tag changes when it comes into sight.
# For neutral and enemy units that have a stable position, use this postag.
# A Point2 (22.5, 130) has postag 45260, as 45260 = 22.5 * 2000 + 130 * 2.
# So for points p on the halfgrid (0 <= p.x < 200 and p.x is whole or half),
#    the postag is unique and invertable.
# 

from loguru import logger

from ender.common import Common
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.ids.ability_id import AbilityId

class Mining(Common):

    __did_step0 = False
    expo_of_postag = {} # constant. For mineralpatches and geysers.
    patch_of_postag_mfu = {} # multiframe unit
    gas_of_postag_mfu = {} # multiframe unit
    minables_hash = -1
    minables_hash_last = -2
    goodgeysers = set()
    minebases = set()
    minebase_of_expo_mfu = {} # multiframe unit
    gasbuildings = set()
    gaswork = [] # multiset
    mimwork = [] # multiset
    assign = {} # Per dronetag: the postag of the mineralpatch or geyser. For drones with a mining job. 
    info_phase_frame = {} # for speedmining
    patchpoint = {} # for speedmining
    basepoint = {} # for speedmining
    patchpoint_dist = {} # for speedmining
    basepoint_dist = {} # for speedmining
    hit_carrying = {} # for speedmining

    def __step0(self):
        self.calc_expo_of_postag()

    async def on_step(self):
        await Common.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.calc_minables()
        await self.calc_oldminers()
        await self.assign_free_work()
        await self.assign_free_miners()
        await self.steer_miners()
        await self.speed_mining()
        # await self.check_mining()
        await self.volunteers()

    def postag_of_position(self, point: Point2) -> int:
        return round(2 * point.x) * 1000 + round(2 * point.y)

    def position_of_postag(self, post: int) -> Point2:
        return Point2(( (post // 1000)/2, (post % 1000) / 2 ))

    def calc_expo_of_postag(self):
        # at gamestart
        self.expo_of_postag = {}
        for res in self.mineral_field:
            respos = res.position
            post = self.postag_of_position(respos)
            bestdist = 99999
            for expo in self.expansion_locations_list:
                dist = self.distance(expo,respos)
                if dist < bestdist:
                    bestdist = dist
                    bestexpo = expo
            self.expo_of_postag[post] = bestexpo
        for res in self.vespene_geyser:
            respos = res.position
            post = self.postag_of_position(respos)
            bestdist = 99999
            for expo in self.expansion_locations_list:
                dist = self.distance(expo,respos)
                if dist < bestdist:
                    bestdist = dist
                    bestexpo = expo
            self.expo_of_postag[post] = bestexpo

    def calc_patch_mfu(self):
        self.patch_of_postag_mfu = {}
        for patch in self.mineral_field:
            post = self.postag_of_position(patch.position)
            self.patch_of_postag_mfu[post] = patch

    def calc_gas_mfu(self):
        self.gas_of_postag_mfu = {}
        for gas in self.gasbuildings:
            post = self.postag_of_position(gas.position)
            self.gas_of_postag_mfu[post] = gas

    def patch_of_postag(self, post: int): # -> Unit
        patch = None
        if post in self.patch_of_postag_mfu:
            patch = self.patch_of_postag_mfu[post]
            if patch not in self.mineral_field:
                self.calc_patch_mfu()
                if post in self.patch_of_postag_mfu:
                    patch = self.patch_of_postag_mfu[post]
        else:
            self.calc_patch_mfu()
            if post in self.patch_of_postag_mfu:
                patch = self.patch_of_postag_mfu[post]
        return patch

    def gas_of_postag(self, post: int): # -> Unit
        gas = None
        if post in self.gas_of_postag_mfu:
            gas = self.gas_of_postag_mfu[post]
            if gas not in self.gasbuildings:
                self.calc_gas_mfu()
                if post in self.gas_of_postag_mfu:
                    gas = self.gas_of_postag_mfu[post]
        else:
            self.calc_gas_mfu()
            if post in self.gas_of_postag_mfu:
                gas = self.gas_of_postag_mfu[post]
        return gas

    async def calc_minables(self):
        # at framestart
        self.minables_hash = 0
        # goodgeysers
        self.goodgeysers = set()
        for gey in self.vespene_geyser:
            if gey.has_vespene:
                self.goodgeysers.add(gey.position)
                self.minables_hash += gey.position.x
        # mineral_field contains only nonempty patches  TO BE VERIFIED
        logger.info('len mineral_field = ' + str(len(self.mineral_field)))
        self.minables_hash += len(self.mineral_field)
        # minebases
        self.minebases = set()
        for typ in self.all_halltypes:
            for bas in self.structures(typ).ready:
                self.minebases.add(bas)
                self.minables_hash += bas.position.x
                # Should hash change when hatch becomes hive?
        # gasbuildings
        self.gasbuildings = set()
        for typ in {UnitTypeId.EXTRACTOR, UnitTypeId.EXTRACTORRICH}:
            for gas in self.structures(typ).ready:
                if gas.position in self.goodgeysers:
                    self.gasbuildings.add(gas)
                    self.minables_hash += gas.position.x
            
    async def calc_oldminers(self):
        if self.minables_hash != self.minables_hash_last:
            self.minables_hash_last = self.minables_hash
            # per expo: the closest own base
            self.minebase_of_expo_mfu = {}
            for expo in self.expansion_locations_list:
                bestdist = 99999
                for bas in self.minebases:
                    baspos = bas.position
                    dist = self.distance(baspos,expo)
                    if dist < bestdist:
                        bestdist = dist
                        bestbas = bas
                self.minebase_of_expo_mfu[expo] = bestbas
            # gaswork: a multiset of post
            self.gaswork = []
            for gas in self.gasbuildings:
                respos = gas.position
                post = self.postag_of_position(respos)
                expo = self.expo_of_postag[post]
                bas = self.minebase_of_expo_mfu[expo]
                dist = self.distance(bas.position, respos)
                if dist < 10:
                    self.gaswork.append(post)
                    self.gaswork.append(post)
                    self.gaswork.append(post)
            # mimwork: a multiset of post
            self.mimwork = []
            for patch in self.mineral_field:
                respos = patch.position
                post = self.postag_of_position(respos)
                expo = self.expo_of_postag[post]
                bas = self.minebase_of_expo_mfu[expo]
                dist = self.distance(bas.position, respos)
                if dist < 10:
                    self.mimwork.append(post)
                    self.mimwork.append(post)
            # assign miners and work
            old_assign = self.assign.copy()
            self.assign = {}
            for miner in old_assign:
                hadpost = old_assign[miner]
                if hadpost in self.mimwork:
                    self.assign[miner] = hadpost
                    del self.mimwork[self.mimwork.index(hadpost)]
            for miner in old_assign:
                hadpost = old_assign[miner]
                if hadpost in self.gaswork:
                    self.assign[miner] = hadpost
                    del self.gaswork[self.gaswork.index(hadpost)]
            # dismiss leftover miners
            for miner in old_assign:
                if miner not in self.assign:
                    self.job_of_unit[miner] = self.Job.UNCLEAR
                    # delete speedmining info
                    if miner in self.info_phase_frame:
                        del self.info_phase_frame[miner]

    async def assign_free_miners(self):
        freeworkers = 0
        for drone in self.units(UnitTypeId.DRONE):
            miner = drone.tag
            if self.job_of_unit[miner] == self.Job.UNCLEAR:
                freeworkers += 1
        freework = len(self.gaswork) + len(self.mimwork)
        if 0 < freeworkers <= freework:
            if self.frame > 3 * self.minutes: # DEBUG
                breakthis = True # DEBUG
            # assign leftover workers to leftover work, gas first
            for drone in self.units(UnitTypeId.DRONE):
                miner = drone.tag
                if self.job_of_unit[miner] == self.Job.UNCLEAR:
                    bestdist = 99999
                    for post in self.gaswork:
                        gaspos = self.position_of_postag(post)
                        dist = self.distance(gaspos, drone.position)
                        if dist < bestdist:
                            bestdist = dist
                            bestwork = post
                    if bestdist < 99999:
                        self.assign[miner] = bestwork
                        del self.gaswork[self.gaswork.index(bestwork)]
                        self.job_of_unit[miner] = self.Job.GASMINER
                        gas = self.gas_of_postag(bestwork)
                        drone.gather(gas)
                    if miner not in self.assign:
                        bestdist = 99999
                        for post in self.mimwork:
                            mimpos = self.position_of_postag(post)
                            dist = self.distance(mimpos, drone.position)
                            if dist < bestdist:
                                bestdist = dist
                                bestwork = post
                        if bestdist < 99999:
                            self.assign[miner] = bestwork
                            del self.mimwork[self.mimwork.index(bestwork)]
                            self.job_of_unit[miner] = self.Job.MIMMINER
                            patch = self.patch_of_postag(bestwork)
                            drone.gather(patch)
                     
    async def assign_free_work(self):
        freeworkers = 0
        for drone in self.units(UnitTypeId.DRONE):
            miner = drone.tag
            if self.job_of_unit[miner] == self.Job.UNCLEAR:
                freeworkers += 1
        freework = len(self.gaswork) + len(self.mimwork)
        if 0 < freework <= freeworkers:
            for work in self.gaswork:
                gaspos = self.position_of_postag(work)
                bestdist = 99999
                for drone in self.units(UnitTypeId.DRONE):
                    miner = drone.tag
                    if self.job_of_unit[miner] == self.Job.UNCLEAR:
                        dist = self.distance(gaspos, drone.position)
                        if dist < bestdist:
                            bestdist = dist
                            bestminer = miner
                if bestdist < 99999:
                    self.assign[bestminer] = work
                    self.job_of_unit[bestminer] = self.Job.GASMINER
                    gas = self.patch_of_postag(work)
                    drone.gather(gas)
                    self.listenframe_of_unit[miner] = self.frame + 5
            self.gaswork = []
            for work in self.mimwork:
                gaspos = self.position_of_postag(work)
                bestdist = 99999
                for drone in self.units(UnitTypeId.DRONE):
                    miner = drone.tag
                    if self.job_of_unit[miner] == self.Job.UNCLEAR:
                        dist = self.distance(gaspos, drone.position)
                        if dist < bestdist:
                            bestdist = dist
                            bestminer = miner
                if bestdist < 99999:
                    self.assign[bestminer] = work
                    self.job_of_unit[bestminer] = self.Job.MIMMINER
                    patch = self.patch_of_postag(work)
                    drone.gather(patch)
                    self.listenframe_of_unit[miner] = self.frame + 5
            self.mimwork = []

    async def steer_miners(self):
        for drone in self.units(UnitTypeId.DRONE):
            miner = drone.tag
            if self.job_of_unit[miner] == self.Job.MIMMINER:
                if self.frame >= self.listenframe_of_unit[miner]:
                    post = self.assign[miner]
                    patch = self.patch_of_postag(post)
                    expo = self.expo_of_postag[post]
                    base = self.minebase_of_expo_mfu[expo]
                    #
                    if len(drone.orders) == 0:
                        if drone.is_carrying_minerals:
                            drone(AbilityId.HARVEST_RETURN, base)
                            self.listenframe_of_unit[miner] = self.frame + 5
                        else: # not carrying minerals
                            drone(AbilityId.HARVEST_GATHER, patch)
                            self.listenframe_of_unit[miner] = self.frame + 5
                    elif len(drone.orders) == 1:
                        if drone.is_carrying_minerals:
                            for order in drone.orders:
                                if order.ability.id == AbilityId.HARVEST_RETURN:
                                    if type(order.target) == int:
                                        if order.target != base.tag:
                                            if order.target != 0:
                                                drone(AbilityId.HARVEST_RETURN, base)
                                                self.listenframe_of_unit[miner] = self.frame + 5
                        else: # not .is_carrying_minerals
                            for order in drone.orders:
                                if order.ability.id == AbilityId.HARVEST_GATHER:
                                    if type(order.target) == int:
                                        if order.target != patch.tag:
                                            if order.target != 0:
                                                drone(AbilityId.HARVEST_GATHER, patch)
                                                self.listenframe_of_unit[miner] = self.frame + 5
            if self.job_of_unit[miner] == self.Job.GASMINER:
                if self.frame >= self.listenframe_of_unit[miner]:
                    post = self.assign[miner]
                    gas = self.gas_of_postag(post)
                    expo = self.expo_of_postag[post]
                    base = self.minebase_of_expo_mfu[expo]
                    #
                    if len(drone.orders) == 0:
                        if drone.is_carrying_vespene:
                            drone(AbilityId.HARVEST_RETURN, base)
                            self.listenframe_of_unit[miner] = self.frame + 5
                        else: # not carrying vespene
                            drone(AbilityId.HARVEST_GATHER, gas)
                            self.listenframe_of_unit[miner] = self.frame + 5
                    elif len(drone.orders) == 1:
                        if drone.is_carrying_vespene:
                            for order in drone.orders:
                                if order.ability.id == AbilityId.HARVEST_RETURN:
                                    if type(order.target) == int:
                                        if order.target != base.tag:
                                            if order.target != 0:
                                                drone(AbilityId.HARVEST_RETURN, base)
                                                self.listenframe_of_unit[miner] = self.frame + 5
                        else: # not .is_carrying_vespene
                            for order in drone.orders:
                                if order.ability.id == AbilityId.HARVEST_GATHER:
                                    if type(order.target) == int:
                                        if order.target != gas.tag:
                                            if order.target != 0:
                                                drone(AbilityId.HARVEST_GATHER, gas)
                                                self.listenframe_of_unit[miner] = self.frame + 5

    async def speed_mining(self):
        for drone in self.units(UnitTypeId.DRONE):
            miner = drone.tag
            if self.job_of_unit[miner] == self.Job.MIMMINER:
                dronepos = drone.position
                post = self.assign[miner]
                patchpos = self.position_of_postag(post)
                patch = self.patch_of_postag(post)
                expo = self.expo_of_postag[post]
                base = self.minebase_of_expo_mfu[expo]
                basepos = base.position.towards(patchpos,2)
                if miner not in self.info_phase_frame:
                    pdist = self.distance(dronepos, patchpos)
                    if pdist < 2.5: # if far, do not start info phase
                        self.info_phase_frame[miner] = self.frame + 12 * self.seconds
                        self.patchpoint_dist[miner] = 99999
                        self.patchpoint[miner] = patchpos
                        self.basepoint_dist[miner] = 99999
                        self.basepoint[miner] = basepos
                        self.hit_carrying[miner] = True
                if miner in self.info_phase_frame:
                    pdist = self.distance(dronepos, patchpos)
                    bdist = self.distance(dronepos, basepos)
                    if self.frame < self.info_phase_frame[miner]:
                        maxdist = self.distance(basepos, patchpos)
                        if self.distance(dronepos, basepos) < maxdist: # inside
                            if self.distance(dronepos, patchpos) < maxdist: # inside
                                if pdist < self.patchpoint_dist[miner]:
                                    self.patchpoint_dist[miner] = pdist
                                    self.patchpoint[miner] = dronepos
                                if bdist < self.basepoint_dist[miner]:
                                    self.basepoint_dist[miner] = bdist
                                    self.basepoint[miner] = dronepos
                    else: # speedmining
                        if self.frame >= self.listenframe_of_unit[miner]:
                            if self.hit_carrying[miner]:
                                if bdist < 2.5:
                                    if drone.is_carrying_minerals:
                                        drone.move(self.basepoint[miner])
                                        drone(AbilityId.SMART, base, queue=True)
                                        self.listenframe_of_unit[miner] = self.frame + 5
                                        self.hit_carrying[miner] = not self.hit_carrying[miner]
                            else: # hit not carrying
                                if pdist < 2.5:
                                    if not drone.is_carrying_minerals:
                                        drone.move(self.patchpoint[miner])
                                        drone(AbilityId.SMART, patch, queue=True)
                                        self.listenframe_of_unit[miner] = self.frame + 5
                                        self.hit_carrying[miner] = not self.hit_carrying[miner]



    async def check_mining(self):
        for drone in self.units(UnitTypeId.DRONE):
            miner = drone.tag
            if self.job_of_unit[miner] == self.Job.MIMMINER:
                logger.info('len orders = ' + str(len(drone.orders)))
                post = self.assign[miner]
                patch = self.patch_of_postag(post)
                expo = self.expo_of_postag[post]
                base = self.minebase_of_expo_mfu[expo]
                # expectations
                normal = False
                if drone.is_carrying_minerals:
                    carries_min = 'Y'
                    if len(drone.orders) == 1:
                        for order in drone.orders:
                            if order.ability.id == AbilityId.HARVEST_RETURN:
                                if type(order.target) == int:
                                    if order.target == base.tag:
                                        normal = True
                else: # not .is_carrying_minerals
                    carries_min = 'N'
                    if len(drone.orders) == 1:
                        for order in drone.orders:
                            if order.ability.id == AbilityId.HARVEST_GATHER:
                                if type(order.target) == int:
                                    if order.target == patch.tag:
                                        normal = True
                # accept speedmining as normal
                if len(drone.orders) == 2:
                    successes = 0
                    for order in drone.orders:
                        if order.ability.id == AbilityId.HARVEST_RETURN:
                            if type(order.target) == int:
                                if order.target == base.tag:
                                    successes += 1
                        if order.ability.id == AbilityId.HARVEST_GATHER:
                            if type(order.target) == int:
                                if order.target == patch.tag:
                                    successes += 1
                    if successes == 2:
                        normal = True
                if normal:
                    logger.info('mining normal')
                else:
                    logger.info('mining strange')
                    # broad logging:
                    logger.info('   is_carrying_minerals = ' + carries_min)
                    logger.info('   len orders = '+str(len(drone.orders)))
                    for order in drone.orders:
                        logger.info('   order.ability.id = ' + str(order.ability.id))
                        logger.info('   type(order.target) = ' + type(order.target).__name__)
                        if type(order.target) == int:
                            logger.info(str(order.target) + ' != ' + str(patch.tag))
                            for stru in self.structures:
                                if stru.tag == order.target:
                                    logger.info('   order.target = ' + stru.type_id.name) 

                                
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
                


        