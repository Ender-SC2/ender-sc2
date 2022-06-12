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
from typing import Optional

from loguru import logger

from ender.common import Common
from ender.job import Job
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit


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
    info_start_frame = {} # for speedmining
    info_end_frame = {} # for speedmining
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
        await self.assign_free_workers()
        await self.steer_miners()
        await self.speed_mining()
        #await self.check_mining()
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

    def gas_of_postag(self, post: int) -> Unit:
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
        # mineral_field contains only nonempty patches
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
                    self.set_unit_job(miner, Job.UNCLEAR)
                    # delete speedmining info
                    if miner in self.info_start_frame:
                        del self.info_start_frame[miner]

    def assign_drone_to_closest_gas(self, drone):
        if self.get_unit_job(drone) == Job.UNCLEAR:
            miner = drone.tag
            best_dist = 99999
            best_work: Optional[int] = None
            for post in self.gaswork:
                gaspos = self.position_of_postag(post)
                dist = self.distance(gaspos, drone.position)
                if dist < best_dist:
                    best_dist = dist
                    best_work = post
            if best_work:
                self.assign[miner] = best_work
                del self.gaswork[self.gaswork.index(best_work)]
                self.set_unit_job(drone, Job.GASMINER)
                gas = self.gas_of_postag(best_work)
                drone.gather(gas)

    def assign_drone_to_closest_patch(self, drone):
        if self.get_unit_job(drone) == Job.UNCLEAR:
            miner = drone.tag
            if miner not in self.assign:
                best_dist = 99999
                best_work: Optional[int] = None
                for post in self.mimwork:
                    mimpos = self.position_of_postag(post)
                    dist = self.distance(mimpos, drone.position)
                    if dist < best_dist:
                        best_dist = dist
                        best_work = post
                if best_work:
                    self.assign[miner] = best_work
                    del self.mimwork[self.mimwork.index(best_work)]
                    self.set_unit_job(drone, Job.MIMMINER)
                    patch = self.patch_of_postag(best_work)
                    drone.gather(patch)

    async def assign_free_workers(self):
        freeworkers = 0
        for drone in self.units(UnitTypeId.DRONE):
            if self.get_unit_job(drone) == Job.UNCLEAR:
                freeworkers += 1
        freework = len(self.gaswork) + len(self.mimwork)
        if 0 < freeworkers <= freework:
            if self.frame > 3 * self.minutes: # DEBUG
                breakthis = True # DEBUG
            # assign leftover workers to leftover work
            # balance on excess gas
            for drone in self.units(UnitTypeId.DRONE):
                if self.minerals >= self.vespene:
                    self.assign_drone_to_closest_gas(drone)
                    self.assign_drone_to_closest_patch(drone)
                else: # having much gas
                    self.assign_drone_to_closest_patch(drone)
                    self.assign_drone_to_closest_gas(drone)
                     
    async def assign_free_work(self):
        freeworkers = 0
        for drone in self.units(UnitTypeId.DRONE):
            if self.get_unit_job(drone) == Job.UNCLEAR:
                freeworkers += 1
        freework = len(self.gaswork) + len(self.mimwork)
        if 0 < freework <= freeworkers:
            for work in self.gaswork:
                gaspos = self.position_of_postag(work)
                bestdist = 99999
                bestminer: Optional[Unit] = None
                for drone in self.units(UnitTypeId.DRONE):
                    if self.get_unit_job(drone) == Job.UNCLEAR:
                        dist = self.distance(gaspos, drone.position)
                        if dist < bestdist:
                            bestdist = dist
                            bestminer = drone
                if bestminer:
                    tag = bestminer.tag
                    self.assign[tag] = work
                    self.set_unit_job(bestminer, Job.GASMINER)
                    gas = self.patch_of_postag(work)
                    bestminer.gather(gas)
                    self.listenframe_of_unit[tag] = self.frame + 5
            self.gaswork.clear()
            for work in self.mimwork:
                gaspos = self.position_of_postag(work)
                bestdist = 99999
                bestminer: Optional[Unit] = None
                for drone in self.units(UnitTypeId.DRONE):
                    if self.get_unit_job(drone) == Job.UNCLEAR:
                        dist = self.distance(gaspos, drone.position)
                        if dist < bestdist:
                            bestdist = dist
                            bestminer = drone
                if bestminer:
                    tag = bestminer.tag
                    self.assign[tag] = work
                    self.set_unit_job(bestminer, Job.MIMMINER)
                    patch = self.patch_of_postag(work)
                    bestminer.gather(patch)
                    self.listenframe_of_unit[tag] = self.frame + 5
            self.mimwork.clear()

    async def steer_miners(self):
        for drone in self.units(UnitTypeId.DRONE):
            miner = drone.tag
            if self.get_unit_job(drone) == Job.MIMMINER:
                if self.frame >= self.listenframe_of_unit[miner]:
                    post = self.assign[miner]
                    patch = self.patch_of_postag(post)
                    expo = self.expo_of_postag[post]
                    base = self.minebase_of_expo_mfu[expo]
                    #
                    if len(drone.orders) == 0:
                        if drone.is_carrying_minerals:
                            drone(AbilityId.SMART, base) # HARVEST_RETURN with an argument
                            self.listenframe_of_unit[miner] = self.frame + 5
                            logger.info('miner kicked to return')
                        else: # not carrying minerals
                            drone(AbilityId.HARVEST_GATHER, patch)
                            self.listenframe_of_unit[miner] = self.frame + 5
                            logger.info('miner kicked to gather')
                    elif len(drone.orders) == 1:
                        if drone.is_carrying_minerals:
                            for order in drone.orders:
                                if order.ability.id == AbilityId.HARVEST_RETURN:
                                    if type(order.target) == int:
                                        if order.target != base.tag:
                                            if order.target != 0:
                                                drone(AbilityId.SMART, base) # HARVEST_RETURN with an argument
                                                self.listenframe_of_unit[miner] = self.frame + 5
                                                logger.info('miner kicked to correct base')
                        else: # not .is_carrying_minerals
                            for order in drone.orders:
                                if order.ability.id == AbilityId.MOVE:
                                    logger.info('follow-the-hatchery bug')
                                    drone(AbilityId.HARVEST_GATHER, patch)
                                    self.listenframe_of_unit[miner] = self.frame + 5
                                elif order.ability.id == AbilityId.HARVEST_GATHER:
                                    if type(order.target) == int:
                                        if order.target != patch.tag:
                                            if order.target != 0:
                                                drone(AbilityId.HARVEST_GATHER, patch)
                                                self.listenframe_of_unit[miner] = self.frame + 5
                                                logger.info('miner kicked to correct patch')
            if self.get_unit_job(drone) == Job.GASMINER:
                if self.frame >= self.listenframe_of_unit[miner]:
                    post = self.assign[miner]
                    gas = self.gas_of_postag(post)
                    expo = self.expo_of_postag[post]
                    base = self.minebase_of_expo_mfu[expo]
                    #
                    if len(drone.orders) == 0:
                        if drone.is_carrying_vespene:
                            drone(AbilityId.SMART, base) # HARVEST_RETURN with an argument
                            self.listenframe_of_unit[miner] = self.frame + 5
                            logger.info('gasminer kicked to return')
                        else: # not carrying vespene
                            drone(AbilityId.HARVEST_GATHER, gas)
                            self.listenframe_of_unit[miner] = self.frame + 5
                            logger.info('gasminer kicked to gather')
                    elif len(drone.orders) == 1:
                        if drone.is_carrying_vespene:
                            for order in drone.orders:
                                if order.ability.id == AbilityId.HARVEST_RETURN:
                                    if type(order.target) == int:
                                        if order.target != base.tag:
                                            if order.target != 0:
                                                drone(AbilityId.SMART, base) # HARVEST_RETURN with an argument
                                                self.listenframe_of_unit[miner] = self.frame + 5
                                                logger.info('miner kicked to correct base')
                        else: # not .is_carrying_vespene
                            for order in drone.orders:
                                if order.ability.id == AbilityId.HARVEST_GATHER:
                                    if type(order.target) == int:
                                        if order.target != gas.tag:
                                            if order.target != 0:
                                                drone(AbilityId.HARVEST_GATHER, gas)
                                                self.listenframe_of_unit[miner] = self.frame + 5
                                                logger.info('miner kicked to correct gasbuilding')

    async def speed_mining(self):
        # logger.info('game_step = ' + str(self.game_step))
        if self.game_step <= 4:
            # A full-speed drone moves 0.7 in 4 frames
            for drone in self.units(UnitTypeId.DRONE):
                if self.get_unit_job(drone) == Job.MIMMINER:
                    miner = drone.tag
                    dronepos = drone.position
                    post = self.assign[miner]
                    patchpos = self.position_of_postag(post)
                    patch = self.patch_of_postag(post)
                    expo = self.expo_of_postag[post]
                    base = self.minebase_of_expo_mfu[expo]
                    basepos = base.position.towards(patchpos, 2)
                    if miner not in self.info_start_frame:
                        pdist = self.distance(dronepos, patchpos)
                        if pdist < 3: # if far, do not start info phase
                            self.info_start_frame[miner] = self.frame + 4 * self.seconds
                            self.info_end_frame[miner] = self.frame + 16 * self.seconds
                            self.patchpoint_dist[miner] = 99999
                            self.patchpoint[miner] = patchpos
                            self.basepoint_dist[miner] = 99999
                            self.basepoint[miner] = basepos
                            self.hit_carrying[miner] = True
                    if miner in self.info_start_frame:
                        if self.frame < self.info_end_frame[miner]:
                            if self.frame >= self.info_start_frame[miner]:
                                pdist = self.distance(dronepos, patchpos)
                                bdist = self.distance(dronepos, basepos)
                                maxdist = self.distance(basepos, patchpos)
                                if bdist < maxdist: # inside circle
                                    if pdist < maxdist: # inside circle
                                        if pdist < self.patchpoint_dist[miner]:
                                            self.patchpoint_dist[miner] = pdist
                                            self.patchpoint[miner] = dronepos
                                        if bdist < self.basepoint_dist[miner]:
                                            self.basepoint_dist[miner] = bdist
                                            self.basepoint[miner] = dronepos
                        else: # speedmining
                            if self.frame >= self.listenframe_of_unit[miner]:
                                pdist = self.distance(dronepos, self.patchpoint[miner])
                                bdist = self.distance(dronepos, self.basepoint[miner])
                                if self.hit_carrying[miner]:
                                    if 0.5 < bdist < 2.0:
                                        if drone.is_carrying_minerals:
                                            drone.move(self.basepoint[miner])
                                            drone(AbilityId.SMART, base, queue=True)
                                            self.listenframe_of_unit[miner] = self.frame + 5
                                            self.hit_carrying[miner] = not self.hit_carrying[miner]
                                else: # hit not carrying
                                    if 0.5 < pdist < 2.0:
                                        if not drone.is_carrying_minerals:
                                            drone.move(self.patchpoint[miner])
                                            drone(AbilityId.SMART, patch, queue=True)
                                            self.listenframe_of_unit[miner] = self.frame + 5
                                            self.hit_carrying[miner] = not self.hit_carrying[miner]

    async def check_mining(self):
        for drone in self.units(UnitTypeId.DRONE):
            miner = drone.tag
            if self.get_unit_job(miner) == Job.MIMMINER:
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
                                    elif order.target == 0: # seen, but why?
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
                        if order.ability.id == AbilityId.MOVE:
                            successes += 1
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
                        logger.info('speedmining')
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
                if self.get_unit_job(unt) == Job.UNCLEAR:
                    unemployed += 1
                    an_unemployed = unt
                if self.get_unit_job(unt) == Job.VOLUNTEER:
                    volunteers += 1
                    a_volunteer = unt
            # idling volunteers
            if volunteers > 0:
                for unt in self.units(UnitTypeId.DRONE).idle:
                    tag = unt.tag
                    if self.get_unit_job(unt) == Job.VOLUNTEER:
                        if self.frame >= self.listenframe_of_unit[tag]:
                            self.set_unit_job(unt, Job.UNCLEAR)
                            volunteers -= 1
            # new volunteer
            if unemployed >= 3:
                unemployed -= 1
                unt = an_unemployed
                untpos = unt.position
                bestdist = 99999
                for patch in self.mineral_field:
                    respos = patch.position
                    post = self.postag_of_position(respos)
                    if post not in self.mimwork:
                        dist = self.distance(untpos, respos)
                        if dist < bestdist:
                            bestdist = dist
                            bestpatch = patch
                if bestdist < 99999:
                    patch = bestpatch
                    self.set_unit_job(unt, Job.VOLUNTEER)
                    unt.gather(patch)
                    self.listenframe_of_unit[unt.tag] = self.frame + self.seconds
                    volunteers += 1
                else:
                    unt = an_unemployed
                    goal = self.enemymain
                    for (typ,pos) in self.enemy_struc_mem:
                        goal = pos
                    for (typ,pos) in self.enemy_struc_mem:
                        if typ in self.all_halltypes:
                            goal = pos
                    unt.attack(goal)
                    self.set_unit_job(unt, Job.BERSERKER)
                    # drone berserkers are separate from army berserkers
            if unemployed < 2:
                if volunteers > 0:
                    unt = a_volunteer
                    self.set_unit_job(unt, Job.UNCLEAR)
                    volunteers -= 1
                    unemployed += 1
