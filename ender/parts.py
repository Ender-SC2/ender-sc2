# parts.py, Ender

import os

from loguru import logger

from ender.common import Common
from ender.utils.type_utils import get_version
from ender.job import Job
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from ender.utils.point_utils import distance


class Parts(Common):

    bot_name = "Ender by MerkMore and Ratosh"

    __did_step0 = False
    #
    chatted = False
    enemy_species = "unknown"
    opponent = "unknown"
    botnames = {}
    #
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
        await self.chatting()
        # await self.show() # can be commented out. Slows execution.
        await self.lingscout()

    async def show(self):
        logger.info("---------------- " + str(self.frame) + "--------------------")
        lines = []
        for unt in self.units():
            pos = unt.position
            job = self.job_of_unit(unt)
            ord = ""
            for order in unt.orders:
                ord += order.ability.exact_id.name + " "
            lines.append(unt.type_id.name + "   " + str(pos.x) + "," + str(pos.y) + "   " + str(job) + "   " + ord)
        for stru in self.structures:
            pos = stru.position
            lines.append(stru.type_id.name + "   " + str(pos.x) + "," + str(pos.y) + "   " + str(stru.tag))
        for claim in self.claims:
            (typ, resources, importance, expiration) = claim
            lines.append("<" + typ.name + "   " + str(expiration) + ">")
        lines.sort()
        for line in lines:
            logger.info(line)

    async def chatting(self):
        if self.frame >= 7.7 * self.seconds:
            if not self.chatted:
                self.chatted = True
                # enemy_species
                if self.enemy_race == Race.Zerg:
                    self.enemy_species = "zerg"
                elif self.enemy_race == Race.Terran:
                    self.enemy_species = "terran"
                elif self.enemy_race == Race.Protoss:
                    self.enemy_species = "protoss"
                else:
                    self.enemy_species = "someone"
                # opponent
                self.opponent = self.opponent_id
                if self.opponent is None:
                    self.opponent = self.enemy_species
                # botnames
                logger.info("reading data/botnames.txt")
                pl = open(os.path.join("data", "botnames.txt"), "r")
                lines = pl.read().splitlines()
                pl.close()
                self.botnames = {}
                for line in lines:
                    # logger.info(line) # debug
                    words = line.split()
                    if len(words) == 2:
                        code = words[0]
                        human = words[1]
                        self.botnames[code] = human
                # chat
                logger.info(self.bot_name)
                await self.client.chat_send(self.bot_name, team_only=False)
                code = self.opponent[0:8]
                if code in self.botnames:
                    human = self.botnames[code]
                else:
                    human = code
                logger.info("Good luck and have fun, " + human)
                await self.client.chat_send("Good luck and have fun, " + human, team_only=False)
                logger.info("Tag:" + code)
                await self.client.chat_send("Tag:" + code, team_only=False)
                version = get_version()
                logger.info("Tag:" + version)
                await self.client.chat_send("Tag:" + version, team_only=False)

    def family(self, mapname):
        mapfamily = ""
        for ch in mapname.replace("LE", "").replace("AIE", ""):
            if ("a" <= ch <= "z") or ("A" <= ch <= "Z"):
                mapfamily += ch.lower()
        return mapfamily

    async def lingscout(self):
        if self.function_listens("lingscout", 10): # so no code needed to prevent double orders
            startminutes = 3.3
            endminutes = 9
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
                                idling = (len(unt.orders) == 0)
                                if (dist < 2) or idling:
                                    scout = unt
                if scout:
                    if len(self.scoutplan) > 0:
                        goal = self.scoutplan.pop(0)
                        scout.move(goal)
                        self.scout_nextgoal = goal
                    else: # finished
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
            toscoutpos.add(expo.towards(self.map_center, 6)) # Will approach 6+2
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



                
                


