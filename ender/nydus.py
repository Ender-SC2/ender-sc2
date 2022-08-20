# nydus.py, Ender

from loguru import logger

from ender.common import Common
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from ender.utils.point_utils import distance


class Nydus(Common):

    __did_step0 = False
    #
    via_nydus = False
    nydus_in = None
    nydus_out = None
    nydus_in_pos = None
    nydus_out_pos = None

    def __step0(self):
        pass

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.do_nydus()

    async def do_nydus(self):
        if self.via_nydus:
            self.nydus_out(AbilityId.SMART)

    def set_nydus(self, aa: Point2, bb: Point2):
        distland = distance(aa, bb)
        distaa = 99999
        for nydus in self.structures(UnitTypeId.NYDUSNETWORK) | self.structures(UnitTypeId.NYDUSCANAL):
            dist = distance(aa, nydus)
            if dist < distaa:
                distaa = dist
                self.nydus_in = nydus
                self.nydus_in_pos = nydus.position
        distbb = 99999
        for nydus in self.structures(UnitTypeId.NYDUSNETWORK) | self.structures(UnitTypeId.NYDUSCANAL):
            dist = distance(nydus, bb)
            if dist < distbb:
                distbb = dist
                self.nydus_out = nydus
                self.nydus_out_pos = nydus.position
        self.via_nydus = (distaa + distbb < distland)

    def attack_via_nydus(self, unt):
        pos = unt.position
        goal = self.attack_goal[unt.tag]
        nyd = self.via_nydus
        if unt.is_flying:
            nyd = False
        if unt.type_id in self.all_changelings:
            nyd = False
        if nyd:
            if distance(pos, self.nydus_in_pos) + distance(pos, self.nydus_out_pos) < distance(pos, goal):
                if distance(pos, self.nydus_in_pos) > 5:
                    unt.attack(self.nydus_in_pos)
                else:
                    if self.frame >= self.wait_of_unit[self.nydus_in.tag]:
                        self.nydus_in(AbilityId.LOAD_NYDUSNETWORK, unt)
                        self.wait_of_unit[self.nydus_in.tag] = self.frame + 0.18 * self.seconds
            else:
                unt.attack(goal)
        else:
            unt.attack(goal)
