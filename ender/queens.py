# queens.py, Ender

from ender.common import Common
from ender.job import Job
from ender.utils.point_utils import distance
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class Queens(Common):

    __did_step0 = False
    nextinject = {}  # per hatch to prevent overinjecting
    treating = {}  # per patient the next treating moment
    mineralside = {}  # per expopos
    # queen_of_hall is in common.py

    def __step0(self):
        self.init_mineralside()

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.queeninject()
        await self.transfuse()
        await self.admin_queen_of_hall()
        await self.transfer()

    def want_injects(self) -> bool:
        return len(self.larva) < 2 * self.nbases

    def choose_inject(self, pos) -> bool:
        # for a queen at pos
        want = False
        itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(pos)
        if itshatch.build_progress == 1:
            if self.want_injects():
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
        if self.function_listens("queeninject", 11):
            # get some inject queens
            for unt in self.units(UnitTypeId.QUEEN).idle:
                if self.job_of_unit(unt) == Job.UNCLEAR:
                    if unt.energy >= 23:  # creep pickup is at 27, nurse at 19
                        if self.frame >= self.listenframe_of_unit[unt.tag]:
                            if self.choose_inject(unt.position):
                                pos = unt.position
                                self.set_job_of_unit(unt, Job.INJECTER)
                                itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(pos)
                                if itshatch.build_progress == 1:
                                    self.nextinject[itshatch.tag] = self.frame + 21 * self.seconds
            # move to its spot
            for unt in self.units(UnitTypeId.QUEEN).idle:
                if self.job_of_unit(unt) == Job.INJECTER:
                    if self.frame >= self.listenframe_of_unit[unt.tag]:
                        itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(unt.position)
                        itsspot = self.get_mineralside(itshatch.position)
                        dist = distance(unt.position, itsspot)
                        if dist > 4:
                            unt.move(itsspot)
                            self.listenframe_of_unit[unt.tag] = self.frame + 5
            # inject
            for unt in self.units(UnitTypeId.QUEEN).idle:
                if self.job_of_unit(unt) == Job.INJECTER:
                    if self.frame >= self.listenframe_of_unit[unt.tag]:
                        if unt.energy >= 25:
                            itshatch = self.structures(UnitTypeId.HATCHERY).closest_to(unt.position)
                            if itshatch.build_progress == 1:
                                unt(AbilityId.EFFECT_INJECTLARVA, itshatch)
                                self.set_job_of_unit(unt, Job.UNCLEAR)
                                self.listenframe_of_unit[unt.tag] = self.frame + 100

    async def transfuse(self):
        if self.function_listens("transfusion", self.seconds):
            nurses = self.job_count(Job.NURSE)
            patients = 0
            for unt in self.units:
                if self.job_of_unit(unt) == Job.WOUNDED:
                    if unt.type_id not in {
                        UnitTypeId.ZERGLING,
                        UnitTypeId.ROACH,
                        UnitTypeId.ROACHBURROWED,
                        UnitTypeId.OVERLORD,
                    }:
                        patients += 1
            # new nurses
            for unt in self.units(UnitTypeId.QUEEN):
                if self.job_of_unit(unt) == Job.UNCLEAR:
                    if unt.energy >= 19:
                        if 2 * nurses < patients:
                            self.set_job_of_unit(unt, Job.NURSE)
                            nurses += 1
                            unt.attack(self.hospital)
                            # this may cost queen_of_hall
                            for halltype in self.all_halltypes:
                                for hall in self.structures(halltype):
                                    if hall.tag in self.queen_of_hall:
                                        if self.queen_of_hall[hall.tag] == unt.tag:
                                            del self.queen_of_hall[hall.tag]
            # dismiss nurses
            for unt in self.units(UnitTypeId.QUEEN):
                if self.job_of_unit(unt) == Job.NURSE:
                    if unt.energy == 200:
                        self.set_job_of_unit(unt, Job.UNCLEAR)
            # heal
            for unt in self.units(UnitTypeId.QUEEN):
                tag = unt.tag
                if self.job_of_unit(unt) in [Job.NURSE, Job.UNCLEAR, Job.DEFENDATTACK]:
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
                                                dist = distance(unt.position, other.position)
                                                if dist < 7:
                                                    unt(AbilityId.TRANSFUSION_TRANSFUSION, other)
                                                    self.listenframe_of_unit[tag] = self.frame + 5
                                                    self.treating[other.tag] = self.frame + 7 * self.seconds

    async def admin_queen_of_hall(self):
        if self.function_listens("admin_queen_of_hall", 1.3 * self.seconds):
            # hall or queen is dead
            todel = set()
            for halltag in self.queen_of_hall:
                if halltag not in self.living:
                    todel.add(halltag)
                tag = self.queen_of_hall[halltag]
                if tag == self.notag:
                    pass  # queen is not yet born
                else:
                    if tag not in self.living:
                        todel.add(halltag)
            for halltag in todel:
                del self.queen_of_hall[halltag]
            # assign new queen to the closest free hall
            for que in self.units(UnitTypeId.QUEEN):
                if self.job_of_unit(que) == Job.UNCLEAR:
                    if que.tag not in self.queen_of_hall.values():
                        bestdist = 20
                        for halltype in self.all_halltypes:
                            for hall in self.structures(halltype):
                                halltag == hall.tag
                                canmatch = False
                                if halltag in self.queen_of_hall:
                                    if self.queen_of_hall[halltag] == self.notag:  # not yet born
                                        canmatch = True
                                else:
                                    canmatch = True
                                if canmatch:
                                    dist = distance(que.position, hall.position)
                                    if dist < bestdist:
                                        bestdist = dist
                                        besthall = hall
                        if bestdist < 20:
                            self.queen_of_hall[besthall.tag] = que.tag
                            que.move(besthall.position)
            # assign free hall to the closest free queen
            for halltag in self.queen_of_hall:
                canmatch = False
                if halltag in self.queen_of_hall:
                    if self.queen_of_hall[halltag] == self.notag:  # not yet born
                        canmatch = True
                else:
                    canmatch = True
                if canmatch:
                    for halltype in self.all_halltypes:
                        for hall in self.structures(halltype):
                            if hall.tag == halltag:
                                bestdist = 60
                                for que in self.units(UnitTypeId.QUEEN):
                                    if self.job_of_unit(que) != Job.NURSE:
                                        if que.tag not in self.queen_of_hall.values():
                                            dist = distance(que.position, hall.position)
                                            if dist < bestdist:
                                                bestdist = dist
                                                bestqueen = que
                                if bestdist < 60:
                                    que = bestqueen
                                    self.queen_of_hall[halltag] = que.tag
                                    self.set_job_of_unit(que, Job.UNCLEAR)
                                    que.move(hall.position)

    def init_mineralside(self):
        self.mineralside = {}
        for expo in self.expansion_locations:
            side = self.map_center
            minerals = self.mineral_field.closer_than(8, expo)
            if minerals:
                side = minerals.center
            self.mineralside[expo] = expo.towards(side, 4)

    def get_mineralside(self, expos: Point2) -> Point2:
        if expos in self.mineralside:
            return self.mineralside[expos]
        else:
            return expos.towards(self.map_center, 4)

    def hall_makes_queen(self, hall) -> bool:
        makes = False
        for order in hall.orders:
            if order.ability.id == AbilityId.TRAINQUEEN_QUEEN:
                makes = True
        return makes

    async def transfer(self):
        # If a queen is made at a near hatch, at that near hatch the existing queen can switch with the queen-being-made.
        if self.function_listens("transfer", 18):
            tohalls = set()
            for halltyp in self.all_halltypes:
                for hall in self.structures(halltyp):
                    if hall.tag in self.queen_of_hall:
                        if self.queen_of_hall[hall.tag] == self.notag:
                            if not self.hall_makes_queen(hall):
                                tohalls.add(hall)
            if len(tohalls) > 0:
                for que in self.units(UnitTypeId.QUEEN):
                    if self.job_of_unit(que) == Job.UNCLEAR:
                        if self.frame >= self.listenframe_of_unit[que.tag]:
                            for halltyp in self.all_halltypes:
                                for hall in self.structures(halltyp):
                                    if hall.tag in self.queen_of_hall:
                                        if que.tag == self.queen_of_hall[hall.tag]:
                                            if self.hall_makes_queen(hall):
                                                if que.energy < 15:
                                                    # this queen could transfer
                                                    bestdist = 99999
                                                    for tohall in tohalls:
                                                        dist = distance(que.position, tohall.position)
                                                        if dist < bestdist:
                                                            bestdist = dist
                                                            besttohall = tohall
                                                    if bestdist < 99999:
                                                        # transfer
                                                        self.queen_of_hall[hall.tag] = self.notag
                                                        self.queen_of_hall[besttohall.tag] = que.tag
                                                        que.attack(besttohall.position)  # moves there
                                                        self.listenframe_of_unit[que.tag] = self.frame + 50
                                                        tohalls.remove(besttohall)
