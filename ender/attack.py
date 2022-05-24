# attack.py, Merkbot, Zerg bot
# 24 may 2022

import random

from sc2.constants import TARGET_AIR, TARGET_GROUND
from sc2.ids.ability_id import AbilityId
from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from ender.common import Common


class Attack(Common):

    speed = {} # in griddist/sec
    minam = {} # minimum to keep when bigattacking.
    __did_step0 = False
    protected = set() # of tags. Some units left behind during a bigattack
    protected_am = {} # amount per type. Some units left behind during a bigattack
    attackgoal = {} # for units pointattacking, where it is going
    defendgoal = None
    renew_defendgoal = 0
    spray = {}
    casts = set() # of (spellkind, pos, expiration)
    berserkers = set()
    kite_back = set() # of unittype
    master = {} # per slavetag a mastertag
    biles = set()
    trips = set() # of (lurker.tag, overlordtransport.tag)    Both unique
    trip_goal = {} # per trip: a goal
    trip_phase = {} # per trip: none -> destined -> phoned -> flying -> falling
    bigattack_moment = -99999
    bigattack_end = 10 # the end of a bigattack, also allowing a new bigattack
    bigattackgoal = None
    last_catch = {} # for burrowed banelings
    burbanes = set() # of positions where a burrowed baneling is or was.
    pos_of_blocker = {}
    blocker_of_pos = {}
    may_spawn = {} # timer for swarmhosts
    sh_forward = {} # direction for swarmhosts
    sh_goal = None # direction for swarmhosts
    dried = set() # expo with neither minerals nor gas
    fresh = set() # expo with minerals or gas
    #

    def __step0(self):
        #
        # speed values copied from Liquipedia, dist per second
        self.speed[UnitTypeId.LARVA] = 0.79
        self.speed[UnitTypeId.OVERLORD] = 0.902
        self.speed[UnitTypeId.OVERLORDTRANSPORT] = 0.902
        self.speed[UnitTypeId.QUEEN] = 1.31
        self.speed[UnitTypeId.SPINECRAWLER] = 1.4
        self.speed[UnitTypeId.SPORECRAWLER] = 1.4
        self.speed[UnitTypeId.BROODLORD] = 1.97
        self.speed[UnitTypeId.LOCUSTMP] = 2.62
        self.speed[UnitTypeId.LOCUSTMPFLYING] = 2.62
        self.speed[UnitTypeId.OVERSEER] = 2.62
        self.speed[UnitTypeId.ROACH] = 3.15
        self.speed[UnitTypeId.HYDRALISK] = 3.15
        self.speed[UnitTypeId.INFESTOR] = 3.15
        self.speed[UnitTypeId.SWARMHOSTMP] = 3.15
        for typ in self.all_changelings:
            self.speed[typ] = 3.15
        self.speed[UnitTypeId.CHANGELINGZERGLING] = 4.13
        self.speed[UnitTypeId.CHANGELINGZERGLINGWINGS] = 4.13
        self.speed[UnitTypeId.BANELING] = 3.5
        self.speed[UnitTypeId.RAVAGER] = 3.85
        self.speed[UnitTypeId.DRONE] = 3.94
        self.speed[UnitTypeId.ZERGLING] = 4.13
        self.speed[UnitTypeId.LURKERMP] = 4.13
        self.speed[UnitTypeId.ULTRALISK] = 4.13
        self.speed[UnitTypeId.VIPER] = 4.13
        self.speed[UnitTypeId.CORRUPTOR] = 4.725
        self.speed[UnitTypeId.BROODLING] = 5.37
        self.speed[UnitTypeId.MUTALISK] = 5.6
        #
        # chosen to not attack:
        self.minam[UnitTypeId.DRONE] = 40
        self.minam[UnitTypeId.QUEEN] = 7
        self.minam[UnitTypeId.OVERLORD] = 20
        self.minam[UnitTypeId.MUTALISK] = 1
        self.minam[UnitTypeId.OVERSEER] = 1
        self.minam[UnitTypeId.CORRUPTOR] = 1
        self.minam[UnitTypeId.HYDRALISK] = 1
        #
        self.defendgoal = self.ourmain.towards(self.map_center,8)
        self.kite_back = {UnitTypeId.BROODLORD, UnitTypeId.INFESTOR}

    async def on_step(self):
        await Common.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.big_attack()
        await self.attack_unclutter() # can be commented to speed up
        await self.defend()
        await self.berserk()
        await self.corrupt()
        await self.infest()
        await self.vipers()
        await self.set_sh_goal()
        await self.swarmhosts()
        await self.blocker()
        await self.slaves()
        await self.wounded()
        await self.transport()
        await self.guards()
        await self.banes()
        await self.do_dried()

    def find_bigattackgoal(self):
        if self.function_listens('find_bigattackgoal',40):
            goals = [] # of (dumbness,dist_to_enemymain,pos)
            goals.append((2,0,self.enemymain))
            for (typ,pos) in self.enemy_struc_mem:
                dist = self.distance(pos,self.enemymain)
                goals.append((1,dist,pos))
            for (typ,pos) in self.enemy_struc_mem:
                if typ in self.all_halltypes:
                    dist = self.distance(pos,self.ourmain)
                    goals.append((0,dist,pos))
            goals.sort()
            (dumbness,dist_to_enemymain,pos) = goals[0]
            self.bigattackgoal = pos

    def do_protect(self, unt, typ):
        if unt.tag not in self.protected:
            if typ in self.protected_am:
                if self.protected_am[typ] < self.minam[typ]:
                    self.protected.add(unt.tag)
                    self.protected_am[typ] += 1
            else:
                self.protected.add(unt.tag)
                self.protected_am[typ] = 1

    async def defend(self):
        # sometimes renew defendgoal
        if self.frame >= self.renew_defendgoal:
            self.renew_defendgoal = self.frame + self.minutes
            bestval = -99999
            for hall in self.townhalls:
                pos = hall.position
                val = abs(hall.tag) % 54321
                #print(str(val))
                if val > bestval:
                    bestval = val
                    bestpos = pos
            if bestval > -99999:
                self.defendgoal = bestpos.towards(self.map_center,8)                  
        # 
        if self.function_listens('defend',20):
            if self.frame >= self.bigattack_end:
                for typ in self.all_armytypes:
                    if typ not in {UnitTypeId.QUEEN, UnitTypeId.LURKERMPBURROWED}:
                        for unt in self.units(typ).idle:
                            tag = unt.tag
                            if self.frame >= self.listenframe_of_unit[tag]:
                                if self.job_of_unit[tag] == self.Job.DEFENDATTACK:
                                    if self.distance(unt.position, self.defendgoal) > 8:
                                        unt.attack(self.defendgoal)
                                        self.attackgoal[tag] = self.defendgoal
                                        self.listenframe_of_unit[tag] = self.frame + 5
                                elif self.job_of_unit[tag] == self.Job.UNCLEAR:
                                    self.job_of_unit[tag] = self.Job.DEFENDATTACK
                                    unt.attack(self.defendgoal)
                                    self.attackgoal[tag] = self.defendgoal
                                    self.listenframe_of_unit[tag] = self.frame + 5
                        
    async def big_attack(self):
        # goal
        self.find_bigattackgoal()
        # attack now?
        if self.frame > self.bigattack_end:
            now = True
            for typ in self.make_plan:
                if typ in self.all_armytypes:
                    if 4 * len(self.units(typ)) < 3 * self.make_plan[typ]:
                        now = False
            if (self.armysupply_used >= 90) or (self.supply_used >= 190):
                eggtypes = {UnitTypeId.EGG, UnitTypeId.BROODLORDCOCOON, UnitTypeId.RAVAGERCOCOON, UnitTypeId.BANELINGCOCOON}
                eggs = 0
                for typ in eggtypes:
                    eggs += len(self.units(typ))
                if eggs < 4:
                    now = True
            if now:
                # report
                self.bigattack_count += 1
                # protect some units
                self.protected = set()
                self.protected_am = {}
                # protect some queens at different bases
                typ = UnitTypeId.QUEEN
                if len(self.units(typ)) > 0:
                    for hall in self.townhalls:
                        unt = self.units(typ).closest_to(hall.position)
                        if self.distance(hall.position,unt.position) < 16:
                            self.do_protect(unt,typ)
                # protect some units
                for typ in self.minam:
                    for unt in self.units(typ):
                        self.do_protect(unt,typ)         
                # get approachdura
                approachdura = 0
                for typ in self.all_armytypes:
                    if typ not in {UnitTypeId.OVERLORDTRANSPORT, UnitTypeId.LURKERMP, UnitTypeId.HYDRALISK,
                           UnitTypeId.OVERSEERSIEGEMODE}:
                        for unt in self.units(typ):
                            tag = unt.tag
                            if tag not in self.protected:
                                if self.job_of_unit[tag] not in (self.Job.BIGATTACK, self.Job.BLOCKER, 
                                        self.Job.WOUNDED, self.Job.SCRATCHED, self.Job.BERSERKER, self.Job.TIRED, 
                                        self.Job.SLAVE, self.Job.NURSE):
                                    distance = self.distance(unt.position,self.bigattackgoal)
                                    speed = self.speed[typ] / self.seconds
                                    duration = distance / speed
                                    approachdura = max(duration, approachdura)
                # fix attackmoment
                self.bigattack_moment = self.frame + approachdura
                self.bigattack_end = self.bigattack_moment + 30 * self.seconds
                # next time, keep more drones
                self.minam[UnitTypeId.DRONE] = 80
        # get some bigattack units
        for typ in self.all_armytypes:
            if typ not in {UnitTypeId.OVERLORDTRANSPORT, UnitTypeId.LURKERMP, UnitTypeId.OVERSEERSIEGEMODE}:
                if typ not in self.all_burrowtypes:
                    for unt in self.units(typ):
                        tag = unt.tag
                        if tag not in self.protected:
                            if self.frame >= self.listenframe_of_unit[tag]:
                                if self.job_of_unit[tag] not in (self.Job.BIGATTACK, self.Job.BLOCKER, 
                                        self.Job.WOUNDED, self.Job.SCRATCHED, self.Job.BERSERKER, self.Job.TIRED, 
                                        self.Job.SLAVE, self.Job.NURSE):
                                    distance = self.distance(unt.position,self.bigattackgoal)
                                    speed = self.speed[typ] / self.seconds
                                    duration = distance / speed
                                    attackmoment = self.frame + duration
                                    if attackmoment >= self.bigattack_moment:
                                        if attackmoment < self.bigattack_end:
                                            #print('debug ' + unt.name + ' starts walking ' + str(duration))
                                            self.job_of_unit[tag] = self.Job.BIGATTACK
                                            self.attackgoal[tag] = self.bigattackgoal
                                            unt.attack(self.bigattackgoal)
                                            self.listenframe_of_unit[tag] = self.frame + 5
        # whip them
        for typ in self.all_armytypes:
            for unt in self.units(typ).idle:
                tag = unt.tag
                if self.job_of_unit[tag] == self.Job.BIGATTACK:
                    if self.frame >= self.listenframe_of_unit[tag]:
                        if self.frame >= self.bigattack_end:
                            self.job_of_unit[tag] = self.Job.UNCLEAR
                        else:
                            # why does it idle?
                            goal = self.attackgoal[tag]
                            dist = self.distance(unt.position,goal)
                            if dist < 5:
                                # it reached its goal
                                unt.attack(self.bigattackgoal)
                                self.listenframe_of_unit[tag] = self.frame + 5
                                self.attackgoal[tag] = self.bigattackgoal
                            else:
                                # it was distracted
                                unt.attack(self.bigattackgoal)
                                self.listenframe_of_unit[tag] = self.frame + 5

    async def berserk(self):
        # berserkers are units that will fight to die to free supply
        # get some berserkers
        if self.function_listens('berserk',20):
            if self.armysupply_used >= 90:
                self.berserkers = self.berserkers and self.living
                if len(self.berserkers) < 6:
                    tomake = 1
                    for typ in {UnitTypeId.ZERGLING, UnitTypeId.ROACH}:
                        for unt in self.units(typ).idle:
                            tag = unt.tag
                            if self.job_of_unit[tag] != self.Job.BERSERKER:
                                if tomake > 0:
                                    tomake -= 1
                                    self.job_of_unit[tag] = self.Job.BERSERKER
                                    self.berserkers.add(tag)
                                    self.find_bigattackgoal()
                                    self.attackgoal[tag] = self.bigattackgoal
                                    unt.attack(self.bigattackgoal)
                                    self.listenframe_of_unit[tag] = self.frame + 5
            # whip them
            for typ in self.all_armytypes:
                for unt in self.units(typ).idle:
                    tag = unt.tag
                    if self.job_of_unit[tag] == self.Job.BERSERKER:
                        if self.frame >= self.listenframe_of_unit[tag]:
                            # why does it idle?
                            goal = self.attackgoal[tag]
                            dist = self.distance(unt.position,goal)
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

        

    def indanger(self, unt) -> bool:
        # do you see an enemy that can hit air, dist < 10?
        danger = False
        somehitair = False
        somehitground = False
        for ene in self.enemy_units:
            if self.distance(ene.position,unt.position) < 10:
                for weapon in ene._weapons:
                    if weapon.type in TARGET_AIR:
                       somehitair = True
                    if weapon.type in TARGET_GROUND:
                       somehitground = True
        for typ in {UnitTypeId.MISSILETURRET, UnitTypeId.PHOTONCANNON, UnitTypeId.SPORECRAWLER,
                    UnitTypeId.SPINECRAWLER, UnitTypeId.PLANETARYFORTRESS, UnitTypeId.BUNKER}:
            for ene in self.enemy_structures(typ): # current visible
                if self.distance(ene.position,unt.position) < 10:
                    for weapon in ene._weapons:
                        if weapon.type in TARGET_AIR:
                           somehitair = True
                        if weapon.type in TARGET_GROUND:
                           somehitground = True
        if unt.is_flying:
            danger = somehitair
        else:
            danger = somehitground
        return danger

    async def attack_unclutter(self):
        for unt in self.units:
            tag = unt.tag
            typ = unt.type_id
            if self.job_of_unit[tag] in {self.Job.DEFENDATTACK, self.Job.BIGATTACK, self.Job.BERSERKER}:
                if typ not in {UnitTypeId.OVERLORD, UnitTypeId.OVERSEER, UnitTypeId.OVERLORDTRANSPORT}:
                    if self.frame >= self.listenframe_of_unit[tag]:
                        if unt.weapon_cooldown > self.game_step:
                            goal = self.attackgoal[tag]
                            goaldist = self.distance(unt.position,goal)
                            if goaldist >= 5:
                                # unt may frustrate others to advance, so move it forward.
                                cooldist = unt.weapon_cooldown * unt.real_speed / self.seconds
                                point = unt.position.towards(goal,cooldist / 2) # halved for melee units
                                if typ in self.kite_back:
                                    if self.indanger(unt):
                                        point = unt.position.towards(self.defendgoal,cooldist / 2)
                                unt.move(point)
                                unt.attack(goal,queue=True)
                                self.listenframe_of_unit[tag] = self.frame + unt.weapon_cooldown + 5             


    async def corrupt(self):
        if self.function_listens('corrupt',10):
            sprayers = self.jobcount(self.Job.SPRAYER)
            for unt in self.units(UnitTypeId.CORRUPTOR):
                tag = unt.tag
                if sprayers < 5:
                    if tag in self.attackgoal:
                        goal = self.attackgoal[tag]
                        if self.distance(unt.position,goal) < 6:
                            abi = AbilityId.CAUSTICSPRAY_CAUSTICSPRAY
                            canspray = True
                            if tag in self.spray:
                                canspray = (self.frame >= self.spray[tag])
                            if canspray:
                                canspray = False
                                for ene in self.enemy_structures: # currently visible
                                    if ene.position == goal:
                                        # dismiss edge case 1 corruptor is left over
                                        if ene.health >= 200:
                                            canspray = True
                                            target = ene
                            if canspray:
                                sprayers += 1
                                unt(abi,target)
                                self.spray[tag] = self.frame + 32.14 * self.seconds
                                self.job_of_unit[tag] = self.Job.SPRAYER
                                self.listenframe_of_unit[tag] = self.frame + 5
            # end sprayer
            for unt in self.units(UnitTypeId.CORRUPTOR).idle:
                if self.job_of_unit[tag] == self.Job.SPRAYER:
                    if self.frame >= self.listenframe_of_unit[tag]:
                        self.job_of_unit[tag] = self.Job.UNCLEAR

    async def infest(self):
        if self.function_listens('infest',10):
            for unt in self.units(UnitTypeId.INFESTOR):
                tag = unt.tag
                pos = unt.position
                fungal = AbilityId.FUNGALGROWTH_FUNGALGROWTH
                # fungal
                if unt.energy >= 75:
                    throw =  self.cast_at_point('fungal', pos, 10, 2.25, 3)
                    if throw != self.nowhere:
                        unt(fungal,throw)
                # back
                if unt.energy < 75 / 2:
                    if self.job_of_unit[tag] != self.Job.TIRED:
                        unt.move(self.ourmain)
                        self.job_of_unit[tag] = self.Job.TIRED
                elif self.job_of_unit[tag] == self.Job.TIRED:
                    self.job_of_unit[tag] = self.Job.UNCLEAR

    async def vipers(self):
        if self.function_listens('vipers',5):
            for vip in self.units(UnitTypeId.VIPER):
                blind = AbilityId.BLINDINGCLOUD_BLINDINGCLOUD # range 11 rad 2 eng 100
                draw = AbilityId.EFFECT_ABDUCT # range 9 eng 75
                attackair = AbilityId.PARASITICBOMB_PARASITICBOMB # range 8 rad 3 eng 125
                load = AbilityId.VIPERCONSUMESTRUCTURE_VIPERCONSUME # 200 damage
                tag = vip.tag
                pos = vip.position
                # blind
                if vip.energy >= 100:
                    throw =  self.cast_at_point('blind', pos, 11, 2, 5.71)
                    if throw != self.nowhere:
                        vip(blind,throw)
                # attackair
                if vip.energy >= 125:
                    throw =  self.cast_at_unit('attackair', pos, 8, 3, 7)
                    if throw is not None:
                        vip(attackair,throw)
                # back
                if vip.energy < 100 / 2:
                    if self.job_of_unit[tag] != self.Job.TIRED:
                        vip.move(self.ourmain)
                        self.job_of_unit[tag] = self.Job.TIRED
                elif self.job_of_unit[tag] == self.Job.TIRED:
                    self.job_of_unit[tag] = self.Job.UNCLEAR
    
    
    async def set_sh_goal(self):
        if self.function_listens('set_sh_goal', 9 * self.seconds):
            self.sh_goal = self.enemymain
            mindist = 99999
            for (typ, pos) in self.enemy_struc_mem:
                if typ in self.all_halltypes:
                    dist = self.distance(self.ourmain,pos)
                    if dist < mindist:
                        mindist = dist
                        target = pos
            if mindist < 99999:
                self.sh_goal = target

    async def swarmhosts(self):
        if self.function_listens('swarmhosts',9):
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
                            sh.move(self.ourmain)
                    else:
                        if not self.sh_forward[tag]:
                            goal = self.sh_goal.towards(self.ourmain,15)
                            self.sh_forward[tag] = True
                            sh.move(goal)
            for sh in self.units(UnitTypeId.SWARMHOSTMP) | self.units(UnitTypeId.SWARMHOSTBURROWEDMP):
                self.job_of_unit[tag] = self.Job.WALKER
                spawn = AbilityId.EFFECT_SPAWNLOCUSTS
                tag = sh.tag
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
                    

    def cast_at_point(self, kind, pos, rrange, radius, duration) -> Point2:
        result = self.nowhere
        targets = set()
        throws = set()
        for ene in self.enemy_units:
            dist = self.distance(ene.position,pos)
            if dist < rrange + radius:
                validtarget = True # e.g.infest
                if ene.type_id in {UnitTypeId.BROODLING, UnitTypeId.AUTOTURRET, UnitTypeId.LARVA, UnitTypeId.EGG}:
                    validtarget = False
                if kind == 'blind':
                    validtarget = False
                    for weapon in ene._weapons:
                        if weapon.type in TARGET_AIR: # added because usually my army flies
                            if weapon.range >= 1:
                                validtarget = True
                    if ene.is_flying:
                        validtarget = False
                if validtarget:
                    if dist < rrange:
                        throws.add(ene.position)
                        targets.add(ene.position)
                    elif dist < rrange + radius:
                        throws.add(pos.towards(ene.position,rrange))
                        targets.add(ene.position)
        if len(targets) >= 3:
            # delete targets in casts
            todel = set()
            for (akind, throw, expiration) in self.casts:
                if akind == kind:
                    if self.frame < expiration:
                        for target in targets:
                            if self.distance(target,throw) < radius:
                                todel.add(target)
            targets -= todel
            # 
            if len(targets) >= 3:
                hit = dict((throw,0) for throw in throws)
                for throw in throws:
                    for target in targets:
                        if self.distance(throw,target) < radius:
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
    
    def cast_at_unit(self, kind, pos, rrange, radius, duration):
        result = None
        targets = set()
        for ene in self.enemy_units:
            dist = self.distance(ene.position,pos)
            if dist < rrange:
                validtarget = True
                if ene.type_id in {UnitTypeId.BROODLING, UnitTypeId.AUTOTURRET, UnitTypeId.LARVA, UnitTypeId.EGG}:
                    validtarget = False
                if kind == 'attackair':
                    validtarget = ene.is_flying
                if validtarget:
                    targets.add(ene)
        if len(targets) >= 3:
            # delete targets in casts
            todel = set()
            for (akind, throw, expiration) in self.casts:
                if akind == kind:
                    if self.frame < expiration:
                        for target in targets:
                            if self.distance(target.position,throw) < radius:
                                todel.add(target)
            targets -= todel
            # 
            if len(targets) >= 3:
                hit = dict((target,0) for target in targets)
                for throwtarget in targets:
                    for target in targets:
                        if self.distance(throwtarget.position,target.position) < radius:
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
    
    async def blocker(self):
        if self.function_listens('blocker',31):
            # zergling is gone
            todel = set()
            for tag in self.pos_of_blocker:
                pos = self.pos_of_blocker[tag]
                if tag in self.living:
                    job = self.job_of_unit[tag]
                    if job != self.Job.BLOCKER:
                        todel.add((tag,pos))
                else:
                    todel.add((tag,pos))
            for (tag,pos) in todel:
                del self.pos_of_blocker[tag]
                del self.blocker_of_pos[pos]
            # recruit
            if self.nbases >= 3:
                for unt in self.units(UnitTypeId.ZERGLING):
                    tag = unt.tag
                    job = self.job_of_unit[tag]
                    if job != self.Job.BLOCKER:
                        pos = self.nowhere
                        dist = 99999
                        for apos in self.expansion_locations_list:
                            adist = self.distance(apos,self.enemymain)
                            if apos not in self.blocker_of_pos:
                                if adist < dist:
                                    dist = adist
                                    pos = apos
                        if pos != self.nowhere:
                            # connect
                            self.pos_of_blocker[tag] = pos
                            self.blocker_of_pos[pos] = tag
                            self.job_of_unit[tag] = self.Job.BLOCKER
                            unt.move(pos)
            # block
            for unt in self.units(UnitTypeId.ZERGLING):
                tag = unt.tag
                if self.frame >= self.listenframe_of_unit[tag]:
                    job = self.job_of_unit[tag]
                    if job == self.Job.BLOCKER:
                        pos = self.pos_of_blocker[tag]
                        if self.distance(unt.position,pos) > 3:
                            if pos not in self.current_expandings:
                                unt.move(pos)
                                self.listenframe_of_unit[tag] = self.frame + 3 * self.seconds
            # burrow
            bur = AbilityId.BURROWDOWN_ZERGLING
            if UpgradeId.BURROW in self.state.upgrades:
                for unt in self.units(UnitTypeId.ZERGLING).idle:
                    tag = unt.tag
                    if self.job_of_unit[tag] == self.Job.BLOCKER:
                        pos = self.pos_of_blocker[tag]
                        if self.distance(unt.position,pos) < 3:
                            if pos not in self.current_expandings:
                                unt(bur)
            # unblock
            bup = AbilityId.BURROWUP_ZERGLING
            for pos in self.blocker_of_pos:
                tag = self.blocker_of_pos[pos]
                if pos in self.current_expandings:
                    for unt in self.units(UnitTypeId.ZERGLINGBURROWED):
                        if unt.tag == tag:
                            unt(bup)
                    

    async def slaves(self):
        if self.function_listens('slaves',61):
            candidates = {UnitTypeId.INFESTOR, UnitTypeId.CORRUPTOR, UnitTypeId.ROACH, UnitTypeId.OVERSEER,
                          UnitTypeId.MUTALISK, UnitTypeId.VIPER}
            # dead master
            todel = set()
            for slatag in self.master:
                if slatag in self.living:
                    if self.job_of_unit[slatag] == self.Job.SLAVE:
                        mastag = self.master[slatag]
                        if mastag not in self.living:
                            self.job_of_unit[slatag] = self.Job.UNCLEAR
                            todel.add(slatag)
            for slatag in todel:
                del self.master[slatag]
            # master wounded
            for sla in self.units:
                slatag = sla.tag
                if self.job_of_unit[slatag] == self.Job.SLAVE:
                    mastag = self.master[slatag]
                    if mastag in self.living:
                        if self.job_of_unit[mastag] in {self.Job.SCRATCHED, self.Job.WOUNDED}:
                            self.job_of_unit[slatag] = self.Job.UNCLEAR
                            del self.master[slatag]
            # slave changed typ
            todel = set()
            for sla in self.units:
                slatag = sla.tag
                if self.job_of_unit[slatag] == self.Job.SLAVE:
                    typ = sla.type_id
                    if typ not in candidates:
                        self.job_of_unit[slatag] = self.Job.UNCLEAR
                        todel.add(slatag)
            for slatag in todel:
                del self.master[slatag]
            # free all slaves
            if len(self.units(UnitTypeId.BROODLORD)) < 3:
                for typ in candidates:
                    for sla in self.units(typ):
                        if self.job_of_unit[sla.tag] == self.Job.SLAVE:
                            self.job_of_unit[sla.tag] = self.Job.UNCLEAR
                            del self.master[sla.tag]
            # make all slaves
            if len(self.units(UnitTypeId.BROODLORD)) >= 3:
                for typ in candidates:
                    for sla in self.units(typ):
                        if self.job_of_unit[sla.tag] not in {self.Job.SLAVE, self.Job.SCRATCHED, self.Job.TIRED, 
                                                             self.Job.WOUNDED, self.Job.BERSERKER}:
                            self.job_of_unit[sla.tag] = self.Job.SLAVE
                            self.master[sla.tag] = self.units(UnitTypeId.BROODLORD).random.tag
            # move slaves
            for typ in candidates:
                for sla in self.units(typ):
                    if self.job_of_unit[sla.tag] == self.Job.SLAVE:
                        bestdist = 99999
                        for mas in self.units(UnitTypeId.BROODLORD):
                            if mas.tag == self.master[sla.tag]:
                                dist = self.distance(mas.position,sla.position)
                                if dist < bestdist:
                                    bestdist = dist
                                    bestpos = mas.position
                        if 3 < bestdist < 99999:
                            sla.move(bestpos)

            
    async def wounded(self):
        ourcorner = self.ourmain.towards(self.map_center,-8)
        for typ in self.all_unittypes:
            if typ not in {UnitTypeId.BANELING, UnitTypeId.OVERLORDTRANSPORT}:
                for unt in self.units(typ):
                    if unt.tag in self.last_health:
                        if unt.health < 0.7 * self.last_health[unt.tag]:
                            if self.job_of_unit[unt.tag] not in {self.Job.BERSERKER, self.Job.NURSE, self.Job.WOUNDED,
                                                                self.Job.SCRATCHED, self.Job.TRANSPORTER}:
                                if unt.health < unt.health_max - 100:
                                    self.job_of_unit[unt.tag] = self.Job.WOUNDED
                                else:
                                    self.job_of_unit[unt.tag] = self.Job.SCRATCHED
                                away = unt.position.towards(self.hospital,7)
                                unt.move(away)
                                unt.attack(self.hospital, queue=True)
        if self.function_listens('wounded',63):
            for typ in self.all_unittypes:
                for unt in self.units(typ):
                    if self.job_of_unit[unt.tag] in {self.Job.WOUNDED, self.Job.SCRATCHED}:
                        if 2 * unt.health >= unt.health_max:        
                            self.job_of_unit[unt.tag] = self.Job.UNCLEAR

    async def dodge_biles(self):
        if self.function_listens('admin_biles',25):
            # delete old biles
            todel = set()
            for (pos,landframe) in self.biles:
                if self.frame > landframe:
                    todel.add((pos,landframe))
            self.biles -= todel
        if self.function_listens('dodge_biles',5):
            # new biles
            for effect in self.state.effects:
                if effect.id == EffectId.RAVAGERCORROSIVEBILECP:
                    for bileposition in effect.positions:
                        if bileposition not in self.biles:
                            self.biles.add((bileposition,self.frame + 60))
            # dodge biles
            if len(self.biles) > 0:
                for typ in self.all_army:
                    for unt in self.units(typ):
                        mustflee = False
                        for (bileposition,landframe) in self.biles:
                            if self.near(bileposition,unt.position,3):
                                if self.frame < landframe:
                                    mustflee = True
                                    abile = bileposition
                        if mustflee:
                            if abile == unt.position:
                                topoint = abile.towards(self.ourmain,3)
                            else:
                                topoint = abile.towards(unt.position,3)
                            unt(AbilityId.MOVE_MOVE,topoint)

    def in_trips_lurker(self, tag) -> bool:
        for (lurtag,tratag) in self.trips:
            if tag == lurtag:
                return True
        return False
    
    def in_trips_tra(self, tag) -> bool:
        for (lurtag,tratag) in self.trips:
            if tag == tratag:
                return True
        return False
    
    async def transport(self):
        if self.function_listens('transport',11):
            # make trips
            for unt in self.units(UnitTypeId.LURKERMP):
                if self.frame >= self.listenframe_of_unit[unt.tag]:
                    for tra in self.units(UnitTypeId.OVERLORDTRANSPORT):
                        if self.frame >= self.listenframe_of_unit[tra.tag]:
                            if not self.in_trips_tra(tra.tag):
                                if tra.health >= 50:
                                    if not self.in_trips_lurker(unt.tag):
                                        trip = (unt.tag,tra.tag)
                                        self.trips.add(trip)
                                        goals = [self.enemymain]
                                        for (typ,pos) in self.enemy_struc_mem:
                                            if typ in self.all_halltypes:
                                                goals.append(pos)
                                        goal = random.choice(goals)
                                        self.trip_goal[trip] = goal
                                        self.trip_phase[trip] = 'destined'
            # per trip (both visible)
            for trip in self.trips:
                goal = self.trip_goal[trip]
                (lurtag,tratag) = trip
                for unt in self.units(UnitTypeId.LURKERMP):
                    if unt.tag == lurtag:
                        if self.frame >= self.listenframe_of_unit[unt.tag]:
                            for tra in self.units(UnitTypeId.OVERLORDTRANSPORT):
                                if self.frame >= self.listenframe_of_unit[tra.tag]:
                                    if tra.tag == tratag:
                                        if self.trip_phase[trip] == 'destined':
                                            self.trip_phase[trip] = 'phoned'
                                            self.job_of_unit[unt.tag] = self.Job.TRANSPORTER
                                            self.job_of_unit[tra.tag] = self.Job.TRANSPORTER
                                            meetingpoint = Point2((0.5 * tra.position.x + 0.5 * unt.position.x,
                                                                   0.5 * tra.position.y + 0.5 * unt.position.y))
                                            tra.move(meetingpoint)
                                            self.listenframe_of_unit[tra.tag] = self.frame + self.seconds
                                            unt.move(meetingpoint)
                                            self.listenframe_of_unit[unt.tag] = self.frame + self.seconds
                                        # remeet on idle
                                        elif self.trip_phase[trip] == 'phoned':
                                            if self.distance(unt.position,tra.position) < 2:
                                                self.trip_phase[trip] = 'flying'
                                                tra(AbilityId.LOAD_OVERLORD,unt)
                                                tra(AbilityId.MOVE_MOVE,goal,queue=True)
                                                self.listenframe_of_unit[tra.tag] = self.frame + 8 * self.seconds
                                                self.listenframe_of_unit[unt.tag] = self.frame + 4 * self.seconds
                                            elif len(tra.orders) == 0:
                                                if self.distance(unt.position,tra.position) >= 2:
                                                    tra.move(unt.position)
                                                    self.listenframe_of_unit[tra.tag] = self.frame + self.seconds
            # per trip (transport visible)
            for trip in self.trips:
                goal = self.trip_goal[trip]
                (lurtag,tratag) = trip
                for tra in self.units(UnitTypeId.OVERLORDTRANSPORT):
                    if self.frame >= self.listenframe_of_unit[tra.tag]:
                        if tra.tag == tratag:
                            if self.trip_phase[trip] == 'flying':
                                if self.distance(tra.position,goal) < 2:
                                    self.trip_phase[trip] = 'falling'
                                    tra(AbilityId.UNLOADALLAT_OVERLORD,goal)
                                    self.job_of_unit[tra.tag] = self.Job.UNCLEAR
                                    self.listenframe_of_unit[tra.tag] = self.frame + 3 * self.seconds
                                    self.listenframe_of_unit[lurtag] = self.frame + 3 * self.seconds
                                elif tra.health < 50:
                                    goal = tra.position
                                    self.trip_goal[trip] = goal
                                elif len(tra.orders) == 0:
                                    if self.distance(tra.position,goal) >= 2:
                                        tra.move(goal)
                                        self.listenframe_of_unit[tra.tag] = self.frame + self.seconds
            # per trip (lurker visible)
            todel = set()
            for trip in self.trips:
                goal = self.trip_goal[trip]
                (lurtag,tratag) = trip
                for unt in self.units(UnitTypeId.LURKERMP):
                    if unt.tag == lurtag:
                        if self.frame >= self.listenframe_of_unit[unt.tag]:
                            if self.trip_phase[trip] == 'falling':
                                if self.distance(unt.position,goal) < 6:
                                    unt(AbilityId.BURROWDOWN_LURKER)
                                    self.job_of_unit[unt.tag] = self.Job.UNCLEAR
                                    del self.trip_goal[trip]
                                    del self.trip_phase[trip]
                                    todel.add(trip)
                                    self.listenframe_of_unit[unt.tag] = self.frame + 4 * self.seconds
                                else:
                                    self.trip_phase[trip] = 'destined'
            self.trips -= todel

    async def guards(self):
        if self.frame < 5 * self.minutes:
            if self.function_listens('guards',10):
                # stray guards
                for unt in self.units(UnitTypeId.DRONE):
                    tag = unt.tag
                    pos = unt.position
                    if self.job_of_unit[tag] == self.Job.GUARD:
                        tohome = 99999
                        for hall in self.structures(UnitTypeId.HATCHERY):
                            dist = self.distance(pos,hall.position)
                            tohome = min(dist,tohome)
                        if tohome >= 20:
                            self.job_of_unit[tag] = self.Job.UNCLEAR
                            unt.move(self.ourmain)
                        elif tohome >= 10:
                            if len(unt.orders) == 0:
                                self.job_of_unit[tag] = self.Job.UNCLEAR
                # per hatchery
                for stru in self.structures(UnitTypeId.HATCHERY):
                    strupos = stru.position
                    if stru.build_progress >= 0.5:
                        attackers = 0
                        for ene in self.enemy_units:
                            if not ene.is_flying:
                                if self.distance(ene.position,strupos) < 10:
                                    anattacker = ene
                                    attackers += 1
                        defenders = set()
                        for unt in self.units(UnitTypeId.DRONE):
                            tag = unt.tag
                            if self.job_of_unit[tag] == self.Job.GUARD:
                                if self.distance(unt.position,strupos) < 10:
                                    defenders.add(tag)
                        # sleeping defenders
                        if attackers > 0:
                            for unt in self.units(UnitTypeId.DRONE).idle:
                                tag = unt.tag
                                if self.job_of_unit[tag] == self.Job.GUARD:
                                    unt.attack(anattacker)
                        # drone guards
                        if attackers > 0:
                            wishdefenders = attackers + 1
                        else:
                            wishdefenders = 0
                        if len(defenders) < wishdefenders:
                            for unt in self.units(UnitTypeId.DRONE):
                                tag = unt.tag
                                if self.job_of_unit[tag] in {self.Job.MIMMINER, self.Job.GASMINER, self.Job.UNCLEAR}:
                                    if self.distance(unt.position,strupos) < 10:
                                        if len(defenders) < wishdefenders:
                                            self.job_of_unit[tag] = self.Job.GUARD
                                            defenders.add(tag)
                                            unt.attack(anattacker)
                        if len(defenders) > wishdefenders:
                            for unt in self.units(UnitTypeId.DRONE):
                                tag = unt.tag
                                if tag in defenders:
                                    if len(defenders) > wishdefenders:
                                        defenders.remove(tag)
                                        self.job_of_unit[tag] = self.Job.UNCLEAR
                                        unt.move(strupos)

    async def banes(self):
        bur = AbilityId.BURROWDOWN_BANELING
        bang = AbilityId.EXPLODE_EXPLODE
        for unt in self.units(UnitTypeId.BANELING):
            pos = unt.position
            burrow = False
            for ene in self.enemy_units:
                if self.distance(ene.position,pos) < 10:
                    burrow = True
            if burrow:
                # max 2 within radius 5
                amclose = 0
                for burba in self.burbanes:
                    if self.distance(burba,pos) < 5:
                        amclose += 1
                if amclose >= 2:
                    burrow = False
                if burrow:
                    self.burbanes.add(pos)
                    unt(bur)
        for unt in self.units(UnitTypeId.BANELINGBURROWED):
            pos = unt.position
            # radius = 2.2
            catch = set()
            smallradius = 1.9
            escaping = set()
            bigradius = 2.2
            for ene in self.enemy_units:
                if not ene.is_flying:
                    dist = self.distance(ene.position,pos)
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
                # keep it in burbanes
            self.last_catch[unt.tag] = catch
            
    async def do_dried(self):
        if self.function_listens('do_dried', 21 * self.seconds):
            # dried bases
            self.dried = set()
            self.fresh = set()
            geysers_nonemp = self.vespene_geyser.filter(lambda gey: gey.has_vespene)
            geysers_nonemp_pos = [gey.position for gey in geysers_nonemp]
            mineral_pos = [patch.position for patch in self.mineral_field]
            for expo in self.expansion_locations_list:
                has_ore = False
                for ore_pos in geysers_nonemp_pos:
                    if self.distance(ore_pos, expo) < 10:
                        has_ore = True
                for ore_pos in mineral_pos:
                    if self.distance(ore_pos, expo) < 10:
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
                            if self.distance(pos,expo) < 10:
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
                        if self.distance(expo,stru.position) < 10:
                            if expo in self.dried:
                                mindist = 99999
                                for to_expo in self.fresh:
                                    dist = self.distance(to_expo,expo)
                                    if dist < mindist:
                                        mindist = dist
                                        goal = to_expo
                                point = goal.towards(expo,8)
                                stru.move(point)
                                self.listenframe_of_structure[tag] = self.frame + 5
                            else: 
                                # rooting is in making.py
                                self.to_root.add(tag)



        


            
                    

            
