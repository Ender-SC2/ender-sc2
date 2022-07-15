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


    def __step0(self):
        pass

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.chatting()
        #await self.show()

    async def show(self):
        logger.info('---------------- ' + str(self.frame) + '--------------------')
        lines = []
        for unt in self.units:
            pos = unt.position
            job = self.job_of_unit(unt)
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
                    if len(words) == 2:
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


