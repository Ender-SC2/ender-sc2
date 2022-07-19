# overlords.py, Ender

import os
import random

from loguru import logger

from ender.common import Common
from ender.job import Job
from ender.utils.point_utils import distance
from ender.utils.unit_utils import range_vs
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


# creepdropping is in creep.py
# creeplords are in creep.py


class Overlords(Common):

    __did_step0 = False
    laired = False
    readoverlord = False
    scoutlords = {}  # numbering the overlords with fixed routes
    overlordplan = set()  # for scoutlords
    tension_points = set()
    trips = set()  # of (passenger.tag, overlordtransport.tag)    Both unique
    trip_goal = {}  # per trip: a goal
    trip_phase = {}  # per trip: none -> destined -> phoned -> flying -> falling
    passenger_types = [UnitTypeId.LURKERMP, UnitTypeId.BANELING, UnitTypeId.DRONE]
    passenger_morphs = {
        UnitTypeId.LURKERMP,
        UnitTypeId.BANELING,
        UnitTypeId.DRONE,
        UnitTypeId.LURKERMPBURROWED,
        UnitTypeId.BANELINGBURROWED,
        UnitTypeId.SPINECRAWLER,
    }
    freespine_couples = set()

    def __step0(self):
        for ovi in self.units(UnitTypeId.OVERLORD):
            ovi.move(self.map_center)

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.spread()
        await self.overlordscout()
        await self.onlair()
        await self.over_micro()
        await self.transport()
        await self.do_freespine()

    async def spread(self):
        if self.function_listens("spread", 30):
            # recruit
            for ovi in self.units(UnitTypeId.OVERLORD):
                if self.job_of_unit(ovi) == Job.UNCLEAR:
                    self.set_job_of_unit(ovi, Job.ROAMER)
            # move random
            for ovi in self.units(UnitTypeId.OVERLORD).idle:
                if self.job_of_unit(ovi) == Job.ROAMER:
                    goal = self.random_mappoint()
                    ovi.move(goal)
                    # hang still at goal
                    if self.laired:
                        self.set_job_of_unit(ovi, Job.HANGER)

    def random_mappoint(self) -> Point2:
        return Point2(
            (random.randrange(self.map_left, self.map_right), random.randrange(self.map_bottom, self.map_top))
        )

    async def onlair(self):
        if self.function_listens("onlair", 35):
            if not self.laired:
                if self.lairtech:
                    self.laired = True

    async def overlordscout(self):
        if self.function_listens("overlordscout", 10):
            # mapdependant points
            if self.frame > 5 * self.seconds:
                if not self.readoverlord:
                    self.readoverlord = True
                    #
                    mapname = self.family(self.game_info.map_name)
                    startx = str(self.ourmain.x)
                    starty = str(self.ourmain.y)
                    #
                    # overlords.txt: has lines e.g.:   atmospheres 186.5 174.5 0 3.5 20.6 20.3
                    # So on map 2000Atmospheres.AIE starting (186.5,174.5), move lord 0 at 3.5 seconds to (20.6,20.3)
                    self.overlordplan = set()
                    logger.info("reading data/overlords.txt")
                    pl = open(os.path.join("data", "overlords.txt"), "r")
                    lines = pl.read().splitlines()
                    pl.close()
                    for line in lines:
                        # logger.info(line) # debug
                        words = line.split()
                        if len(words) > 0:
                            if words[0] != "#":
                                if (words[0] == mapname) and (words[1] == startx) and (words[2] == starty):
                                    self.overlordplan.add(
                                        (float(words[3]), float(words[4]), float(words[5]), float(words[6]))
                                    )
                    if len(self.overlordplan) == 0:
                        self.overlordplan.add((0, 0, self.enemymain.x, self.enemymain.y))
                        logger.info("append to data/overlords.txt:")
                        logger.info(
                            mapname
                            + " "
                            + startx
                            + " "
                            + starty
                            + " 0 0 "
                            + str(self.enemymain.x)
                            + " "
                            + str(self.enemymain.y)
                        )
                # id the lords
                if len(self.units(UnitTypeId.OVERLORD)) > len(self.scoutlords):
                    for ovi in self.units(UnitTypeId.OVERLORD):
                        if ovi.tag not in self.scoutlords.values():
                            nr = len(self.scoutlords)
                            self.scoutlords[nr] = ovi.tag
                # move the lords
                used = set()
                for moveplan in self.overlordplan:
                    (o_id, o_sec, o_x, o_y) = moveplan
                    pos = Point2((o_x, o_y))
                    if self.frame >= o_sec * self.seconds:
                        if o_id in self.scoutlords:
                            tag = self.scoutlords[o_id]
                            for ovi in self.units(UnitTypeId.OVERLORD):
                                if ovi.tag == tag:
                                    self.set_job_of_unittag(tag, Job.HANGER)
                                    ovi.move(pos)
                                    used.add(moveplan)
                self.overlordplan -= used

    async def over_micro(self):
        if self.function_listens("over_micro", 9):
            for ovi in self.units(UnitTypeId.OVERLORD):
                if self.job_of_unit(ovi) in {Job.ROAMER, Job.HANGER}:
                    enemies = self.enemy_units.filter(lambda ene: distance(ene.position, ovi.position) < 13).filter(
                        lambda ene: range_vs(ene, ovi) > 0
                    )
                    enemies |= self.enemy_structures.filter(
                        lambda ene: distance(ene.position, ovi.position) < 13
                    ).filter(lambda ene: range_vs(ene, ovi) > 0)
                    rangedist = 99999
                    for ene in enemies:
                        rd = distance(ovi.position, ene.position) - range_vs(ene, ovi)
                        if rd < rangedist:
                            rangedist = rd
                            monster = ene
                    if rangedist < 99999:
                        if rangedist != 0:
                            self.tension_point_add(ovi.position)
                            goal = ovi.position.towards(monster.position, -1)
                            ovi.move(goal)

    def tension_point_add(self, point: Point2):
        dist = 99999
        for apoint in self.tension_points:
            dist = min(distance(point, apoint), dist)
        if dist > 3:
            self.tension_points.add(point)  # not yet used

    def in_trips_passenger(self, tag) -> bool:
        for (pastag, lortag) in self.trips:
            if tag == pastag:
                return True
        return False

    def in_trips_lor(self, tag) -> bool:
        for (pastag, lortag) in self.trips:
            if tag == lortag:
                return True
        return False

    async def transport(self):
        if self.function_listens("transport", 11):
            # log
            # for lor in self.units(UnitTypeId.OVERLORDTRANSPORT):
            #    job = self.job_of_unit(lor)
            #    logger.info('Overlordtransport ' + job.name)
            # logger.info('freespine_couples: ' + str(self.freespine_couples))
            # trips gone wrong
            todel = set()
            for trip in self.trips:
                (pastag, lortag) = trip
                if pastag not in self.living:
                    todel.add(trip)
                if lortag not in self.living:
                    todel.add(trip)
            self.trips -= todel
            for (pastag, lortag) in todel:
                for lor in self.units(UnitTypeId.OVERLORDTRANSPORT):
                    if lor.tag == lortag:
                        if self.job_of_unit(lor) == Job.TRANSPORTER:
                            self.set_job_of_unit(lor, Job.UNCLEAR)
                for pastype in self.passenger_morphs:
                    for pas in self.units(pastype):  # buildings have no job
                        if pas.tag == pastag:
                            if self.job_of_unit(pas) == Job.TRANSPORTER:
                                self.set_job_of_unit(pas, Job.UNCLEAR)
            # log
            # for trip in self.trips:
            #    stri = 'trip'
            #    (pastag, lortag) = trip
            #    for unt in self.units:
            #        if unt.tag == pastag:
            #            stri += ' ' + unt.name
            #    for unt in self.units:
            #        if unt.tag == lortag:
            #            stri += ' ' + unt.name
            #    stri += ' ' + self.trip_phase[trip]
            #    logger.info(stri)
            #
            if self.lairtech:
                # make trips
                goals = [self.enemymain]
                for postag in self.enemy_struc_mem:
                    (typ, pos) = self.enemy_struc_mem[postag]
                    if typ in self.all_halltypes:
                        goals.append(pos)
                goal = random.choice(goals)
                bestdist = 99999
                for lor in self.units(UnitTypeId.OVERLORDTRANSPORT):
                    if self.frame >= self.listenframe_of_unit[lor.tag]:
                        if self.job_of_unit(lor) in {Job.UNCLEAR, Job.HANGER, Job.ROAMER}:  # premorph jobs
                            if lor.health >= 50:
                                if self.blue_half(lor.tag):
                                    dist = distance(lor.position, goal)
                                    if dist < bestdist:
                                        bestdist = dist
                                        bestlord = lor
                if bestdist < 99999:
                    bestdist = 99999
                    for pastype in self.passenger_types:
                        for pas in self.units(pastype):
                            if self.job_of_unit(pas) in {Job.UNCLEAR, Job.VOLUNTEER, Job.MIMMINER, Job.DEFENDATTACK}:
                                dist = distance(pas.position, goal) + 200 * self.passenger_types.index(pastype)
                                if dist < bestdist:
                                    bestdist = dist
                                    bestpas = pas
                                    if pastype == UnitTypeId.DRONE:
                                        bestgoal = goal.towards(self.ourmain, 4)
                                    else:
                                        bestgoal = goal.towards(self.map_center, -4)
                    if bestdist < 99999:
                        self.set_job_of_unit(bestpas, Job.TRANSPORTER)
                        self.set_job_of_unit(bestlord, Job.TRANSPORTER)
                        trip = (bestpas.tag, bestlord.tag)
                        self.trips.add(trip)
                        self.trip_goal[trip] = bestgoal
                        self.trip_phase[trip] = "destined"
            # per trip (both visible)
            todel = set()
            for trip in self.trips:
                goal = self.trip_goal[trip]
                (pastag, lortag) = trip
                for pastype in self.passenger_types:
                    for unt in self.units(pastype):
                        if unt.tag == pastag:
                            if self.frame >= self.listenframe_of_unit[unt.tag]:
                                for lor in self.units(UnitTypeId.OVERLORDTRANSPORT):
                                    if self.frame >= self.listenframe_of_unit[lor.tag]:
                                        if lor.tag == lortag:
                                            if self.trip_phase[trip] == "destined":
                                                self.trip_phase[trip] = "phoned"
                                                meetingpoint = Point2(
                                                    (
                                                        0.5 * lor.position.x + 0.5 * unt.position.x,
                                                        0.5 * lor.position.y + 0.5 * unt.position.y,
                                                    )
                                                )
                                                meetingpoint = (lor.position + unt.position) / 2
                                                lor.move(meetingpoint)
                                                self.listenframe_of_unit[lortag] = self.frame + self.seconds
                                                unt.move(meetingpoint)
                                                self.listenframe_of_unit[pastag] = self.frame + self.seconds
                                            # remeet on idle
                                            elif self.trip_phase[trip] == "phoned":
                                                if distance(unt.position, lor.position) < 2:
                                                    self.trip_phase[trip] = "flying"
                                                    lor(AbilityId.LOAD_OVERLORD, unt)
                                                    lor(AbilityId.MOVE_MOVE, goal, queue=True)
                                                    self.listenframe_of_unit[lortag] = self.frame + 8 * self.seconds
                                                    self.listenframe_of_unit[pastag] = self.frame + 4 * self.seconds
                                                elif len(lor.orders) == 0:
                                                    if distance(unt.position, lor.position) >= 2:
                                                        lor.move(unt.position)
                                                        self.listenframe_of_unit[lortag] = self.frame + self.seconds
                                            elif self.trip_phase[trip] == "falling":
                                                del self.trip_goal[trip]
                                                del self.trip_phase[trip]
                                                todel.add(trip)
                                                if unt.type_id == UnitTypeId.LURKERMP:
                                                    self.set_job_of_unittag(pastag, Job.HOLY)
                                                    unt(AbilityId.BURROWDOWN_LURKER)
                                                    self.listenframe_of_unit[pastag] = self.frame + 4 * self.seconds
                                                    self.set_job_of_unittag(lortag, Job.UNCLEAR)
                                                    lor.move(self.ourmain)
                                                    self.listenframe_of_unit[lortag] = self.frame + self.seconds
                                                elif unt.type_id == UnitTypeId.DRONE:
                                                    self.set_job_of_unittag(lortag, Job.FREESPINE)
                                                    self.set_job_of_unittag(pastag, Job.FREESPINE)
                                                    self.listenframe_of_unit[pastag] = self.frame + 2 * self.seconds
                                                    self.listenframe_of_unit[lortag] = self.frame + self.seconds
                                                    self.freespine_couples.add((pastag, lortag))
                                                elif unt.type_id == UnitTypeId.BANELING:
                                                    self.set_job_of_unittag(pastag, Job.HOLY)
                                                    if random.random() < 0.5:
                                                        unt(AbilityId.BURROWDOWN_BANELING)
                                                    self.listenframe_of_unit[pastag] = self.frame + self.seconds
                                                    self.set_job_of_unittag(lortag, Job.UNCLEAR)
                                                    lor.move(self.ourmain)
                                                    self.listenframe_of_unit[lortag] = self.frame + self.seconds
                                                else:  # passenger may have morphed already
                                                    self.set_job_of_unittag(lortag, Job.UNCLEAR)
                                                    lor.move(self.ourmain)
                                                    self.listenframe_of_unit[lortag] = self.frame + self.seconds
            self.trips -= todel
            # per trip (transport visible)
            todel = set()
            for trip in self.trips:
                goal = self.trip_goal[trip]
                (pastag, lortag) = trip
                for lor in self.units(UnitTypeId.OVERLORDTRANSPORT):
                    if self.frame >= self.listenframe_of_unit[lor.tag]:
                        if lor.tag == lortag:
                            if self.trip_phase[trip] == "flying":
                                if distance(lor.position, goal) < 1:
                                    self.trip_phase[trip] = "falling"
                                    lor(AbilityId.UNLOADALLAT_OVERLORD, goal)
                                    self.listenframe_of_unit[lortag] = self.frame + 3 * self.seconds
                                    self.listenframe_of_unit[pastag] = self.frame + 3 * self.seconds
                                elif lor.health < 50:
                                    goal = lor.position
                                    self.trip_goal[trip] = goal
                                elif len(lor.orders) == 0:
                                    if distance(lor.position, goal) >= 2:
                                        lor.move(goal)
                                        self.listenframe_of_unit[lortag] = self.frame + self.seconds
                            elif self.trip_phase[trip] == "falling":
                                # we may have missed the exploding of the passenger
                                del self.trip_goal[trip]
                                del self.trip_phase[trip]
                                todel.add(trip)
                                self.set_job_of_unittag(lortag, Job.UNCLEAR)
                                lor.move(self.ourmain)
                                self.listenframe_of_unit[lortag] = self.frame + self.seconds
            self.trips -= todel

    async def do_freespine(self):
        # a freespine_couple is (overlordtransport FREESPINE, drone or spinecrawler FREESPINE)
        # dismiss
        if self.function_listens("do_freespine", 17):
            todel = set()
            for couple in self.freespine_couples:
                (unttag, lortag) = couple
                seen = 0
                for lor in self.units(UnitTypeId.OVERLORDTRANSPORT):
                    if lor.tag == lortag:
                        if self.job_of_unit(lor) == Job.FREESPINE:
                            seen += 1
                for unt in self.units(UnitTypeId.DRONE):
                    if unt.tag == unttag:
                        if self.job_of_unit(unt) == Job.FREESPINE:
                            seen += 1
                for unt in self.structures(UnitTypeId.SPINECRAWLER):
                    if unt.tag == unttag:
                        seen += 1
                if seen < 2:
                    todel.add(couple)
            self.freespine_couples -= todel
            for (unttag, lortag) in todel:
                logger.info("deleting freespine duo " + str(unttag) + "," + str(lortag))
                for lor in self.units(UnitTypeId.OVERLORDTRANSPORT):
                    if lor.tag == lortag:
                        if self.job_of_unit(lor) == Job.FREESPINE:
                            self.set_job_of_unit(lor, Job.UNCLEAR)
                for unt in self.units(UnitTypeId.DRONE):
                    if unt.tag == unttag:
                        if self.job_of_unit(unt) == Job.FREESPINE:
                            self.set_job_of_unit(unt, Job.UNCLEAR)
                for unt in self.structures(UnitTypeId.SPINECRAWLER):
                    if unt.tag == unttag:
                        if self.job_of_unit(unt) == Job.FREESPINE:
                            self.set_job_of_unit(unt, Job.UNCLEAR)
        # actions are in making.py
