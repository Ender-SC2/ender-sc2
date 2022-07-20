# attack.py, Ender

import random
from math import cos, sin, pi
from typing import List

from loguru import logger

from ender.behavior import IBehavior
from ender.behavior.combat import (
    FocusFireCombatBehavior,
    RepositionBehavior,
    ForwardBehavior,
    BackBehavior,
    SidewardsBehavior,
)
from ender.job import Job
from ender.map_if import Map_if
from ender.tech import Tech
from ender.utils.point_utils import distance
from sc2.constants import TARGET_AIR
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class Attack(Map_if, Tech):

    __did_step0 = False
    attackgoal = {}  # for units pointattacking, where it is going
    defendgoal = None
    spray = {}
    casts = set()  # of (spellkind, pos, expiration)
    berserkers = set()
    kite_back = set()  # of unittype
    master = {}  # per slavetag a mastertag
    biles = set()  # enemy and own ravager biles
    bilecool = {}  # per ravager, when it is ready to bile
    biletarget_buildings = {
        UnitTypeId.PHOTONCANNON,
        UnitTypeId.MISSILETURRET,
        UnitTypeId.BUNKER,
        UnitTypeId.SPINECRAWLER,
        UnitTypeId.SPORECRAWLER,
        UnitTypeId.SPAWNINGPOOL,
    }
    biletarget_units = {
        UnitTypeId.SIEGETANKSIEGED,
        UnitTypeId.RAVAGER,
        UnitTypeId.CORRUPTOR,
        UnitTypeId.GHOST,
        UnitTypeId.LIBERATORAG,
        UnitTypeId.SENTRY,
        UnitTypeId.COLOSSUS,
    }
    biletarget_no = {UnitTypeId.LARVA, UnitTypeId.EGG, UnitTypeId.AUTOTURRET, UnitTypeId.MULE}
    # bigattacking in common.py
    bigattack_moment = -99999
    bigattack_end = 0  # the end of a bigattack, also allowing a new bigattack
    bigattackgoal = None
    gathertime = 0  # 6 seconds for grouping up the bigattack army.
    gatherpoint = None  # 2/3 bigattack_goal + 1/3 defendgoal
    attack_started = {}  # separate gather phase from actual attack phase
    last_catch = {}  # for burrowed banelings
    burbanes = {}  # of positions where a own burrowed baneling is or was. Per tag: (pos, upframe)
    dontburrow = {}  # A baneling can have temporary don't-burrow status. Per tag: downframe.
    pos_of_blocker = {}
    blocker_of_pos = {}
    may_spawn = {}  # timer for swarmhosts
    sh_forward = {}  # direction for swarmhosts
    sh_goal = None  # direction for swarmhosts
    dried = set()  # expo with neither minerals nor gas
    fresh = set()  # expo with minerals or gas
    behaviors: List[IBehavior] = [
        ForwardBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
        FocusFireCombatBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
        RepositionBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
        BackBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
        SidewardsBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
    ]
    detector_types = [
        UnitTypeId.MISSILETURRET,
        UnitTypeId.PHOTONCANNON,
        UnitTypeId.SPORECRAWLER,
        UnitTypeId.OVERSEER,
        UnitTypeId.OVERSEERSIEGEMODE,
        UnitTypeId.OBSERVER,
        UnitTypeId.OBSERVERSIEGEMODE,
        UnitTypeId.RAVEN,
    ]
    circle = []  # unit circle with n points
    circler_frames = {}  # per circlertag: amount of frames for one circle.
    circler_pos = {}
    circler_next_frame = 0  # common for all circlers
    enemy_nat_blocked = False
    want_enemy_nat_block = True
    enemynatural = None
    succer = {}  # viper loading
    succed = {}  # viper loading
    drawn = {}  # viper abducted

    #
    def __step0(self):
        #
        #
        #
        self.defendgoal = self.ourmain.towards(self.map_center, 8)
        self.kite_back = {UnitTypeId.BROODLORD, UnitTypeId.INFESTOR}
        for behavior in self.behaviors:
            behavior.setup(self, self)
        # enemynatural
        bestdist = 99999
        for pos in self.expansion_locations_list:
            dist = distance(pos, self.enemymain)
            if dist > 5:
                if dist < bestdist:
                    bestdist = dist
                    self.enemynatural = pos
        # bigattack_end
        self.bigattack_end = self.minutes  # this sets earliest bigattack at 2 minutes, and latest migattack.
        #
        self.biletarget_no |= self.all_changelings
        #
        self.want_enemy_nat_block = random.random() < 0.5

    async def on_step(self, iteration: int):
        await Map_if.on_step(self, iteration)
        await Tech.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.set_big_attack()
        await self.big_attack()
        for behavior in self.behaviors:
            await behavior.on_step(iteration)
        await self.renew_defendgoal()
        await self.defend()
        await self.berserk()
        await self.corrupt()
        await self.infest()
        await self.vipers()
        await self.vipers_slow()
        await self.set_sh_goal()
        await self.swarmhosts()
        await self.blocker()
        await self.slaves()
        await self.wounded()
        await self.guards()
        await self.banes()
        await self.do_dried()
        await self.dodge_biles()
        await self.bile()
        await self.circle_blockers()
        await self.spies()

    def find_bigattackgoal(self):
        if self.function_listens("find_bigattackgoal", 10):
            goals = []  # of (dumbness,dist_to_enemymain,pos)
            goals.append((2, 0, self.enemymain))
            for postag in self.enemy_struc_mem:
                (typ, pos) = self.enemy_struc_mem[postag]
                dist = distance(pos, self.enemymain)
                goals.append((1, dist, pos))
            for postag in self.enemy_struc_mem:
                (typ, pos) = self.enemy_struc_mem[postag]
                if typ in self.all_halltypes:
                    dist = distance(pos, self.defendgoal)
                    goals.append((0, dist, pos))
            goals.sort()
            (dumbness, dist_to_enemymain, pos) = goals[0]
            pos = self.improve_flyer_point(pos)
            self.bigattackgoal = pos
            self.calc_gatherpoint()

    async def renew_defendgoal(self):
        # sometimes renew defendgoal
        if self.function_listens("renew_defendgoal", self.minutes):
            n = -0.51
            center = n * self.ourmain
            for hall in self.townhalls:
                center = center + hall.position
                n += 1
            center = center / n
            bestval = 99999
            for hall in self.townhalls:
                pos = hall.position
                val = distance(pos, center)
                if val < bestval:
                    bestval = val
                    bestpos = pos
            if bestval < 99999:
                self.defendgoal = bestpos.towards(self.map_center, 8)
                self.calc_gatherpoint()

    def calc_gatherpoint(self):
        gp = (2 * self.bigattackgoal + self.defendgoal) / 3
        gp = self.map_around(gp, 4)
        self.gatherpoint = gp
        self.gathertime = 6 * self.seconds

    async def defend(self):
        if self.function_listens("defend", 20):
            if self.frame >= self.bigattack_end:
                for typ in self.all_armytypes:
                    if typ not in {UnitTypeId.OVERSEERSIEGEMODE}:  # too slow
                        for unt in self.units(typ).idle:
                            tag = unt.tag
                            canrecruit = True
                            if typ == UnitTypeId.QUEEN:
                                if tag in self.queen_of_hall.values():
                                    canrecruit = False
                                if unt.energy == 200:
                                    # full energy queen better lay a tumor
                                    canrecruit = False
                            if canrecruit:
                                if self.frame >= self.listenframe_of_unit[tag]:
                                    # recruit
                                    if self.job_of_unit(unt) == Job.UNCLEAR:
                                        self.set_job_of_unit(unt, Job.DEFENDATTACK)
                                    # act
                                    if self.job_of_unit(unt) == Job.DEFENDATTACK:
                                        self.attackgoal[tag] = self.defendgoal
                                        if distance(unt.position, self.defendgoal) > 8:
                                            unt.attack(self.defendgoal)
                                            self.listenframe_of_unit[tag] = self.frame + 5
            # dismiss full energy queens
            for unt in self.units(UnitTypeId.QUEEN):
                if self.job_of_unit(unt) == Job.DEFENDATTACK:
                    if unt.energy == 200:
                        self.set_job_of_unit(unt, Job.UNCLEAR)


    async def set_big_attack(self):
        if self.function_listens("set_big_attack", 33):
            # goal
            self.find_bigattackgoal()
            # ended?
            if self.bigattacking:
                # only ovis then end
                if self.frame >= self.bigattack_moment + 15 * self.seconds:
                    ground_damage = False
                    for typ in self.all_armytypes:
                        for unt in self.units(typ):
                            if self.job_of_unit(unt) == Job.BIGATTACK:
                                if (unt.can_attack_ground) or (unt.type_id == UnitTypeId.BROODLORD):
                                    ground_damage = True
                    if not ground_damage:
                        logger.info("ending bigattack by lack of ground damage")
                        self.bigattack_end = self.frame
                # time end bigattack
                if self.frame >= self.bigattack_end:
                    self.bigattacking = False
                    logger.info("bigattack ended")
            # attack now?
            if self.frame > self.bigattack_end + 30 * self.seconds:
                logger.info("bigattack planning time")
                now = True
                for typ in self.result_plan:
                    if typ in self.all_armytypes:
                        having = len(self.units(typ))
                        tomake = self.result_plan[typ]
                        for mor in self.morph:  # morph[ravager] == roach
                            if self.morph[mor] == typ:
                                having += len(self.units(mor))
                        if 5 * having < 4 * tomake:
                            now = False
                            logger.info("not enough " + typ.name)
                # full army
                logger.info("armysupply " + str(self.army_supply_used) + " of " + str(self.supplycap_army))
                if (self.army_supply_used >= self.supplycap_army - 5) or (self.supply_used >= 190):
                    now = True
                    logger.info(
                        "armysupply " + str(self.army_supply_used) + " of " + str(self.supplycap_army) + " (or 190)"
                    )
                # wait for cocoons
                cocoons = 0
                for typ in [
                    UnitTypeId.BROODLORDCOCOON,
                    UnitTypeId.RAVAGERCOCOON,
                    UnitTypeId.BANELINGCOCOON,
                    UnitTypeId.LURKERMPEGG,
                ]:
                    cocoons += len(self.units(typ))
                if cocoons >= 2:
                    logger.info("wait for cocoons")
                    now = False
                # wait for supplytrick
                if self.supplytricking:
                    logger.info("wait for supplytrick")
                    now = False
                # waiting long
                if self.frame > self.bigattack_end + 10 * self.minutes:
                    now = True
                    logger.info("ten minute rule")
                #
                if now:
                    self.wave_count += 1
                    wanttrade = True
                    if self.nbases >= self.nenemybases + 2:
                        wanttrade = False
                    if (self.army_supply_used >= self.supplycap_army - 10) or (self.supply_used >= 180):
                        wanttrade = True
                    if wanttrade:
                        # report
                        logger.info("PLANNING BIGATTACK!")
                        self.bigattacking = True
                        #
                        self.correct_speed()
                        # get approachdura
                        approachdura = 0
                        for typ in self.all_armytypes:
                            if typ not in {UnitTypeId.OVERSEERSIEGEMODE, UnitTypeId.QUEEN}:  # too slow
                                for unt in self.units(typ):
                                    if self.job_of_unit(unt) in {Job.UNCLEAR, Job.DEFENDATTACK}:
                                        dist = distance(unt.position, self.bigattackgoal)
                                        speed = self.speed[typ] / self.seconds
                                        duration = dist / speed
                                        approachdura = max(duration, approachdura)
                        # fix attackmoment
                        logger.info("approachdura " + str(approachdura))
                        self.bigattack_moment = self.frame + approachdura + self.gathertime
                        logger.info("bigattack moment will be " + str(self.bigattack_moment))
                        self.bigattack_end = self.bigattack_moment + 30 * self.seconds
                        logger.info("bigattack end will be = " + str(self.bigattack_end))
                    else:  # not want trade
                        logger.info("SKIPPING BIGATTACK!")
                        await self.client.chat_send("skipping attack", team_only=False)
                        self.bigattack_moment = self.frame
                        self.bigattack_end = self.frame + 30 * self.seconds
                        logger.info("earliest bigattack moment will be " + str(self.frame + self.minutes))

    async def big_attack(self):
        if self.bigattacking:
            # get some bigattack units, gather them
            for typ in self.all_armytypes:
                if typ not in {UnitTypeId.OVERSEERSIEGEMODE, UnitTypeId.QUEEN}:  # too slow
                    for unt in self.units(typ):
                        tag = unt.tag
                        if self.frame >= self.listenframe_of_unit[tag]:
                            if self.job_of_unit(unt) in {Job.UNCLEAR, Job.DEFENDATTACK}:
                                dist = distance(unt.position, self.bigattackgoal)
                                speed = self.speed[typ] / self.seconds
                                duration = dist / speed
                                gathermoment = self.frame + duration + self.gathertime
                                attackmoment = self.frame + duration
                                if attackmoment < self.bigattack_end:
                                    if gathermoment >= self.bigattack_moment:
                                        # print('debug ' + unt.name + ' starts walking ' + str(duration))
                                        self.set_job_of_unit(unt, Job.BIGATTACK)
                                        self.attackgoal[tag] = self.gatherpoint
                                        unt.attack(self.gatherpoint)
                                        self.listenframe_of_unit[tag] = self.frame + 5
                                        self.attack_started[tag] = False
            # bigattack
            for typ in self.all_armytypes:
                for unt in self.units(typ):
                    tag = unt.tag
                    if self.frame >= self.listenframe_of_unit[tag]:
                        if self.job_of_unit(unt) == Job.BIGATTACK:
                            if not self.attack_started[tag]:
                                dist = distance(unt.position, self.bigattackgoal)
                                speed = self.speed[typ] / self.seconds
                                duration = dist / speed
                                attackmoment = self.frame + duration
                                if attackmoment < self.bigattack_end:
                                    if attackmoment >= self.bigattack_moment:
                                        # print('debug ' + unt.name + ' starts walking ' + str(duration))
                                        self.attackgoal[tag] = self.bigattackgoal
                                        unt.attack(self.bigattackgoal)
                                        self.listenframe_of_unit[tag] = self.frame + 5
                                        self.attack_started[tag] = True
            # whip them (or release them)
            for typ in self.all_armytypes:
                for unt in self.units(typ).idle:
                    tag = unt.tag
                    if self.job_of_unit(unt) == Job.BIGATTACK:
                        if self.attack_started[tag]:
                            if self.frame >= self.listenframe_of_unit[tag]:
                                if self.frame >= self.bigattack_end:
                                    self.set_job_of_unit(unt, Job.UNCLEAR)
                                else:
                                    # why does it idle?
                                    goal = self.attackgoal[tag]
                                    dist = distance(unt.position, goal)
                                    if dist < 5:
                                        # it reached its goal
                                        if self.attackgoal[tag] != self.bigattackgoal:
                                            self.attackgoal[tag] = self.bigattackgoal
                                            unt.attack(self.bigattackgoal)
                                            self.listenframe_of_unit[tag] = self.frame + 5
                                    else:
                                        # it was distracted
                                        unt.attack(goal)
                                        self.listenframe_of_unit[tag] = self.frame + 5

    async def berserk(self):
        # berserkers are units that will fight to die to free supply
        # get some berserkers
        if self.function_listens("berserk", 20):
            if self.army_supply_used >= 90:
                self.berserkers = self.berserkers and self.living
                if len(self.berserkers) < 6:
                    tomake = 1
                    for typ in {UnitTypeId.ZERGLING, UnitTypeId.ROACH}:
                        for unt in self.units(typ).idle:
                            tag = unt.tag
                            if self.job_of_unit(unt) not in {Job.BERSERKER, Job.HOLY}:
                                if tomake > 0:
                                    tomake -= 1
                                    self.set_job_of_unittag(tag, Job.BERSERKER)
                                    self.berserkers.add(tag)
                                    self.find_bigattackgoal()
                                    self.attackgoal[tag] = self.bigattackgoal
                                    unt.attack(self.bigattackgoal)
                                    self.listenframe_of_unit[tag] = self.frame + 5
            # whip them
            for typ in self.all_armytypes:
                for unt in self.units(typ).idle:
                    tag = unt.tag
                    if self.job_of_unit(unt) == Job.BERSERKER:
                        if self.frame >= self.listenframe_of_unit[tag]:
                            # why does it idle?
                            goal = self.attackgoal[tag]
                            dist = distance(unt.position, goal)
                            if dist < 5:
                                # it reached its goal
                                self.find_bigattackgoal()
                                unt.attack(self.bigattackgoal)
                                self.listenframe_of_unit[tag] = self.frame + 5
                                self.attackgoal[tag] = self.bigattackgoal
                            else:
                                # it was distracted
                                unt.attack(self.bigattackgoal)
                                self.listenframe_of_unit[tag] = self.frame + 5

    async def corrupt(self):
        if self.function_listens("corrupt", 10):
            sprayers = self.job_count(Job.SPRAYER)
            for unt in self.units(UnitTypeId.CORRUPTOR):
                tag = unt.tag
                if sprayers < 7:
                    if tag in self.attackgoal:
                        goal = self.attackgoal[tag]
                        if distance(unt.position, goal) < 6:
                            abi = AbilityId.CAUSTICSPRAY_CAUSTICSPRAY
                            canspray = True
                            if tag in self.spray:
                                canspray = self.frame >= self.spray[tag]
                            if canspray:
                                canspray = False
                                for ene in self.enemy_structures:  # currently visible
                                    if ene.position == goal:
                                        # dismiss edge case 1 corruptor is left over
                                        if ene.health >= 200:
                                            canspray = True
                                            target = ene
                            if canspray:
                                sprayers += 1
                                unt(abi, target)
                                self.spray[tag] = self.frame + 32.14 * self.seconds
                                self.set_job_of_unit(unt, Job.SPRAYER)
                                self.listenframe_of_unit[tag] = self.frame + 5
            # end sprayer
            for unt in self.units(UnitTypeId.CORRUPTOR).idle:
                if self.job_of_unit(unt) == Job.SPRAYER:
                    if self.frame >= self.listenframe_of_unit[tag]:
                        self.set_job_of_unit(unt, Job.UNCLEAR)

    async def infest(self):
        if self.function_listens("infest", 10):
            for unt in self.units(UnitTypeId.INFESTOR):
                pos = unt.position
                fungal = AbilityId.FUNGALGROWTH_FUNGALGROWTH
                # fungal
                if unt.energy >= 75:
                    musthit = 3
                    if unt.shield_health_percentage < 0.5:
                        musthit = 1
                    throw = self.cast_at_point("fungal", pos, 10, 2.25, 3, musthit)
                    if throw != self.nowhere:
                        unt(fungal, throw)
                # back
                if unt.energy < 60:
                    if self.job_of_unit(unt) != Job.TIRED:
                        unt.move(self.hospital)
                        self.set_job_of_unit(unt, Job.TIRED)
                elif self.job_of_unit(unt) == Job.TIRED:
                    self.set_job_of_unit(unt, Job.UNCLEAR)

    async def vipers(self):
        if self.function_listens("vipers", 5):
            blind = AbilityId.BLINDINGCLOUD_BLINDINGCLOUD  # range 11 rad 2 eng 100
            draw = AbilityId.EFFECT_ABDUCT  # range 9 eng 75
            attackair = AbilityId.PARASITICBOMB_PARASITICBOMB  # range 8 rad 3 eng 125
            load = AbilityId.VIPERCONSUMESTRUCTURE_VIPERCONSUME  # 200 damage 50 eng 14 sec
            for vip in self.units(UnitTypeId.VIPER):
                tag = vip.tag
                pos = vip.position
                # blind
                if vip.energy >= 100:
                    musthit = 3
                    if vip.shield_health_percentage < 0.5:
                        musthit = 1
                    throw = self.cast_at_point("blind", pos, 11, 2, 5.71, musthit)
                    if throw != self.nowhere:
                        vip(blind, throw)
                # attackair
                if vip.energy >= 125:
                    musthit = 3
                    if vip.shield_health_percentage < 0.5:
                        musthit = 1
                    throw = self.cast_at_unit("attackair", pos, 8, 3, 7, musthit)
                    if throw is not None:
                        vip(attackair, throw)
                # draw
                if vip.energy >= 75:
                    if self.job_of_unit(vip) == Job.SLAVE:
                        enes = self.enemy_units.closer_than(9, vip.position)
                        bestworth = 400
                        for ene in enes:  # DEBUG must exclude larva etc
                            if ene.tag not in self.drawn:
                                self.drawn[ene.tag] = 0
                            if self.frame >= self.drawn[ene.tag] + 5 * self.seconds:
                                worth = self.worth(ene.type_id)
                                if worth > bestworth:
                                    bestworth = worth
                                    bestene = ene
                        if bestworth > 400:
                            vip(draw, bestene)
                            self.drawn[bestene.tag] = self.frame
                # back
                if vip.energy < 60:
                    if self.job_of_unit(vip) != Job.TIRED:
                        vip.move(self.hospital)
                        self.set_job_of_unit(vip, Job.TIRED)

    async def vipers_slow(self):
        if self.function_listens("vipers_slow", 77):
            blind = AbilityId.BLINDINGCLOUD_BLINDINGCLOUD  # range 11 rad 2 eng 100
            draw = AbilityId.EFFECT_ABDUCT  # range 9 eng 75
            attackair = AbilityId.PARASITICBOMB_PARASITICBOMB  # range 8 rad 3 eng 125
            load = AbilityId.VIPERCONSUMESTRUCTURE_VIPERCONSUME  # 200 damage 50 eng 14 sec
            # administration
            todel = set()
            for strutag in self.succed:
                (viptag, endtime) = self.succed[strutag]
                if self.frame > endtime:
                    todel.add(strutag)
            for strutag in todel:
                del self.succed[strutag]
            todel = set()
            for viptag in self.succer:
                (strutag, endtime) = self.succer[viptag]
                if self.frame > endtime:
                    todel.add(viptag)
            for viptag in todel:
                del self.succer[viptag]
            # donors
            donors = set()
            for typ in self.all_normalstructuretypes:
                for stru in self.structures(typ):
                    if stru.health >= 300:
                        if stru.tag not in self.succed:
                            donors.add(stru)
            for vip in self.units(UnitTypeId.VIPER):
                # load
                if self.job_of_unit(vip) == Job.TIRED:
                    if vip.energy == 200:
                        self.set_job_of_unit(vip, Job.UNCLEAR)
                    if vip.tag not in self.succer:
                        bestdist = 99999
                        for donor in donors:
                            dist = distance(donor.position, vip.position)
                            if dist < bestdist:
                                bestdist = dist
                                bestdonor = donor
                        if vip.energy >= 150:
                            self.set_job_of_unit(vip, Job.UNCLEAR)
                        elif bestdist < 99999:
                            # succ
                            donors.remove(bestdonor)
                            vip(load, bestdonor)
                            endtime = self.frame + 14 * self.seconds + 0.5 * bestdist
                            self.succed[bestdonor.tag] = (vip.tag, endtime)
                            self.succer[vip.tag] = (bestdonor.tag, endtime)
                        else:  # cannot succ
                            if vip.energy >= 60:  # waiting works too
                                self.set_job_of_unit(vip, Job.UNCLEAR)

    async def set_sh_goal(self):
        if self.function_listens("set_sh_goal", 9 * self.seconds):
            self.sh_goal = self.enemymain
            mindist = 99999
            for postag in self.enemy_struc_mem:
                (typ, pos) = self.enemy_struc_mem[postag]
                if typ in self.all_halltypes:
                    dist = distance(self.ourmain, pos)
                    if dist < mindist:
                        mindist = dist
                        target = pos
            if mindist < 99999:
                self.sh_goal = target

    async def swarmhosts(self):
        if self.function_listens("swarmhosts", 9):
            for sh in self.units(UnitTypeId.SWARMHOSTMP):
                tag = sh.tag
                if self.frame >= self.listenframe_of_unit[tag]:
                    if tag not in self.may_spawn:
                        self.may_spawn[tag] = 0
                    if tag not in self.sh_forward:
                        self.sh_forward[tag] = False
                    #
                    if self.frame < self.may_spawn[tag] - 22 * self.seconds:
                        if self.sh_forward[tag]:
                            self.sh_forward[tag] = False
                            sh.move(self.hospital)
                    else:
                        if not self.sh_forward[tag]:
                            goal = self.sh_goal.towards(self.ourmain, 15)
                            self.sh_forward[tag] = True
                            sh.move(goal)
            for sh in self.units(UnitTypeId.SWARMHOSTMP) | self.units(UnitTypeId.SWARMHOSTBURROWEDMP):
                tag = sh.tag
                self.set_job_of_unit(sh, Job.WALKER)
                spawn = AbilityId.EFFECT_SPAWNLOCUSTS
                if self.frame >= self.listenframe_of_unit[tag]:
                    if tag not in self.may_spawn:
                        self.may_spawn[tag] = 0
                    #
                    if self.frame >= self.may_spawn[tag]:
                        locusts = False
                        if len(sh.orders) == 0:
                            locusts = True
                        if tag in self.last_health:
                            if sh.health < self.last_health[tag]:
                                locusts = True
                        if locusts:
                            sh(spawn, self.sh_goal)
                            self.may_spawn[tag] = self.frame + 43 * self.seconds + 20
                            self.listenframe_of_unit[tag] = self.frame + self.seconds

    def cast_at_point(self, kind, pos, rrange, radius, duration, musthit) -> Point2:
        result = self.nowhere
        targets = set()
        throws = set()
        for ene in self.enemy_units:
            dist = distance(ene.position, pos)
            if dist < rrange + radius:
                validtarget = True  # e.g.infest
                if ene.type_id in {UnitTypeId.BROODLING, UnitTypeId.AUTOTURRET, UnitTypeId.LARVA, UnitTypeId.EGG}:
                    validtarget = False
                if kind == "blind":
                    validtarget = False
                    for weapon in ene._weapons:
                        if weapon.type in TARGET_AIR:  # added because usually my army flies
                            if weapon.range >= 1:
                                validtarget = True
                    if ene.is_flying:
                        validtarget = False
                if validtarget:
                    if dist < rrange:
                        throws.add(ene.position)
                        targets.add(ene.position)
                    elif dist < rrange + radius:
                        throws.add(pos.towards(ene.position, rrange))
                        targets.add(ene.position)
        if len(targets) >= musthit:
            # delete targets in casts
            todel = set()
            for (akind, throw, expiration) in self.casts:
                if akind == kind:
                    if self.frame < expiration:
                        for target in targets:
                            if distance(target, throw) < radius:
                                todel.add(target)
            targets -= todel
            #
            if len(targets) >= musthit:
                hit = dict((throw, 0) for throw in throws)
                for throw in throws:
                    for target in targets:
                        if distance(throw, target) < radius:
                            hit[throw] += 1
                hits = 0
                for throw in throws:
                    if hit[throw] > hits:
                        bestthrow = throw
                        hits = hit[throw]
                if hits > 0:
                    result = bestthrow
                    self.casts.add((kind, bestthrow, self.frame + duration * self.seconds))
                    #
                    # administration
                    todel = set()
                    for (akind, throw, expiration) in self.casts:
                        if self.frame >= expiration:
                            todel.add((akind, throw, expiration))
                    self.casts -= todel
        return result

    def cast_at_unit(self, kind, pos, rrange, radius, duration, musthit):
        result = None
        targets = set()
        for ene in self.enemy_units:
            dist = distance(ene.position, pos)
            if dist < rrange:
                validtarget = True
                if ene.type_id in {UnitTypeId.BROODLING, UnitTypeId.AUTOTURRET, UnitTypeId.LARVA, UnitTypeId.EGG}:
                    validtarget = False
                if kind == "attackair":
                    validtarget = ene.is_flying
                if validtarget:
                    targets.add(ene)
        if len(targets) >= musthit:
            # delete targets in casts
            todel = set()
            for (akind, throw, expiration) in self.casts:
                if akind == kind:
                    if self.frame < expiration:
                        for target in targets:
                            if distance(target.position, throw) < radius:
                                todel.add(target)
            targets -= todel
            #
            if len(targets) >= musthit:
                hit = dict((target, 0) for target in targets)
                for throwtarget in targets:
                    for target in targets:
                        if distance(throwtarget.position, target.position) < radius:
                            hit[throwtarget] += 1
                hits = 0
                for target in targets:
                    if hit[target] > hits:
                        besttarget = target
                        hits = hit[target]
                if hits > 0:
                    result = besttarget
                    self.casts.add((kind, besttarget.position, self.frame + duration * self.seconds))
                    #
                    # administration
                    todel = set()
                    for (akind, throw, expiration) in self.casts:
                        if self.frame >= expiration:
                            todel.add((akind, throw, expiration))
                    self.casts -= todel
        return result

    def make_circle(self, n):
        # n points on the unitcircle
        self.circle = []
        for i in range(0, n):
            alfa = 2 * pi * i / n
            point = Point2((cos(alfa), sin(alfa)))
            self.circle.append(point)

    def start_block_circle(self, circleframes, tag, expopos):
        self.circler_frames[tag] = circleframes
        self.make_circle(circleframes)
        self.circler_pos[tag] = []
        radius = circleframes / 25  # should be wider than the actual walked circle. Speed?
        for point in self.circle:
            self.circler_pos[tag].append(Point2((expopos.x + radius * point.x, expopos.y + radius * point.y)))

    async def circle_blockers(self):
        # high apm
        if len(self.circler_frames) > 0:
            if self.frame >= self.circler_next_frame + 6:
                for circler_type in {UnitTypeId.DRONE, UnitTypeId.ZERGLING}:
                    for blo in self.units(circler_type):
                        tag = blo.tag
                        if tag in self.circler_frames:
                            if self.job_of_unittag(tag) == Job.BLOCKER:
                                circleframes = self.circler_frames[tag]
                                blocker_pole = self.frame % circleframes
                                goal = self.circler_pos[tag][blocker_pole]
                                blo.move(goal)

    async def blocker(self):
        if self.function_listens("blocker", 31):
            # zergling or job or freeexpo is gone
            todel = set()
            for tag in self.pos_of_blocker:
                pos = self.pos_of_blocker[tag]
                if pos not in self.freeexpos:
                    todel.add((tag, pos))
                if tag in self.living:
                    job = self.job_of_unittag(tag)
                    if job != Job.BLOCKER:
                        # logger.info(job) # debug
                        todel.add((tag, pos))
                else:
                    # logger.info('dead') # debug
                    todel.add((tag, pos))
            for (tag, pos) in todel:
                del self.pos_of_blocker[tag]
                del self.blocker_of_pos[pos]
                if tag in self.circler_frames:
                    del self.circler_frames[tag]
                if self.job_of_unittag(tag) == Job.BLOCKER:
                    self.set_job_of_unittag(tag, Job.UNCLEAR)
            # recruit natblocker
            if self.enemy_race == Race.Zerg:
                startframe = 7
            else:
                startframe = 13 * self.seconds
            if self.frame > startframe:
                if self.want_enemy_nat_block:
                    if not self.enemy_nat_blocked:
                        pos = self.enemynatural
                        for unt in self.units(UnitTypeId.DRONE):
                            tag = unt.tag
                            if self.job_of_unittag(tag) == Job.MIMMINER and not unt.is_carrying_resource:
                                self.enemy_nat_blocked = True
                                # connect
                                self.pos_of_blocker[tag] = pos
                                self.blocker_of_pos[pos] = tag
                                self.set_job_of_unit(unt, Job.BLOCKER)
                                self.start_block_circle(96, tag, pos)
                                break
            # recruit zerglings
            if self.nbases >= 3:  # 3 finished bases
                for unt in self.units(UnitTypeId.ZERGLING):
                    tag = unt.tag
                    job = self.job_of_unit(unt)
                    if job in {Job.UNCLEAR, Job.DEFENDATTACK}:
                        pos = self.nowhere
                        dist = 99999
                        for apos in self.freeexpos:
                            adist = distance(apos, self.enemymain)
                            if apos not in self.blocker_of_pos:
                                if adist < dist:
                                    dist = adist
                                    pos = apos
                        if dist < 99999:
                            # connect
                            self.pos_of_blocker[tag] = pos
                            self.blocker_of_pos[pos] = tag
                            self.set_job_of_unit(unt, Job.BLOCKER)
                            self.start_block_circle(76, tag, pos)
            # burrow
            bur = AbilityId.BURROWDOWN_ZERGLING
            if UpgradeId.BURROW in self.state.upgrades:
                for unt in self.units(UnitTypeId.ZERGLING):
                    tag = unt.tag
                    if self.job_of_unit(unt) == Job.BLOCKER:
                        pos = self.pos_of_blocker[tag]
                        if pos not in self.current_expandings:
                            if tag in self.circler_frames:
                                del self.circler_frames[tag]
                            burpoint = pos.towards(self.ourmain, 2)
                            unt.move(burpoint)
                            self.listenframe_of_unit[tag] = self.frame + 4 * self.seconds
                            if distance(unt.position, burpoint) < 4:
                                unt(bur, queue=True)
            # unblock
            bup = AbilityId.BURROWUP_ZERGLING
            todel = set()
            for pos in self.blocker_of_pos:
                if pos in self.current_expandings:
                    todel.add(pos)
            for pos in todel:
                tag = self.blocker_of_pos[pos]
                del self.blocker_of_pos[pos]
                del self.pos_of_blocker[tag]
                if tag in self.circler_frames:
                    del self.circler_frames[tag]
                self.set_job_of_unittag(tag, Job.UNCLEAR)
                for unt in self.units(UnitTypeId.ZERGLINGBURROWED):
                    if unt.tag == tag:
                        if self.frame >= self.listenframe_of_unit[tag]:
                            unt(bup)
                            self.listenframe_of_unit[tag] = self.frame + 3 * self.seconds

    async def slaves(self):
        if self.function_listens("slaves", 61):
            candidates = {
                UnitTypeId.INFESTOR,
                UnitTypeId.CORRUPTOR,
                UnitTypeId.ROACH,
                UnitTypeId.OVERSEER,
                UnitTypeId.MUTALISK,
                UnitTypeId.VIPER,
                UnitTypeId.HYDRALISK,
                UnitTypeId.OVERLORDTRANSPORT,
                UnitTypeId.ULTRALISK,
            }  # not the zerglings
            # dead master
            todel = set()
            for slatag in self.master:
                if slatag in self.living:
                    if self.job_of_unittag(slatag) == Job.SLAVE:
                        mastag = self.master[slatag]
                        if mastag not in self.living:
                            self.set_job_of_unittag(slatag, Job.UNCLEAR)
                            todel.add(slatag)
            for slatag in todel:
                del self.master[slatag]
            # master wounded
            for sla in self.units:
                if self.job_of_unit(sla) == Job.SLAVE:
                    slatag = sla.tag
                    mastag = self.master[slatag]
                    if mastag in self.living:
                        if self.job_of_unittag(mastag) in [Job.SCRATCHED, Job.WOUNDED]:
                            self.set_job_of_unit(sla, Job.UNCLEAR)
                            del self.master[slatag]
            # slave changed typ
            todel = set()
            for sla in self.units:
                slatag = sla.tag
                if self.job_of_unit(sla) == Job.SLAVE:
                    typ = sla.type_id
                    if typ not in candidates:
                        self.set_job_of_unit(sla, Job.UNCLEAR)
                        todel.add(slatag)
            for slatag in todel:
                del self.master[slatag]
            # free all slaves
            if len(self.units(UnitTypeId.BROODLORD)) < 3:
                for typ in candidates:
                    for sla in self.units(typ):
                        if self.job_of_unit(sla) == Job.SLAVE:
                            self.set_job_of_unit(sla, Job.UNCLEAR)
                            del self.master[sla.tag]
            # make all slaves
            if len(self.units(UnitTypeId.BROODLORD)) >= 3:
                for typ in candidates:
                    for sla in self.units(typ):
                        itsjob = self.job_of_unit(sla)
                        if itsjob not in [
                            Job.SLAVE,
                            Job.SCRATCHED,
                            Job.TIRED,
                            Job.WOUNDED,
                            Job.BERSERKER,
                            Job.HOLY,
                            Job.BLOCKER,
                            Job.TRANSPORTER,
                        ]:
                            if (typ != UnitTypeId.OVERLORDTRANSPORT) or (not self.blue_half(sla.tag)):
                                self.set_job_of_unit(sla, Job.SLAVE)
                                self.master[sla.tag] = self.units(UnitTypeId.BROODLORD).random.tag
            # move slaves
            for typ in candidates:
                for sla in self.units(typ):
                    if self.job_of_unit(sla) == Job.SLAVE:
                        bestdist = 99999
                        for mas in self.units(UnitTypeId.BROODLORD):
                            if mas.tag == self.master[sla.tag]:
                                dist = distance(mas.position, sla.position)
                                if dist < bestdist:
                                    bestdist = dist
                                    bestpos = mas.position
                        if 3 < bestdist < 99999:
                            sla.move(bestpos)

    async def wounded(self):
        for unt in self.units:
            typ = unt.type_id
            if typ not in {
                UnitTypeId.BANELING,
                UnitTypeId.OVERLORDTRANSPORT,
                UnitTypeId.DRONE,
                UnitTypeId.BROODLING,
                UnitTypeId.LOCUSTMP,
            }:
                if unt.tag in self.last_health:
                    if unt.health < 0.7 * self.last_health[unt.tag]:
                        if self.job_of_unit(unt) not in [
                            Job.BERSERKER,
                            Job.HOLY,
                            Job.NURSE,
                            Job.WOUNDED,
                            Job.SCRATCHED,
                            Job.TRANSPORTER,
                        ]:
                            if unt.health < unt.health_max - 100:
                                self.set_job_of_unit(unt, Job.WOUNDED)
                            else:
                                self.set_job_of_unit(unt, Job.SCRATCHED)
                            if len(self.enemy_units) > 0:
                                enepos = self.enemy_units.closest_to(unt.position).position
                            else:
                                enepos = self.enemymain
                            away = unt.position.towards(enepos, -4)
                            away = away.towards(self.hospital, 5)
                            unt.move(away)
                            unt.move(self.hospital, queue=True)
        if self.function_listens("wounded", 63):
            for typ in self.all_unittypes:
                for unt in self.units(typ):
                    if self.job_of_unit(unt) in [Job.WOUNDED, Job.SCRATCHED]:
                        if 2 * unt.health >= unt.health_max:
                            self.set_job_of_unit(unt, Job.UNCLEAR)
            for unt in self.units(UnitTypeId.ROACH):
                if self.job_of_unit(unt) in [Job.WOUNDED, Job.SCRATCHED]:
                    if distance(unt.position, self.hospital) < 10:
                        if 2 * unt.health < unt.health_max:
                            if UpgradeId.BURROW in self.state.upgrades:
                                unt(AbilityId.BURROWDOWN_ROACH)
            for unt in self.units(UnitTypeId.ROACHBURROWED):
                if self.job_of_unit(unt) in [Job.WOUNDED, Job.SCRATCHED]:
                    if distance(unt.position, self.hospital) < 15:
                        if unt.health >= 0.9 * unt.health_max:
                            unt(AbilityId.BURROWUP_ROACH)

    async def dodge_biles(self):
        if self.function_listens("admin_biles", 25):
            # delete old biles
            todel = set()
            for (pos, landframe) in self.biles:
                if self.frame > landframe:
                    todel.add((pos, landframe))
            self.biles -= todel
        if self.function_listens("dodge_biles", 5):
            # new biles
            for effect in self.state.effects:
                if effect.id == EffectId.RAVAGERCORROSIVEBILECP:
                    for bileposition in effect.positions:
                        if bileposition not in self.biles:
                            self.biles.add((bileposition, self.frame + 60))
            # dodge biles
            if len(self.biles) > 0:
                for typ in self.all_armytypes:
                    for unt in self.units(typ):
                        mustflee = False
                        for (bileposition, landframe) in self.biles:
                            if distance(bileposition, unt.position) < 1:
                                if landframe - 2 * self.seconds < self.frame < landframe:
                                    mustflee = True
                                    abile = bileposition
                        if mustflee:
                            if abile == unt.position:
                                topoint = abile.towards(self.ourmain, 2)
                            else:
                                topoint = abile.towards(unt.position, 2)
                            unt(AbilityId.MOVE_MOVE, topoint)

    async def bile(self):
        if self.function_listens("bile", 19):
            for rav in self.units(UnitTypeId.RAVAGER):
                tag = rav.tag
                ravpos = rav.position
                if tag not in self.bilecool:
                    self.bilecool[tag] = 0
                if self.frame >= self.bilecool[tag]:
                    targets = []
                    for postag in self.enemy_struc_mem:
                        (enetyp, enepos) = self.enemy_struc_mem[postag]
                        if distance(ravpos, enepos) < 9.5 + self.size_of_structure[enetyp] / 2:
                            eneworth = self.worth(enetyp)
                            if distance(ravpos, enepos) > 9:
                                throwat = ravpos.towards(enepos, 9)
                            else:
                                throwat = enepos
                            targets.append((3, -eneworth, throwat))
                    for ene in self.enemy_units:
                        enepos = ene.position
                        if ene.type_id not in self.biletarget_no:
                            eneworth = self.worth(ene.type_id)
                            if distance(ravpos, ene.position) < 9.5 + ene.radius:
                                if distance(ravpos, enepos) > 9:
                                    throwat = ravpos.towards(enepos, 9)
                                else:
                                    throwat = enepos
                                targets.append((2, -eneworth, throwat))
                    for postag in self.enemy_struc_mem:
                        (enetyp, enepos) = self.enemy_struc_mem[postag]
                        if distance(ravpos, enepos) < 9.5 + self.size_of_structure[enetyp] / 2:
                            if enetyp in self.biletarget_buildings:
                                eneworth = self.worth(enetyp)
                                if distance(ravpos, enepos) > 9:
                                    throwat = ravpos.towards(enepos, 9)
                                else:
                                    throwat = enepos
                                targets.append((1, -eneworth, throwat))
                    for ene in self.enemy_units:
                        enepos = ene.position
                        if distance(ravpos, ene.position) < 9.5 + ene.radius:
                            if ene.type_id in self.biletarget_units:
                                eneworth = self.worth(ene.type_id)
                                if distance(ravpos, enepos) > 9:
                                    throwat = ravpos.towards(enepos, 9)
                                else:
                                    throwat = enepos
                                targets.append((0, -eneworth, throwat))
                    if len(targets) > 0:
                        targets.sort()
                        (urgency, eworth, besttargetpos) = targets[0]
                        # do not bile double (except on sieged tank)
                        if urgency > 0:  # target not sieged tank
                            targetfound = False
                            for (urgency, eworth, targetpos) in targets:
                                if not targetfound:
                                    double = False
                                    for (bileposition, landframe) in self.biles:
                                        if self.frame < landframe:
                                            if distance(targetpos, bileposition) < 1:
                                                double = True
                                    if not double:
                                        targetfound = True
                                        besttargetpos = targetpos
                        #
                        rav(AbilityId.EFFECT_CORROSIVEBILE, besttargetpos)
                        self.bilecool[tag] = self.frame + 7.5 * self.seconds

    async def guards(self):
        if self.frame < 5 * self.minutes:
            if self.function_listens("guards", 10):
                defensive_mineral = self.mineral_field.closest_to(self.ourmain)
                need_target = set()
                released_guard = False
                # stray guards
                for unt in self.units(UnitTypeId.DRONE).sorted(lambda worker: worker.shield_health_percentage):
                    tag = unt.tag
                    pos = unt.position
                    if self.job_of_unit(unt) == Job.GUARD:
                        tohome = 99999
                        for hall in self.structures(UnitTypeId.HATCHERY):
                            dist = distance(pos, hall.position)
                            tohome = min(dist, tohome)
                        if not released_guard:
                            released_guard = True
                            unt.gather(defensive_mineral)
                            self.set_job_of_unit(unt, Job.UNCLEAR)
                        elif unt.weapon_cooldown > 8:
                            unt.gather(defensive_mineral)
                        elif unt.is_carrying_resource:
                            unt.return_resource()
                        elif tohome >= 10:
                            unt.gather(defensive_mineral)
                            self.set_job_of_unit(unt, Job.UNCLEAR)
                        else:
                            need_target.add(unt.tag)
                # per hatchery
                for hatchery in self.structures(UnitTypeId.HATCHERY):
                    if hatchery.build_progress >= 0.5:
                        an_attacker = None
                        closest_dist = 9999
                        attackers = 0
                        for ene in self.enemy_units.not_flying:
                            dist = distance(ene.position, hatchery.position)
                            if dist < 10:
                                attackers += 1
                                if dist < closest_dist:
                                    an_attacker = ene
                                    closest_dist = dist
                        defenders = set()
                        for unt in self.units(UnitTypeId.DRONE):
                            tag = unt.tag
                            if self.job_of_unit(unt) == Job.GUARD:
                                if distance(unt.position, hatchery.position) < 10:
                                    defenders.add(tag)
                                    if tag in need_target and an_attacker:
                                        unt.attack(an_attacker.position)
                        # drone guards
                        attackers = max(0, attackers - int(self.supply_army))
                        if attackers > 2:
                            wish_defenders = attackers + 1
                        else:
                            wish_defenders = attackers
                        if len(defenders) < wish_defenders:
                            # Defenders should have the highest health
                            for unt in self.units(UnitTypeId.DRONE).sorted(
                                lambda worker: worker.shield_health_percentage, reverse=True
                            ):
                                if len(defenders) >= wish_defenders:
                                    break
                                tag = unt.tag
                                if self.job_of_unit(unt) in [Job.MIMMINER, Job.GASMINER, Job.UNCLEAR]:
                                    if distance(unt.position, hatchery.position) < 10:
                                        self.set_job_of_unit(unt, Job.GUARD)
                                        defenders.add(tag)
                                        unt.attack(an_attacker)
                        if len(defenders) > wish_defenders:
                            # Release defenders with the lowest health first
                            for unt in self.units(UnitTypeId.DRONE).sorted(
                                lambda worker: worker.shield_health_percentage
                            ):
                                if len(defenders) <= wish_defenders:
                                    break
                                tag = unt.tag
                                if tag in defenders:
                                    defenders.remove(tag)
                                    self.set_job_of_unit(unt, Job.UNCLEAR)
                                    unt.gather(defensive_mineral)

    async def banes(self):
        bur = AbilityId.BURROWDOWN_BANELING
        burup = AbilityId.BURROWUP_BANELING
        bang = AbilityId.EXPLODE_EXPLODE
        for unt in self.units(UnitTypeId.BANELING):
            pos = unt.position
            burrow = False
            for ene in self.enemy_units:
                if ene.type_id not in self.all_workertypes:
                    if distance(ene.position, pos) < 10:
                        if unt.tag in self.dontburrow:
                            if self.frame >= self.dontburrow[unt.tag]:
                                burrow = True
                        else:
                            burrow = True
            if burrow:
                # detected?
                for ene in self.enemy_units:
                    if distance(ene.position, pos) < 10:
                        if ene.type_id in self.detector_types:
                            burrow = False
                for effect in self.state.effects:
                    if effect.id == EffectId.SCANNERSWEEP:
                        for effectpos in effect.positions:
                            if distance(effectpos, pos) < 13.5:  # scanrange + 0.5
                                burrow = False
                # max 2 within radius 7
                amclose = 0
                for atag in self.burbanes:
                    (apos, aframe) = self.burbanes[atag]
                    if distance(apos, pos) < 7:
                        amclose += 1
                if amclose >= 2:
                    burrow = False
                if burrow:
                    upframe = self.frame + self.minutes
                    self.burbanes[unt.tag] = (pos, upframe)
                    unt(bur)
        # explode
        for unt in self.units(UnitTypeId.BANELINGBURROWED):
            pos = unt.position
            # radius = 2.2
            catch = set()
            smallradius = 1.9
            escaping = set()
            bigradius = 2.2
            for ene in self.enemy_units:
                if not ene.is_flying:
                    dist = distance(ene.position, pos)
                    if dist < smallradius:
                        catch.add(ene.tag)
                    if dist < bigradius:
                        escaping.add(ene.tag)
            if unt.tag in self.last_catch:
                last_catch = self.last_catch[unt.tag] & escaping
            else:
                last_catch = set()
            if len(catch) < len(last_catch):
                unt(bang)
                # chosen is to ignore administration of burbanes
            self.last_catch[unt.tag] = catch
        # upframe
        for unt in self.units(UnitTypeId.BANELINGBURROWED):
            tag = unt.tag
            if tag in self.burbanes:
                (pos, upframe) = self.burbanes[tag]
                if self.frame >= upframe:
                    unt(burup)
                    del self.burbanes[tag]
                    self.dontburrow[tag] = self.frame + 6 * self.seconds
        # dontburrow administration
        if self.frame % 37 == 0:
            todel = set()
            for tag in self.dontburrow:
                if self.frame >= self.dontburrow[tag]:
                    todel.add(tag)
            for tag in todel:
                del self.dontburrow[tag]

    async def do_dried(self):
        if self.function_listens("do_dried", 21 * self.seconds):
            # dried bases
            self.dried = set()
            self.fresh = set()
            geysers_nonemp = self.vespene_geyser.filter(lambda gey: gey.has_vespene)
            geysers_nonemp_pos = [gey.position for gey in geysers_nonemp]
            mineral_pos = [patch.position for patch in self.mineral_field]
            for expo in self.expansion_locations_list:
                has_ore = False
                for ore_pos in geysers_nonemp_pos:
                    if distance(ore_pos, expo) < 10:
                        has_ore = True
                for ore_pos in mineral_pos:
                    if distance(ore_pos, expo) < 10:
                        has_ore = True
                if has_ore:
                    self.fresh.add(expo)
                else:
                    self.dried.add(expo)
            # uproot
            if len(self.fresh) > 0:
                for expo in self.dried:
                    for typ in {UnitTypeId.SPINECRAWLER, UnitTypeId.SPORECRAWLER}:
                        for stru in self.structures(typ):
                            pos = stru.position
                            if distance(pos, expo) < 10:
                                if typ == UnitTypeId.SPINECRAWLER:
                                    up = AbilityId.SPINECRAWLERUPROOT_SPINECRAWLERUPROOT
                                else:
                                    up = AbilityId.SPORECRAWLERUPROOT_SPORECRAWLERUPROOT
                                stru(up)
                                self.listenframe_of_structure[stru.tag] = self.frame + self.seconds + 10
        # downroot (often)
        for typ in {UnitTypeId.SPINECRAWLERUPROOTED, UnitTypeId.SPORECRAWLERUPROOTED}:
            for stru in self.structures(typ).idle:
                tag = stru.tag
                if self.frame >= self.listenframe_of_structure[tag]:
                    for expo in self.expansion_locations_list:
                        if distance(expo, stru.position) < 10:
                            if expo in self.dried:
                                mindist = 99999
                                for to_expo in self.fresh:
                                    dist = distance(to_expo, expo)
                                    if dist < mindist:
                                        mindist = dist
                                        goal = to_expo
                                point = goal.towards(expo, 8)
                                stru.move(point)
                                self.listenframe_of_structure[tag] = self.frame + 5
                            else:
                                # rooting is in making.py
                                self.to_root.add(tag)

    async def spies(self):
        if self.function_listens("spies", 1.6 * self.seconds):
            # half of the changelings get Job.SPY
            n = 0
            nspies = 0
            for chtyp in self.all_changelings:
                for unt in self.units(chtyp):
                    n += 1
                    if self.job_of_unit(unt) == Job.SPY:
                        nspies += 1
                    else:
                        anunt = unt
            if 2 * nspies < n:
                unt = anunt
                self.set_job_of_unit(unt, Job.SPY)
            # follow
            for chtyp in self.all_changelings:
                for unt in self.units(chtyp).idle:
                    if self.job_of_unit(unt) == Job.SPY:
                        bestdist = 30
                        for enetyp in {UnitTypeId.ZERGLING, UnitTypeId.ZEALOT, UnitTypeId.MARINE}:
                            for ene in self.enemy_units(enetyp):
                                dist = distance(ene.position, unt.position)
                                if dist < bestdist:
                                    bestdist = dist
                                    bestene = ene
                        if bestdist < 30:
                            unt.attack(bestene)
                        else:
                            goal = self.random_mappoint()
                            unt.attack(goal)

    def random_mappoint(self) -> Point2:
        return Point2(
            (random.randrange(self.map_left, self.map_right), random.randrange(self.map_bottom, self.map_top))
        )

    def improve_flyer_point(self, in_point: Point2) -> Point2:
        point = in_point
        goodrange = 8  # range plus radius plus radius
        changed = True
        for steps in range(5):
            if changed:
                changed = False
                for postag in self.enemy_struc_mem:
                    (typ, pos) = self.enemy_struc_mem[postag]
                    if typ in {UnitTypeId.PHOTONCANNON, UnitTypeId.SPORECRAWLER, UnitTypeId.MISSILETURRET}:
                        if distance(point, pos) < goodrange:
                            point = pos.towards(point, goodrange)
                            changed = True
        return point
