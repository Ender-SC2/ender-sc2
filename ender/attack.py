# attack.py, Ender

import random
from collections import defaultdict
from math import cos, sin, pi
from typing import List

from loguru import logger

from ender.behavior import IBehavior
from ender.behavior.combat import (
    FocusFireCombatBehavior,
    MoreRangeBehavior,
    LessRangeBehavior,
    SameRangeBehavior,
    SidewardsBehavior,
    UprampBehavior,
)
from ender.job import Job
from ender.map_if import Map_if
from ender.tech import Tech
from ender.nydus import Nydus
from ender.utils.point_utils import distance, towards
from ender.utils.structure_utils import structure_radius
from sc2.constants import TARGET_AIR
from sc2.ids.ability_id import AbilityId
from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class Attack(Map_if, Tech, Nydus):

    __did_step0 = False
    # attackgoal is in nydus.py. For units pointattacking, where it is going
    defendgoal = None
    spray = {}
    casts = set()  # of (spellkind, pos, expiration)
    berserkers = set()
    kite_back = set()  # of unittype
    master = {}  # per slavetag a mastertag
    biles = set()  # enemy and own ravager biles
    bile_positions = set()  # positions where a bile will land (or has landed)
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
        UnitTypeId.SIEGETANK,
        UnitTypeId.LURKERMP,
        UnitTypeId.LURKERMPBURROWED,
        UnitTypeId.INFESTOR,
        UnitTypeId.GHOST,
        UnitTypeId.LIBERATORAG,
        UnitTypeId.SENTRY,
        UnitTypeId.COLOSSUS,
    }
    guard_structures = {
        UnitTypeId.SPORECRAWLER,
        UnitTypeId.PHOTONCANNON,
        UnitTypeId.BUNKER,
    }
    guard_structures_safe = {
        UnitTypeId.PYLON,
        UnitTypeId.COMMANDCENTER,
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
    may_spawn = {}  # timer for swarmhosts
    sh_forward = {}  # direction for swarmhosts
    sh_goal = None  # direction for swarmhosts
    sh_indiv_goal = {}  # should follow sh_goal
    dried = set()  # expo with neither minerals nor gas
    fresh = set()  # expo with minerals or gas
    behaviors: List[IBehavior] = [
        LessRangeBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
        MoreRangeBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
        SameRangeBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
        SidewardsBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
        FocusFireCombatBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
        UprampBehavior(jobs=[Job.DEFENDATTACK, Job.BIGATTACK, Job.BERSERKER]),
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
    enemynatural = None
    succer = {}  # viper loading
    succed = {}  # viper loading
    drawn = {}  # viper abducted

    #
    def __step0(self):
        #
        #
        #
        self.defendgoal = towards(self.ourmain, self.map_center, 8)
        self.kite_back = {UnitTypeId.BROODLORD, UnitTypeId.INFESTOR}
        for behavior in self.behaviors:
            behavior.setup(self, self)
        # enemynatural
        bestdist = 99999
        for pos in self.expansion_locations:
            dist = distance(pos, self.enemymain)
            if dist > 5:
                if dist < bestdist:
                    bestdist = dist
                    self.enemynatural = pos
        # bigattack_end
        self.bigattack_end = self.minutes  # this sets earliest bigattack at 2 minutes.
        #
        self.biletarget_no |= self.all_changelings
        #
        self.gathertime = 6 * self.seconds
        #

    async def on_step(self, iteration: int):
        await Map_if.on_step(self, iteration)
        await Tech.on_step(self, iteration)
        await Nydus.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.set_big_attack()
        await self.big_attack1()
        await self.big_attack2()
        await self.big_attack3()
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
        await self.slaves()
        await self.wounded()
        await self.guards()
        await self.banes()
        await self.do_dried()
        await self.dodge_biles()
        await self.bile()
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
                if self.defendgoal:
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
        if self.function_listens("renew_defendgoal", 8 * self.seconds):
            # myworth defenders
            myworth = 0.0
            for typ in self.all_armytypes:
                worth = self.worth(typ)
                for unt in self.units(typ):
                    if self.job_of_unit(unt) == Job.DEFENDATTACK:
                        myworth += worth
            # center of our halls
            n = -0.51
            center = n * self.ourmain
            for hall in self.townhalls:
                center = center + hall.position
                n += 1
            center = center / n
            # enecenter of enemy units on our half
            enecenter = self.ourmain
            eneworth = 1.0
            for tag in self.enemy_unit_mem:
                (typ, pos) = self.enemy_unit_mem[tag]
                if distance(pos, self.ourmain) < distance(pos, self.enemymain):
                    worth = self.worth(typ)
                    enecenter += worth * pos
                    eneworth += worth
            enecenter = enecenter / eneworth
            if eneworth < myworth < 4.0 * eneworth:
                center = enecenter
            # closest own hall
            bestval = 99999
            bestpos = None
            for hall in self.townhalls:
                pos = hall.position
                val = distance(pos, center)
                if val < bestval:
                    bestval = val
                    bestpos = pos
            if bestpos:
                self.defendgoal = towards(bestpos, self.map_center, 8)
                self.calc_gatherpoint()

    def calc_gatherpoint(self):
        if self.bigattackgoal and self.defendgoal:
            gp = (2 * self.bigattackgoal + self.defendgoal) / 3
            gp = self.map_around(gp, 4)
            self.gatherpoint = gp

    async def defend(self):
        if self.function_listens("defend", 20):
            if self.frame >= self.bigattack_end:
                thereisblue = False
                for unt in self.units(UnitTypeId.OVERSEER).idle:
                    tag = unt.tag
                    if self.blue_half(tag):
                        thereisblue = True
                for typ in self.all_armytypes:
                    if typ not in [
                        UnitTypeId.OVERSEERSIEGEMODE,
                        UnitTypeId.OVERLORDTRANSPORT,
                    ]:  # too slow
                        for unt in self.units(typ).idle:
                            tag = unt.tag
                            canrecruit = True
                            if typ == UnitTypeId.QUEEN:
                                if tag in self.queen_of_hall.values():
                                    canrecruit = False
                                if unt.energy == 200:
                                    # full energy queen better lay a tumor
                                    canrecruit = False
                            if typ == UnitTypeId.OVERSEER:
                                if self.blue_half(tag) != thereisblue:
                                    canrecruit = False
                            if canrecruit:
                                if self.frame >= self.listenframe_of_unit[tag]:
                                    # recruit
                                    if self.job_of_unit(unt) in [
                                        Job.UNCLEAR,
                                        Job.HANGER,
                                    ]:
                                        self.set_job_of_unit(unt, Job.DEFENDATTACK)
                                    # act
                                    if self.job_of_unit(unt) == Job.DEFENDATTACK:
                                        if self.defendgoal:
                                            self.attackgoal[tag] = self.defendgoal
                                            if distance(unt.position, self.defendgoal) > 8:
                                                self.attack_via_nydus(unt)
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
                        await self.client.chat_send("planning attack", team_only=False)
                        self.bigattacking = True
                        #
                        self.correct_speed()
                        # get approachdura
                        approachdura = 0
                        for typ in self.all_armytypes:
                            if typ not in {UnitTypeId.OVERSEERSIEGEMODE, UnitTypeId.QUEEN}:  # too slow
                                for unt in self.units(typ):
                                    if self.bigattackgoal and self.job_of_unit(unt) in {Job.UNCLEAR, Job.DEFENDATTACK}:
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

    async def big_attack1(self):
        if self.bigattacking:
            if self.function_listens("big_attack1", 19):
                # get some bigattack units, gather them
                for typ in self.all_armytypes:
                    if typ not in {UnitTypeId.OVERSEERSIEGEMODE, UnitTypeId.QUEEN}:  # too slow
                        for unt in self.units(typ):
                            tag = unt.tag
                            if self.frame >= self.listenframe_of_unit[tag]:
                                if self.bigattackgoal and self.job_of_unit(unt) in {Job.UNCLEAR, Job.DEFENDATTACK}:
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
                                            self.attack_via_nydus(unt)
                                            self.listenframe_of_unit[tag] = self.frame + 5
                                            self.attack_started[tag] = False

    async def big_attack2(self):
        if self.bigattacking:
            if self.function_listens("big_attack2", 19):
                # bigattack
                for typ in self.all_armytypes:
                    for unt in self.units(typ):
                        tag = unt.tag
                        if self.frame >= self.listenframe_of_unit[tag]:
                            if self.job_of_unit(unt) == Job.BIGATTACK:
                                if self.bigattackgoal and not self.attack_started[tag]:
                                    dist = distance(unt.position, self.bigattackgoal)
                                    speed = self.speed[typ] / self.seconds
                                    duration = dist / speed
                                    attackmoment = self.frame + duration
                                    if attackmoment < self.bigattack_end:
                                        if attackmoment >= self.bigattack_moment:
                                            # print('debug ' + unt.name + ' starts walking ' + str(duration))
                                            self.attackgoal[tag] = self.bigattackgoal
                                            self.attack_via_nydus(unt)
                                            self.listenframe_of_unit[tag] = self.frame + 5
                                            self.attack_started[tag] = True

    async def big_attack3(self):
        if self.bigattacking:
            if self.function_listens("big_attack3", 19):
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
                                            if self.bigattackgoal and self.attackgoal[tag] != self.bigattackgoal:
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
                                    if self.bigattackgoal:
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
                                if self.bigattackgoal:
                                    unt.attack(self.bigattackgoal)
                                    self.listenframe_of_unit[tag] = self.frame + 5
                                    self.attackgoal[tag] = self.bigattackgoal
                            elif self.bigattackgoal:
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
                            target = None
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
                            if canspray and target:
                                sprayers += 1
                                unt(abi, target)
                                self.spray[tag] = self.frame + 32.14 * self.seconds
                                self.set_job_of_unit(unt, Job.SPRAYER)
                                self.listenframe_of_unit[tag] = self.frame + 5
            # end sprayer
            for unt in self.units(UnitTypeId.CORRUPTOR).idle:
                if self.job_of_unit(unt) == Job.SPRAYER:
                    if self.frame >= self.listenframe_of_unit[unt.tag]:
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
            for vip in self.units(UnitTypeId.VIPER):
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
                        bestene = None
                        for ene in enes:  # DEBUG must exclude larva etc
                            if ene.tag not in self.drawn:
                                self.drawn[ene.tag] = 0
                            if self.frame >= self.drawn[ene.tag] + 5 * self.seconds:
                                worth = self.worth(ene.type_id)
                                if worth > bestworth:
                                    bestworth = worth
                                    bestene = ene
                        if bestene:
                            vip(draw, bestene)
                            self.drawn[bestene.tag] = self.frame
                # back
                if vip.energy < 60:
                    if self.job_of_unit(vip) != Job.TIRED:
                        vip.move(self.hospital)
                        self.set_job_of_unit(vip, Job.TIRED)

    async def vipers_slow(self):
        if self.function_listens("vipers_slow", 77):
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
                        bestdonor = None
                        for donor in donors:
                            dist = distance(donor.position, vip.position)
                            if dist < bestdist:
                                bestdist = dist
                                bestdonor = donor
                        if vip.energy >= 150:
                            self.set_job_of_unit(vip, Job.UNCLEAR)
                        elif bestdonor:
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
        # for swarmhosts
        if self.function_listens("set_sh_goal", 9 * self.seconds):
            self.sh_goal = self.enemymain
            mindist = 99999
            target = None
            for postag in self.enemy_struc_mem:
                (typ, pos) = self.enemy_struc_mem[postag]
                if typ in self.all_halltypes:
                    dist = distance(self.ourmain, pos)
                    if dist < mindist:
                        mindist = dist
                        target = pos
            if target:
                self.sh_goal = target

    def sh_throwspot(self, hatchpos: Point2) -> Point2:
        # for swarmhosts
        hatchheight = self.height(hatchpos)
        path = 15
        pos = towards(hatchpos, self.ourmain, path)
        posheight = self.height(pos)
        while (path < 25) and (posheight == hatchheight):
            path += 1
            pos = towards(hatchpos, self.ourmain, path)
            posheight = self.height(pos)
        # if at max, go back to normal
        if path == 25:
            path = 20
            pos = towards(hatchpos, self.ourmain, path)
        else:  # otherheight pos
            pos = towards(hatchpos, self.ourmain, path)
            pos = self.map_around_notheight(pos, hatchheight)
        return pos

    async def swarmhosts(self):
        if self.function_listens("swarmhosts", 9) and self.sh_goal:
            for sh in self.units(UnitTypeId.SWARMHOSTMP):
                tag = sh.tag
                if self.frame >= self.listenframe_of_unit[tag]:
                    if tag not in self.may_spawn:
                        self.may_spawn[tag] = 0
                    if tag not in self.sh_forward:
                        self.sh_forward[tag] = False
                    if tag not in self.sh_indiv_goal:
                        self.sh_indiv_goal[tag] = self.ourmain
                    #
                    if self.frame < self.may_spawn[tag] - 22 * self.seconds:
                        if self.sh_forward[tag]:
                            self.sh_forward[tag] = False
                            sh.move(self.hospital)
                    else:
                        # go forward
                        if self.sh_forward[tag]:
                            if self.sh_indiv_goal[tag] != self.sh_goal:
                                self.sh_indiv_goal[tag] = self.sh_goal
                                throwspot = self.sh_throwspot(self.sh_goal)
                                sh.move(throwspot)
                        else:
                            self.sh_forward[tag] = True
                            self.sh_indiv_goal[tag] = self.sh_goal
                            throwspot = self.sh_throwspot(self.sh_goal)
                            sh.move(throwspot)
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
                        if len(sh.orders) == 0:  # goal reached
                            locusts = True
                        if tag in self.last_health:  # being shot
                            if sh.health < self.last_health[tag]:
                                locusts = True
                        if self.enemy_units:
                            enemies = self.enemy_units.filter(lambda ene: ene.can_attack_ground)
                            if enemies:
                                enemy = enemies.closest_to(sh)
                                if distance(sh.position, enemy.position) < 8:
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
                hit: dict[Point2, int] = dict((throw, 0) for throw in throws)
                for throw in throws:
                    for target in targets:
                        if distance(throw, target) < radius:
                            hit[throw] += 1
                hits = 0
                bestthrow = None
                for throw in throws:
                    if hit[throw] > hits:
                        bestthrow = throw
                        hits = hit[throw]
                if hits > 0 and bestthrow:
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
                hit = defaultdict()
                for throwtarget in targets:
                    for target in targets:
                        if distance(throwtarget.position, target.position) < radius:
                            hit[throwtarget] += 1
                hits = 0
                besttarget = None
                for target in targets:
                    if hit[target] > hits:
                        besttarget = target
                        hits = hit[target]
                if hits > 0 and besttarget:
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
                        bestpos = None
                        for mas in self.units(UnitTypeId.BROODLORD):
                            if mas.tag == self.master[sla.tag]:
                                dist = distance(mas.position, sla.position)
                                if dist < bestdist:
                                    bestdist = dist
                                    bestpos = mas.position
                        if 3 < bestdist and bestpos:
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
                            away = towards(unt.position, enepos, -4)
                            away = towards(away, self.hospital, 5)
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
        # new biles
        # will also be used in function 'bile'.
        for effect in self.state.effects:
            if effect.id == EffectId.RAVAGERCORROSIVEBILECP:
                for bileposition in effect.positions:
                    if bileposition not in self.bile_positions:
                        self.bile_positions.add(bileposition)
                        self.biles.add((bileposition, self.frame + 60))
                        # how to detect a bile at the same position as an older bile?
        if self.function_listens("admin_biles", 25):
            # delete old biles
            todel = set()
            for (pos, landframe) in self.biles:
                if self.frame > landframe:
                    todel.add((pos, landframe))
            self.biles -= todel
            if len(self.biles) == 0:
                self.bile_positions = set()
        if self.function_listens("dodge_biles", 5):
            # dodge biles
            if len(self.biles) > 0:
                for typ in self.all_armytypes:
                    for unt in self.units(typ):
                        mustflee = False
                        abile = None
                        for (bileposition, landframe) in self.biles:
                            if distance(bileposition, unt.position) < unt.radius + 0.5:
                                if landframe - 2 * self.seconds < self.frame < landframe:
                                    mustflee = True
                                    abile = bileposition
                        if mustflee and abile:
                            if abile == unt.position:
                                to_point = towards(abile, self.ourmain, 2)
                            else:
                                to_point = towards(abile, unt.position, 2)
                            unt(AbilityId.MOVE_MOVE, to_point)

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
                        if distance(ravpos, enepos) < 9.5 + structure_radius[enetyp] / 2:
                            eneworth = self.worth(enetyp)
                            if distance(ravpos, enepos) > 9:
                                throwat = ravpos.towards(enepos, 9)
                            else:
                                throwat = enepos
                            if not self.willdie_structure(enetyp, enepos):
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
                                if not self.willdie_unit(ene):
                                    targets.append((2, -eneworth, throwat))
                    for postag in self.enemy_struc_mem:
                        (enetyp, enepos) = self.enemy_struc_mem[postag]
                        if distance(ravpos, enepos) < 9.5 + structure_radius[enetyp] / 2:
                            if enetyp in self.biletarget_buildings:
                                eneworth = self.worth(enetyp)
                                if distance(ravpos, enepos) > 9:
                                    throwat = ravpos.towards(enepos, 9)
                                else:
                                    throwat = enepos
                                if not self.willdie_structure(enetyp, enepos):
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
                                if not self.willdie_unit(ene):
                                    targets.append((0, -eneworth, throwat))
                    if len(targets) > 0:
                        targets.sort()
                        (urgency, eworth, bileposition) = targets[0]
                        rav(AbilityId.EFFECT_CORROSIVEBILE, bileposition)
                        self.bilecool[tag] = self.frame + 7.5 * self.seconds
                        # add to known biles
                        self.bile_positions.add(bileposition)
                        self.biles.add((bileposition, self.frame + 60))

    def willdie_structure(self, enetyp, enepos) -> bool:
        # enemy structure will die because of biles
        # usually the structure is visible
        biledamage = 60
        itshealth = 1000
        itsradius = structure_radius[enetyp] / 2
        for stru in self.enemy_structures(enetyp):
            if stru.position == enepos:
                itshealth = stru.health + stru.shield
                itsradius = stru.radius
        for (bileposition, landframe) in self.biles:
            if self.frame < landframe:
                if distance(bileposition, enepos) < itsradius + 0.5:
                    itshealth -= biledamage
        return itshealth < 0

    def willdie_unit(self, ene) -> bool:
        # enemy unit will die because of biles if it does not move.
        biledamage = 60
        itshealth = ene.health + ene.shield
        itsradius = ene.radius
        enepos = ene.position
        for (bileposition, landframe) in self.biles:
            if self.frame < landframe:
                if distance(bileposition, enepos) < itsradius + 0.5:
                    itshealth -= biledamage
        return itshealth < 0

    async def guards(self):
        if self.frame < 5 * self.minutes:
            if self.function_listens("guards", 10):
                defensive_mineral = self.mineral_field.closest_to(self.ourmain)
                need_target = set()
                released_guard = False
                # stray guards
                for worker in self.units(UnitTypeId.DRONE).sorted(lambda worker: worker.shield_health_percentage):
                    tag = worker.tag
                    pos = worker.position
                    if self.job_of_unit(worker) == Job.GUARD:
                        tohome = 99999
                        for hall in self.structures(UnitTypeId.HATCHERY):
                            dist = distance(pos, hall.position)
                            tohome = min(dist, tohome)
                        if not released_guard:
                            released_guard = True
                            worker.gather(defensive_mineral)
                            self.set_job_of_unit(worker, Job.UNCLEAR)
                        elif worker.weapon_cooldown > 8:
                            worker.gather(defensive_mineral)
                        elif worker.is_carrying_resource:
                            worker.return_resource()
                        elif tohome >= 25:
                            worker.gather(defensive_mineral)
                            self.set_job_of_unit(worker, Job.UNCLEAR)
                        else:
                            need_target.add(worker.tag)
                attackers = self.enemy_units.not_flying.filter(lambda u: self.townhalls.closest_distance_to(u) < 30)
                structures = self.enemy_structures.filter(
                    lambda s: self.townhalls.closest_distance_to(s) < 30
                    and (
                        s.type_id in self.guard_structures
                        and s.build_progress < 0.95
                        or s.type_id in self.guard_structures_safe
                    )
                )

                # drone guards
                attacking_amount = max(0, len(attackers) - int(self.supply_army))

                if attacking_amount > 2:
                    wish_defenders = attacking_amount + 1
                else:
                    wish_defenders = attacking_amount
                wish_defenders += len(structures) * 3
                defenders = set()
                for worker in self.workers.filter(lambda w: self.job_of_unit(w) == Job.GUARD):
                    logger.info(f"Guard {worker.tag} at {worker.position}")
                    tag = worker.tag
                    defenders.add(tag)
                    if tag in need_target:
                        if attackers:
                            worker.attack(attackers.closest_to(worker).position)
                        elif structures:
                            worker.attack(structures.closest_to(worker))

                while len(defenders) < wish_defenders:
                    # Take defenders with high health
                    workers = self.workers.filter(
                        lambda filter_worker: self.job_of_unit(filter_worker)
                        in [Job.MIMMINER, Job.GASMINER, Job.UNCLEAR]
                    ).sorted(
                        lambda sorter_worker: (
                            sorter_worker.shield_health_percentage,
                            -(attackers or structures).closest_distance_to(sorter_worker),
                        ),
                        reverse=True,
                    )
                    if workers:
                        worker = workers.first
                        tag = worker.tag
                        self.set_job_of_unit(worker, Job.GUARD)
                        defenders.add(tag)
                        if attackers:
                            worker.attack(attackers.closest_to(worker).position)
                        elif structures:
                            worker.attack(structures.closest_to(worker))
                    else:
                        break
                while len(defenders) > wish_defenders:
                    # Release defenders with the lowest health first
                    workers = self.workers.filter(lambda filter_worker: filter_worker.tag in defenders).sorted(
                        lambda sorter_worker: sorter_worker.shield_health_percentage
                    )
                    if workers:
                        worker = workers.first
                        defenders.remove(worker.tag)
                        self.set_job_of_unit(worker, Job.UNCLEAR)
                        worker.gather(defensive_mineral)
                    else:
                        break

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
                # max 2 within radius 9
                amclose = 0
                for atag in self.burbanes:
                    (apos, aframe) = self.burbanes[atag]
                    if distance(apos, pos) < 9:
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
            for expo in self.expansion_locations:
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
                    for expo in self.expansion_locations:
                        if distance(expo, stru.position) < 10:
                            if expo in self.dried:
                                mindist = 99999
                                goal = None
                                for to_expo in self.fresh:
                                    dist = distance(to_expo, expo)
                                    if dist < mindist:
                                        mindist = dist
                                        goal = to_expo
                                if goal:
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
            anunt = None
            for chtyp in self.all_changelings:
                for unt in self.units(chtyp):
                    n += 1
                    if self.job_of_unit(unt) == Job.SPY:
                        nspies += 1
                    else:
                        anunt = unt
            if 2 * nspies < n and anunt:
                unt = anunt
                self.set_job_of_unit(unt, Job.SPY)
            # follow
            for chtyp in self.all_changelings:
                for unt in self.units(chtyp).idle:
                    if self.job_of_unit(unt) == Job.SPY:
                        bestdist = 30
                        bestene = None
                        for enetyp in {UnitTypeId.ZERGLING, UnitTypeId.ZEALOT, UnitTypeId.MARINE}:
                            for ene in self.enemy_units(enetyp):
                                dist = distance(ene.position, unt.position)
                                if dist < bestdist:
                                    bestdist = dist
                                    bestene = ene
                        if bestene:
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
