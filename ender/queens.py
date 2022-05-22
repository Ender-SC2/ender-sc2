# queens.py, Merkbot, Zerg sandbox bot
# 20 may 2022
# moved queencreep(self) to creep.py

from ender.common import Common
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId


class Queens(Common):

    __did_step0 = False
    nextinject = {} # per hatch to prevent overinjecting
    treating = {} # per patient the next treating moment

    def __step0(self):
        pass

    async def on_step(self):
        await Common.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.queeninject()
        await self.transfuse()

    def choose_inject(self,pos) -> bool:
        # for a queen at pos
        want = False
        itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(pos)
        if len(self.larva) < 2 * self.nbases:
            mayinject = True
            if itshatch.tag in self.nextinject:
                if self.frame < self.nextinject[itshatch.tag]:
                    mayinject = False
            if mayinject:
                if itshatch.has_buff(BuffId.QUEENSPAWNLARVATIMER):
                    # print('spawnrest '+str(itshatch.buff_duration_remain))
                    if itshatch.buff_duration_remain < 8 * self.seconds:
                        want = True
                else:
                    want = True
        return want
        
    async def queeninject(self):
        if self.function_listens('queeninject', 11):
            # get some inject queens
            for unt in self.units(UnitTypeId.QUEEN).idle:
                if self.job_of_unit[unt.tag] == self.Job.UNCLEAR:
                    if unt.energy >= 23: # creep pickup is at 27, nurse at 19
                        if self.frame >= self.listenframe_of_unit[unt.tag]:
                            if self.choose_inject(unt.position):
                                pos = unt.position
                                self.job_of_unit[unt.tag] = self.Job.INJECTING
                                itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(pos)
                                self.nextinject[itshatch.tag] = self.frame + 21 * self.seconds
            # move to its spot
            for unt in self.units(UnitTypeId.QUEEN).idle:
                if self.job_of_unit[unt.tag] == self.Job.INJECTING:
                    if self.frame >= self.listenframe_of_unit[unt.tag]:
                        itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(unt.position)
                        itsspot = itshatch.position.towards(self.map_center,4)
                        dist = self.distance(unt.position,itsspot)
                        if dist > 4:
                            unt.move(itsspot)
                            self.listenframe_of_unit[unt.tag] = self.frame + 5
            # inject
            for unt in self.units(UnitTypeId.QUEEN).idle:
                if self.job_of_unit[unt.tag] == self.Job.INJECTING:
                    if self.frame >= self.listenframe_of_unit[unt.tag]:
                        if unt.energy >= 25:
                            itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(unt.position)
                            unt(AbilityId.EFFECT_INJECTLARVA,itshatch)
                            self.job_of_unit[unt.tag] = self.Job.UNCLEAR
                            self.listenframe_of_unit[unt.tag] = self.frame + 100
        
    async def transfuse(self):
        if self.function_listens('transfusion', self.seconds):
            nurses = self.jobcount(self.Job.NURSE)
            patients = self.jobcount(self.Job.WOUNDED)
            # new nurses
            for unt in self.units(UnitTypeId.QUEEN):
                tag = unt.tag
                if self.job_of_unit[tag] == self.Job.UNCLEAR:
                    if unt.energy >= 19:
                        if 2 * nurses < patients:
                            self.job_of_unit[tag] = self.Job.NURSE
                            nurses += 1
                            unt.attack(self.hospital)
            # dismiss nurses
            for unt in self.units(UnitTypeId.QUEEN):
                tag = unt.tag
                if self.job_of_unit[tag] == self.Job.NURSE:
                    if unt.energy == 200:
                        self.job_of_unit[tag] = self.Job.UNCLEAR
            # heal
            for unt in self.units(UnitTypeId.QUEEN):
                tag = unt.tag
                if self.job_of_unit[tag] in {self.Job.NURSE, self.Job.UNCLEAR, self.Job.BIGATTACK}:
                    if unt.energy >= 50:
                        if self.has_creep(unt.position):
                            for other in self.units:
                                worth = False
                                if other.health < other.health_max - 100:
                                    worth = True
                                if other.health < other.health_max - 50:
                                    if unt.energy >= 110:
                                        worth = True
                                if worth:
                                    if other.tag != tag:
                                        if self.frame >= self.listenframe_of_unit[tag]:
                                            may_treat_it = True
                                            if other.tag in self.treating:
                                                if self.frame < self.treating[other.tag]:
                                                    may_treat_it = False
                                            if may_treat_it:
                                                dist = self.distance(unt.position,other.position)
                                                if dist < 7:
                                                    unt(AbilityId.TRANSFUSION_TRANSFUSION,other)
                                                    self.listenframe_of_unit[tag] = self.frame + 5
                                                    self.treating[other.tag] = self.frame + 7 * self.seconds
                        
