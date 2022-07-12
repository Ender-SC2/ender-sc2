# creep.py, Ender

import random
from typing import Optional

from loguru import logger

from ender.job import Job
from ender.map_if import Map_if
from ender.utils.point_utils import distance
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class Creep(Map_if):

    __did_step0 = False
    dx = 0 # to try different creep locations
    dy = 0 # to try different creep locations
    activecreep = set() # tumors that have not spread yet
    activecreeppos = {} # for activecreep, its position
    moms = set() # of (pos,momtag) for a spread attempt
    creepstyle = 0
    creepdirection = [] # directions creep may go
    directionfinish = [] # closer tumors will end this direction
    different_directions = 0
    directionx_of_tumor = {} # for activecreep, a directionindex
    tries = {} # for activecreep, how often did it try to make a tumor
    next_directionx = 0
    creeplords = set() # overlords to spread creep for tumor steps
    creeplord_state = {} # free/moving/dropping
    creeplord_goal = {} # place where this overlord will creep
    creeplord_free = {} # the frame the overlord can be reused
    creepdropping = {} # all overlords etc, when having a lair, will have creepdrop on.
                        # The creepdropping switch is turned off when morphing.
    #

    def __step0(self):
        self.init_creepstyle()
        #
        if self.enemy_race != Race.Zerg:
            # do not creep on expansionlocations
            for pos in self.expansion_locations_list:
                self.map_nocreep(pos, 5)
        #

    async def on_step(self, iteration: int):
        await Map_if.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.creep_spread()
        await self.re_direction()
        await self.queencreep()
        await self.do_creeplord()
        await self.creepdrop()

    def init_creepstyle(self):
        self.creepdirection = []
        self.directionfinish = []
        if self.creepstyle == 0: # aggressive
            for epo in self.expansion_locations_list:
                 if distance(epo,self.enemymain) < 70:
                     self.creepdirection.append(epo)
                     self.directionfinish.append(12)
        elif self.creepstyle == 1: # all bases
            for epo in self.expansion_locations_list:
                 self.creepdirection.append(epo)
                 self.directionfinish.append(12)
        elif self.creepstyle == 2: # mapedges
            breadth = self.map_right - self.map_left
            height = self.map_top - self.map_bottom
            for dx in range(0,5):
                for dy in range(0,5):
                    if (dx==0) or (dx==4) or (dy==0) or (dy==4):
                        self.creepdirection.append(Point2((self.map_left + dx * breadth / 4, 
                                                           self.map_bottom + dy * height / 4)))
            self.directionfinish = [9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9]
        self.different_directions = len(self.creepdirection)
        if self.next_directionx >= self.different_directions:
            self.next_directionx = 0
        for tum in self.directionx_of_tumor:
            if self.directionx_of_tumor[tum] >= self.different_directions:
                self.directionx_of_tumor[tum] = 0

    async def re_direction(self):
        # if a creepgoal is reached, overwrite it with some other creepgoal.
        if self.frame % 31 == 30: # rarely
            # against execution slowness, restricted to 20 minutes
            if self.frame < 20 * self.minutes:
                for directionx in range(0,len(self.creepdirection)):
                    goal = self.creepdirection[directionx]
                    finish = self.directionfinish[directionx]
                    reached = False
                    for typ in self.all_tumortypes:
                        for stru in self.structures(typ):
                            pos = stru.position
                            if distance(pos,goal) < finish:
                                reached = True
                    if reached:
                        altx = random.randrange(0,len(self.creepdirection))
                        self.creepdirection[directionx] = self.creepdirection[altx]
                        self.directionfinish[directionx] = self.directionfinish[altx]
                self.different_directions = len(set(self.creepdirection))
                if (self.creepstyle < 2) and (self.different_directions == 1):
                    self.creepstyle += 1
                    #print('creepstyle ' + str(self.creepstyle))
                    self.init_creepstyle()
                if (self.creepstyle == 0) and (self.frame > 7 * self.minutes):
                    self.creepstyle += 1
                    #print('creepstyle ' + str(self.creepstyle))
                    self.init_creepstyle()
                if (self.creepstyle == 1) and (self.frame > 14 * self.minutes):
                    self.creepstyle += 1
                    #print('creepstyle ' + str(self.creepstyle))
                    self.init_creepstyle()

    def creepable(self, point) -> bool:
        # for a point on the halfgrid, with halves.
        ok = False
        if self.map_can_plan_creep(point,1):
            if self.has_creep(point):
                ok = True
        return ok

    def creepable_ask_lord(self, point) -> bool:
        # for a point on the halfgrid, with halves.
        ok = False
        if self.map_can_plan_creep(point,1):
            if self.has_creep(point):
                ok = True
            else:
                self.ask_lord(point)
        return ok

    def random_direction(self, pos,tag):
        self.directionx_of_tumor[tag] = self.next_directionx
        self.next_directionx = (self.next_directionx + 1) % len(self.creepdirection)
        self.correct_direction(pos,tag)

    def correct_direction(self, pos,tag):
        # tag is in self.directionx_of_tumor
        # let it change direction if it is close to the directionpoint.
        directionx = self.directionx_of_tumor[tag]
        dirpoint = self.creepdirection[directionx]
        dirfin = self.directionfinish[directionx]
        while (distance(pos,dirpoint) < dirfin) and (self.different_directions > 1):
            self.directionx_of_tumor[tag] = self.next_directionx
            self.next_directionx = (self.next_directionx + 1) % len(self.creepdirection)
            directionx = self.directionx_of_tumor[tag]
            dirpoint = self.creepdirection[directionx]
                   
    async def queencreep(self):
        # get some creep queens
        for unt in self.units(UnitTypeId.QUEEN).idle:
            if self.job_of_unit(unt) == Job.UNCLEAR:
                if unt.energy >= 27: # inject pickup is at 23
                    if self.frame >= self.listenframe_of_unit[unt.tag]:
                        self.set_job_of_unit(unt, Job.CREEPER)
        # move to its spot
        for unt in self.units(UnitTypeId.QUEEN).idle:
            if self.job_of_unit(unt) == Job.CREEPER:
                if self.frame >= self.listenframe_of_unit[unt.tag]:
                    itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(unt.position)
                    itsspot = itshatch.position.towards(self.map_center,9)
                    dist = distance(unt.position,itsspot)
                    if dist > 4:
                        unt.move(itsspot)
                        self.listenframe_of_unit[unt.tag] = self.frame + 5
        # make creeptumor
        for unt in self.units(UnitTypeId.QUEEN).idle:
            if self.job_of_unit(unt) == Job.CREEPER:
                if self.frame >= self.listenframe_of_unit[unt.tag]:
                    if unt.energy >= 25:
                        untpos = unt.position
                        center = Point2((round(untpos.x - 0.5) + 0.5,round(untpos.y - 0.5) + 0.5))
                        altpoint = center
                        ok = self.creepable(altpoint)
                        radius = 0
                        dx = 0
                        dy = 0
                        while (not ok) and (radius < 5):
                            dx += 1
                            if dx > radius:
                                dy += 1
                                dx = -radius
                                if dy > radius:
                                    radius += 1
                                    dy = -radius
                                    dx = -radius
                            x = center.x + dx
                            y = center.y + dy
                            altpoint = Point2((x, y))
                            ok = self.creepable(altpoint)
                        if ok and (radius < 5):
                            it = UnitTypeId.CREEPTUMORQUEEN
                            pos = altpoint
                            unt(self.creation[it],pos)
                            self.map_plan(pos, 1)
                        self.set_job_of_unit(unt, Job.UNCLEAR)
                        self.listenframe_of_unit[unt.tag] = self.frame + 100
        
    async def creep_spread(self):
        if self.frame % 3 == 2:
            # against execution slowness, restricted to 20 minutes
            if self.frame < 20 * self.minutes:
                # change random vibration over ([-2,2],[-2,2])
                self.dx += 1
                if self.dx == 3:
                    self.dx = -2
                    self.dy += 1
                    if self.dy == 3:
                        self.dy = -2
                # activecreep
                for stru in self.structures(UnitTypeId.CREEPTUMORQUEEN):
                    if stru.tag not in self.activecreep:
                        self.activecreep.add(stru.tag)
                        self.activecreeppos[stru.tag] = stru.position
                        self.random_direction(stru.position,stru.tag)
                        self.tries[stru.tag] = 0
                        self.map_build_nodel(stru.position,1)
                for stru in self.structures(UnitTypeId.CREEPTUMOR):
                    if stru.tag not in self.activecreep:
                        self.activecreep.add(stru.tag)
                        self.activecreeppos[stru.tag] = stru.position
                        self.random_direction(stru.position,stru.tag)
                        self.tries[stru.tag] = 0
                        self.map_build_nodel(stru.position,1)
                        # this is doughter, end mom's activecreep
                        for (pos,momtag) in self.moms:
                            if pos == stru.position:
                                if momtag in self.activecreep: # usually yes
                                    self.directionx_of_tumor[stru.tag] = self.directionx_of_tumor[momtag] # go straight
                                    self.correct_direction(stru.position,stru.tag)
                                    self.activecreep.remove(momtag)
                                    del self.activecreeppos[momtag]
                                    del self.directionx_of_tumor[momtag]
                                    del self.tries[momtag]
                # moms
                todel = set()
                for (pos,momtag) in self.moms:
                    if momtag not in self.activecreep:
                        todel.add((pos,momtag))
                self.moms -= todel
                # creeptumorqueen and creeptumor change after 10 seconds to creeptumorburrowed
                # The tag remains the same.
                # the creeptumorburrowed needs 11 waittime. Start that ending the former phase.
                for stru in self.structures(UnitTypeId.CREEPTUMORQUEEN):
                    self.listenframe_of_structure[stru.tag] = self.frame + 11 * self.seconds
                for stru in self.structures(UnitTypeId.CREEPTUMOR):
                    self.listenframe_of_structure[stru.tag] = self.frame + 11 * self.seconds
                # A creeptumorburrowed can build a creeptumor once.
                for tag in self.activecreep:
                    if self.frame >= self.listenframe_of_structure[tag]:
                        strupos = self.activecreeppos[tag]
                        directionx = self.directionx_of_tumor[tag]
                        dirpoint = self.creepdirection[directionx]
                        rawpos = strupos.towards(dirpoint,10)
                        center = Point2((round(rawpos.x - 0.5) + 0.5,round(rawpos.y - 0.5) + 0.5))
                        altpoint = center
                        ok = self.creepable_ask_lord(altpoint)
                        if (not ok):
                            rawpos = strupos.towards(dirpoint,8)
                            center = Point2((round(rawpos.x - 0.5) + 0.5,round(rawpos.y - 0.5) + 0.5))
                            altpoint = Point2((center.x + self.dx, center.y + self.dy))
                            ok = self.creepable(altpoint)
                        if ok:
                            for stru in self.structures(UnitTypeId.CREEPTUMORBURROWED):
                                if stru.tag == tag:
                                    it = UnitTypeId.CREEPTUMOR
                                    pos = altpoint
                                    stru(AbilityId.BUILD_CREEPTUMOR_TUMOR,pos)
                                    self.listenframe_of_structure[tag] = self.frame + 5 * self.seconds
                                    self.map_plan(pos, 1)
                                    self.moms.add((pos,tag))
                                    self.tries[tag] += 1
                                    if self.tries[tag] > 10:
                                        self.random_direction(strupos,tag)
                                        self.tries[tag] = 0

    async def creepdrop(self):
        # overlords etc drop creep if standing still
        if self.function_listens('creepdrop',10):
            if len(self.structures(UnitTypeId.LAIR)) > 0:
                for typ in {UnitTypeId.OVERLORD, UnitTypeId.OVERLORDTRANSPORT, UnitTypeId.OVERSEERSIEGEMODE, UnitTypeId.OVERSEER}:
                    for lord in self.units(typ).idle: # stopped
                        tag = lord.tag
                        if self.frame >= self.listenframe_of_unit[tag]:
                            if tag in self.creepdropping:
                                if self.creepdropping[tag] != typ.name:
                                    del self.creepdropping[tag]
                            if tag not in self.creepdropping:
                                # debug, slow query:
                                #abilities = (await self.get_available_abilities([lord]))[0]
                                #if AbilityId.BEHAVIOR_GENERATECREEPOFF in abilities:
                                #    logger.info('creepdrop superfluous')
                                #if AbilityId.BEHAVIOR_GENERATECREEPON in abilities:
                                #    logger.info('creepdrop correct')
                                lord(AbilityId.BEHAVIOR_GENERATECREEPON)
                                self.listenframe_of_unit[tag] = self.frame + 5
                                self.creepdropping[tag] = typ.name

    async def do_creeplord(self):
        if len(self.structures(UnitTypeId.LAIR)) > 0:
            # creeplords alive and job
            todel = set()
            for tag in self.creeplords:
                seen = False
                for typ in {UnitTypeId.OVERLORD}:
                    for lord in self.units(typ):
                        if tag == lord.tag:
                            if self.job_of_unit(lord) == Job.CREEPLORD:
                                seen = True
                if not seen:
                    todel.add(tag)
            self.creeplords -= todel
            # get new ones
            if len(self.creeplords) < 3:
                bestdist = 99999
                best_unit: Optional[Unit] = None
                for typ in {UnitTypeId.OVERLORD}:
                    for lord in self.units(typ).idle:
                        tag = lord.tag
                        if tag not in self.creeplords:
                            if self.job_of_unit(lord) in {Job.UNCLEAR, Job.HANGER, Job.ROAMER}:
                                dist = distance(lord.position, self.ourmain)
                                if dist < bestdist:
                                    bestdist = dist
                                    best_unit = lord
                if best_unit:
                    tag = best_unit.tag
                    self.set_job_of_unit(best_unit, Job.CREEPLORD)
                    self.creeplords.add(tag)
                    self.creeplord_state[tag] = 'free'
            # moving is done by self.ask_lord(point)
            # reevaluate moving
            if self.function_listens('reevaluate_creeplord',20):
                for tag in self.creeplords:
                    if self.creeplord_state[tag] == 'moving':
                        itspoint = self.creeplord_goal[tag]
                        if self.has_creep(itspoint):
                            self.creeplord_state[tag] = 'free'
            # on point
            for typ in {UnitTypeId.OVERLORD}:
                for lord in self.units(typ).idle: # stopped or reached
                    tag = lord.tag
                    lordpos = lord.position
                    if tag in self.creeplords:
                        if self.creeplord_state[tag] == 'moving':
                            itspoint = self.creeplord_goal[tag]
                            dist = distance(lordpos, itspoint)
                            if dist < 1:
                                if self.has_creep(itspoint):
                                    self.creeplord_state[tag] = 'free'
                                else: # no creep yet
                                    self.creeplord_state[tag] = 'dropping'
                                    # GENERATECREEPON is done in another function 
                                    self.creeplord_free[tag] = self.frame + 7 * self.seconds
                            else: # stopped; retry
                                lord(AbilityId.MOVE, itspoint)
            # dropping
            for typ in {UnitTypeId.OVERLORD}:
                for lord in self.units(typ):
                    tag = lord.tag
                    if tag in self.creeplords:
                        if self.creeplord_state[tag] == 'dropping':
                            if self.frame >= self.creeplord_free[tag]:
                                self.creeplord_state[tag] = 'free'
                                # it can continue to creep until it is reused

    def ask_lord(self, point: Point2):
        if len(self.structures(UnitTypeId.LAIR)) > 0:
            # point not near an active goal
            goodpoint = True
            for tag in self.creeplords:
                if self.creeplord_state[tag] in {'moving', 'dropping'}:
                    goal = self.creeplord_goal[tag]
                    if distance(goal, point) < 10:
                        goodpoint = False
            if goodpoint:
                # send one close to point
                bestdist = 99999
                for typ in {UnitTypeId.OVERLORD}:
                    for lord in self.units(typ):
                        tag = lord.tag
                        if tag in self.creeplords:
                            if self.creeplord_state[tag] == 'free':
                                lordpos = lord.position
                                dist = distance(lordpos, point)
                                if dist < bestdist:
                                    bestdist = dist
                                    bestlord = lord
                if bestdist < 99999:
                    lord = bestlord
                    tag = lord.tag
                    self.creeplord_state[tag] = 'moving'
                    self.creeplord_goal[tag] = point
                    lord(AbilityId.MOVE, point)


