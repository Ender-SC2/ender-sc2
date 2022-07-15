# antiair.py, Merkbot, Zerg bot
# 20 may 2022

from ender.common import Common

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class Antiair(Common):

    __did_step0 = False
    static_antiair_types = []
    antiair_pos = set()  # set of positions of enemy antiairor buildings
    antiair_hash = 0  # to notice changes in antiair
    antiair_range = 7
    antiair_problem_pos = None  # a hint given by flystraight
    _last_enemy_struc_mem_hash = 0
    #

    def __step0(self):
        self.static_antiair_types = [
            UnitTypeId.BUNKER,
            UnitTypeId.MISSILETURRET,
            UnitTypeId.PHOTONCANNON,
            UnitTypeId.SPORECRAWLER,
        ]
        self.antiair_problem_pos = self.nowhere
        #

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.get_antiair_pos()

    async def get_antiair_pos(self):
        if self._last_enemy_struc_mem_hash != self.enemy_struc_mem_hash:
            self._last_enemy_struc_mem_hash = self.enemy_struc_mem_hash
            antiairs = set()  # set of positions of enemy antiairor buildings
            ehash = 0
            for postag in self.enemy_struc_mem:
                tpplus = self.enemy_struc_mem[postag]
                (typ, pos) = tpplus
                if typ in self.static_antiair_types:
                    antiairs.add(pos)
                    ehash += postag
            if self.antiair_hash != ehash:
                self.antiair_hash = ehash
                self.antiair_pos = antiairs
                # changed so recalculate flightplans

    def antiair_ok(self, point) -> bool:
        ok = True
        for aap in self.antiair:
            if self.near(aap, point, self.antiair_range):
                ok = False
        return ok

    def antiair_point(self, around) -> Point2:
        # get a point near 'around' but probably without antiair, probably in the map
        goal = around
        if not self.unantiair_ok(goal):
            away = self.random_mappoint()
            while not self.antiair_ok(away):
                away = self.random_mappoint()
            tries = 0
            while (not self.antiair_ok(goal)) and (tries < 7):
                tries += 1
                for aap in self.antiair:
                    if self.near(aap, goal, 1):
                        goal = goal.towards(away, 1)
                    elif self.near(aap, goal, self.antiair_range):
                        goal = aap.towards(goal, self.antiair_range)
                        goal = self.into_map(goal)
            while (not self.antiair_ok(goal)) and (tries < 77):
                tries += 1
                goal = goal.towards(away, 1)
        return goal

    def flystraight(self, aa, bb) -> bool:
        # can fly straight from aa to bb, no antiairor in self.antiair_range?
        # bb should not be aa
        dist = self.circledist(aa, bb)
        mid = Point2(((aa.x + bb.x) / 2, (aa.y + bb.y) / 2))
        aabbvec = ((bb.x - aa.x) / dist, (bb.y - aa.y) / dist)
        perpendic = ((aa.y - bb.y) / dist, (bb.x - aa.x) / dist)
        straight = True
        for aap in self.antiair_pos:
            if self.near(aap, mid, self.antiair_range + dist / 2):
                tooclose = False
                if self.near(aap, aa, self.antiair_range):
                    tooclose = True
                    self.antiair_problem_pos = aap
                if self.near(aap, bb, self.antiair_range):
                    tooclose = True
                    self.antiair_problem_pos = aap
                aaaap = (aap.x - aa.x, aap.y - aa.y)
                inprovec = aaaap[0] * aabbvec[0] + aaaap[1] * aabbvec[1]
                inproper = aaaap[0] * perpendic[0] + aaaap[1] * perpendic[1]
                if (inprovec > 0) and (inprovec < dist):
                    if abs(inproper) < self.antiair_range:
                        tooclose = True
                        self.antiair_problem_pos = aap
                straight = straight and not tooclose
        return straight

    def flightplan(self, aa, bb):
        # gives a plan to fly from aa to bb; a list of points including aa and bb at the ends
        cc = self.antiair_point(bb)
        plan = [aa, cc]
        problem = True
        while problem and (len(plan) < 10):
            problem = False
            for ix in range(0, len(plan) - 1):
                iy = ix + 1
                xx = plan[ix]
                yy = plan[iy]
                if not self.flystraight(xx, yy):
                    problem = True
                    mid = Point2(((xx.x + yy.x) / 2, (xx.y + yy.y) / 2))
                    aap = self.antiair_problem_pos
                    point = aap.towards(mid, self.antiair_range + 1)  # hope to not go exactly over it
                    plan.insert(iy, point)
        return plan
