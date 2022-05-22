# creep.py, Merkbot, Zerg sandbox bot
# 20 may 2022
from common import Common
from map_if import Map_if
import sc2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.buff_id import BuffId
from sc2.position import Point2
from sc2.data import Race, Difficulty
from enum import Enum
from math import sqrt,cos,sin,pi,acos
import random

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
    #

    def __step0(self):
        self.init_creepstyle()
        #
        if self.enemy_race != Race.Zerg:
            # do not creep on expansionlocations
            for pos in self.expansion_locations_list:
                self.map_nocreep(pos, 5)
        #

    async def on_step(self):
        await Map_if.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.creep_spread()
        await self.re_direction()
        await self.queencreep()

    def init_creepstyle(self):
        self.creepdirection = []
        self.directionfinish = []
        if self.creepstyle == 0: # aggressive
            for epo in self.expansion_locations_list:
                 if self.distance(epo,self.enemymain) < 70:
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
            for directionx in range(0,len(self.creepdirection)):
                goal = self.creepdirection[directionx]
                finish = self.directionfinish[directionx]
                reached = False
                for typ in self.all_tumortypes:
                    for stru in self.structures(typ):
                        pos = stru.position
                        if self.distance(pos,goal) < finish:
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
            if (self.creepstyle == 0) and (self.frame > 8 * self.minutes):
                self.creepstyle += 1
                #print('creepstyle ' + str(self.creepstyle))
                self.init_creepstyle()
            if (self.creepstyle == 1) and (self.frame > 16 * self.minutes):
                self.creepstyle += 1
                #print('creepstyle ' + str(self.creepstyle))
                self.init_creepstyle()

    def creepable(self, point) -> bool:
        # for a point on the halfgrid, with halves.
        ok = self.has_creep(point) and self.map_can_plan_creep(point,1)
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
        while (self.distance(pos,dirpoint) < dirfin) and (self.different_directions > 1):
            self.directionx_of_tumor[tag] = self.next_directionx
            self.next_directionx = (self.next_directionx + 1) % len(self.creepdirection)
            directionx = self.directionx_of_tumor[tag]
            dirpoint = self.creepdirection[directionx]
                   
    async def queencreep(self):
        # get some creep queens
        for unt in self.units(UnitTypeId.QUEEN).idle:
            if self.job_of_unit[unt.tag] == self.Job.UNCLEAR:
                if unt.energy >= 27: # inject pickup is at 23
                    if self.frame >= self.listenframe_of_unit[unt.tag]:
                        self.job_of_unit[unt.tag] = self.Job.CREEPING
        # move to its spot
        for unt in self.units(UnitTypeId.QUEEN).idle:
            if self.job_of_unit[unt.tag] == self.Job.CREEPING:
                if self.frame >= self.listenframe_of_unit[unt.tag]:
                    itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(unt.position)
                    itsspot = itshatch.position.towards(self.map_center,9)
                    dist = self.distance(unt.position,itsspot)
                    if dist > 4:
                        unt.move(itsspot)
                        self.listenframe_of_unit[unt.tag] = self.frame + 5
        # make creeptumor
        for unt in self.units(UnitTypeId.QUEEN).idle:
            if self.job_of_unit[unt.tag] == self.Job.CREEPING:
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
                        self.job_of_unit[unt.tag] = self.Job.UNCLEAR
                        self.listenframe_of_unit[unt.tag] = self.frame + 100
        
    async def creep_spread(self):
        if self.frame % 3 == 2:
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
                    ok = self.creepable(altpoint)
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

