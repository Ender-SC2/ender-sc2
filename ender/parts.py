# parts.py, Ender
import os

from loguru import logger

from ender.common import Common
from ender.utils.type_utils import get_version
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class Parts(Common):

    bot_name = f'Ender by MerkMore and Ratosh'

    __did_step0 = False
    #
    chatted = False
    enemy_species = 'unknown'
    opponent = 'unknown'
    botnames = {}
    #
    startoverlord = False
    readoverlord = False
    lords = {} # numbering the overlords
    overlords = set()


    def __step0(self):
        pass

    async def on_step(self):
        await Common.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.chatting()
        await self.overlordscout()
        #await self.show()
 
                    
                    
    async def show(self):
        logger.info('---------------- ' + str(self.frame) + '--------------------')
        lines = []
        for unt in self.units:
            pos = unt.position
            job = self.job_of_unit[unt.tag]
            ord = ''
            for order in unt.orders:
                ord += order.ability.exact_id.name + ' '
            lines.append(unt.type_id.name + '   ' + str(pos.x) + ',' + str(pos.y) + '   ' + str(job) + '   ' + ord)
        for stru in self.structures:
            pos = stru.position
            lines.append(stru.type_id.name + '   ' + str(pos.x) + ',' + str(pos.y) + '   ' + str(stru.tag))
        for claim in self.claims:
            (typ,resources,importance,expiration) = claim
            lines.append('<' + typ.name + '   ' + str(expiration) + '>')
        lines.sort()
        for line in lines:
            logger.info(line)


    async def chatting(self):
        if self.frame >= 7.7 * self.seconds:
            if not self.chatted:
                self.chatted = True
                # enemy_species
                if self.enemy_race == Race.Zerg:
                    self.enemy_species = 'zerg'
                elif self.enemy_race == Race.Terran:
                    self.enemy_species = 'terran'
                elif self.enemy_race == Race.Protoss:
                    self.enemy_species = 'protoss'
                else:
                    self.enemy_species = 'someone'
                # opponent
                self.opponent = self.opponent_id
                if self.opponent is None:
                    self.opponent = self.enemy_species
                # botnames
                logger.info('reading data/botnames.txt')
                pl = open(os.path.join('data','botnames.txt'),'r')
                lines = pl.read().splitlines()
                pl.close()
                self.botnames = {}
                for line in lines:
                    #logger.info(line) # debug
                    words = line.split()
                    code = words[0]
                    human = words[1]
                    self.botnames[code] = human
                # chat
                logger.info(self.bot_name)
                await self._client.chat_send(self.bot_name, team_only=False)
                code = self.opponent[0:8]
                if code in self.botnames:
                    human = self.botnames[code]
                else:
                    human = code
                logger.info('Good luck and have fun, ' + human)
                await self._client.chat_send('Good luck and have fun, ' + human, team_only=False)
                logger.info('Tag:' + code)
                await self._client.chat_send('Tag:' + code, team_only=False)
                version = get_version()
                logger.info('Tag:' + version)
                await self._client.chat_send('Tag:' + version, team_only=False)

    def family(self, mapname):
        mapfamily = ''
        for ch in mapname.replace('LE', '').replace('AIE', ''):
            if ('a' <= ch <= 'z') or ('A' <= ch <= 'Z'):
                mapfamily += ch.lower()
        return mapfamily

    async def overlordscout(self):
        if self.function_listens('overlordscout',10):
            # initial start
            if not self.startoverlord:
                self.startoverlord = True
                for ovi in self.units(UnitTypeId.OVERLORD):
                    ovi.move(self.map_center)
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
                    self.overlords = set()
                    logger.info('reading data/overlords.txt')
                    pl = open(os.path.join('data','overlords.txt'),'r')
                    lines = pl.read().splitlines()
                    pl.close()
                    for line in lines:
                        #logger.info(line) # debug
                        words = line.split()
                        if len(words) > 0:
                            if words[0] != '#':
                                if (words[0] == mapname) and (words[1] == startx) and (words[2] == starty):
                                    self.overlords.add((float(words[3]), float(words[4]), float(words[5]), float(words[6])))
                    if len(self.overlords) == 0:
                        self.overlords.add((0, 0, self.enemymain.x, self.enemymain.y))
                        logger.info('append to data/overlords.txt:')
                        logger.info(mapname + ' ' + startx + ' ' + starty + ' 0 0 '+str(self.enemymain.x) + ' ' + str(self.enemymain.y))
                # id the lords
                if len(self.units(UnitTypeId.OVERLORD)) > len(self.lords):
                    for ovi in self.units(UnitTypeId.OVERLORD):
                        if ovi.tag not in self.lords.values():
                            nr = len(self.lords)
                            self.lords[nr] = ovi.tag
                # move the lords
                used = set()
                for moveplan in self.overlords:
                    (o_id, o_sec, o_x, o_y) = moveplan
                    pos = Point2((o_x,o_y))
                    if self.frame >= o_sec * self.seconds:
                        if o_id in self.lords:
                            tag = self.lords[o_id]
                            for ovi in self.units(UnitTypeId.OVERLORD):
                                if ovi.tag == tag:
                                    ovi.move(pos)
                                    used.add(moveplan)
                self.overlords -= used


