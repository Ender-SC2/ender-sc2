# lingscout.py, Ender

import os

from loguru import logger

from ender.common import Common
from ender.job import Job
from sc2.ids.unit_typeid import UnitTypeId
from ender.utils.point_utils import distance


class Lingscout(Common):

    __did_step0 = False
    nextscout = 0
    lingscout_tag = 0
    scoutplan = []
    scout_nextgoal = None
    #

    def __step0(self):
        pass

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.do_lingscout()

    async def do_lingscout(self):
        if self.function_listens("lingscout", 10):  # so no code needed to prevent double orders
            startminutes = 3.3
            endminutes = 12
            interminutes = 0.6
            #
            # go run
            if self.lingscout_tag in self.living:
                # get the scout, near its goal
                scout = None
                for unittype in [UnitTypeId.ZERGLING, UnitTypeId.DRONE]:
                    for unt in self.units(unittype):
                        if unt.tag == self.lingscout_tag:
                            if self.job_of_unit(unt) == Job.SCOUT:
                                dist = distance(unt.position, self.scout_nextgoal)
                                idling = len(unt.orders) == 0
                                if (dist < 2) or idling:
                                    scout = unt
                if scout:
                    if len(self.scoutplan) > 0:
                        goal = self.scoutplan.pop(0)
                        scout.move(goal)
                        self.scout_nextgoal = goal
                    else:  # finished
                        self.set_job_of_unit(scout, Job.UNCLEAR)
                        self.lingscout_tag = 0
            #
            if self.nextscout == 0:
                self.nextscout = startminutes * self.minutes
            if self.nextscout >= endminutes * self.minutes:
                self.nextscout = 9999999
            if self.nextscout < self.frame < self.nextscout + self.seconds:
                self.nextscout += interminutes * self.minutes
                # is there a scout?
                scout = None
                for unittype in [UnitTypeId.ZERGLING, UnitTypeId.DRONE]:
                    for unt in self.units(unittype):
                        if unt.tag == self.lingscout_tag:
                            if self.job_of_unit(unt) == Job.SCOUT:
                                scout = unt
                if not scout:
                    # get new scout if possible
                    for unittype in [UnitTypeId.ZERGLING, UnitTypeId.DRONE]:
                        for unt in self.units(unittype):
                            if self.lingscout_tag not in self.living:
                                job = self.job_of_unit(unt)
                                if job not in {Job.BUILDER, Job.WALKER}:
                                    # logger.info('Scout made, was ' + job.name)
                                    # for order in unt.orders:
                                    #     logger.info('Scout did ' + order.ability.friendly_name)
                                    self.lingscout_tag = unt.tag
                                    self.set_job_of_unit(unt, Job.SCOUT)
                                    scout = unt
                if scout:
                    if len(self.scoutplan) == 0:
                        self.make_scoutplan(scout.position)
                    # start run
                    if len(self.scoutplan) > 0:
                        goal = self.scoutplan.pop(0)
                        scout.move(goal)
                        self.scout_nextgoal = goal

    def make_scoutplan(self, startpos):
        self.scoutplan = []
        toscoutpos = set()
        for expo in self.freeexpos:
            toscoutpos.add(expo.towards(self.map_center, 6))  # Will approach 6+2
        nowpos = startpos
        while len(toscoutpos) > 0:
            bestdist = 99999
            for apos in toscoutpos:
                dist = distance(apos, nowpos)
                if dist < bestdist:
                    bestdist = dist
                    bestpos = apos
            toscoutpos.remove(bestpos)
            self.scoutplan.append(bestpos)
            nowpos = bestpos
