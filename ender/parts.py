# parts.py, Ender
# 25 may 2022

from ender.common import Common
import sc2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.data import Race
from sc2.position import Point2
import os


class Parts(Common):

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
        self.init_all_structures()

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
        print('---------------- ' + str(self.frame) + '--------------------')
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
            print(line)


    def init_structures(self,species,category,barra,builddura, size):
        self.builddura_of_structure[barra] = builddura
        self.category_of_structure[barra] = category
        self.size_of_structure[barra] = size
        self.species_of_structure[barra] = species

    def init_all_structures(self):
        # list of structures, with species, category,builddura, size. Can be flying, can be lowered.
        # terran
        self.init_structures('T','otherbuilding',UnitTypeId.SUPPLYDEPOT, 21, 2)
        self.init_structures('T','otherbuilding',UnitTypeId.SUPPLYDEPOTLOWERED, 21, 2)
        self.init_structures('T','armybuilding',UnitTypeId.BARRACKS, 46, 3)
        self.init_structures('T','armybuilding',UnitTypeId.BARRACKSFLYING, 46, 3)
        self.init_structures('T','otherbuilding',UnitTypeId.REFINERY, 21, 3)
        self.init_structures('T','otherbuilding',UnitTypeId.REFINERYRICH, 21, 3)
        self.init_structures('T','lab',UnitTypeId.BARRACKSTECHLAB, 18, 2)
        self.init_structures('T','armybuilding',UnitTypeId.FACTORY, 43, 3)
        self.init_structures('T','armybuilding',UnitTypeId.FACTORYFLYING, 43, 3)
        self.init_structures('T','lab',UnitTypeId.FACTORYTECHLAB, 18, 2)
        self.init_structures('T','armybuilding',UnitTypeId.STARPORT, 36, 3)
        self.init_structures('T','armybuilding',UnitTypeId.STARPORTFLYING, 36, 3)
        self.init_structures('T','lab',UnitTypeId.STARPORTTECHLAB, 18, 2)
        self.init_structures('T','lab',UnitTypeId.TECHLAB, 18, 2)
        self.init_structures('T','upgradebuilding',UnitTypeId.FUSIONCORE,46, 3)
        self.init_structures('T','base',UnitTypeId.COMMANDCENTER, 71, 5)
        self.init_structures('T','base',UnitTypeId.COMMANDCENTERFLYING, 71, 5)
        self.init_structures('T','base',UnitTypeId.PLANETARYFORTRESS, 36, 5)
        self.init_structures('T','base',UnitTypeId.ORBITALCOMMAND, 25, 5)
        self.init_structures('T','base',UnitTypeId.ORBITALCOMMANDFLYING, 25, 5)
        self.init_structures('T','upgradebuilding',UnitTypeId.ENGINEERINGBAY, 25, 3)
        self.init_structures('T','otherbuilding',UnitTypeId.MISSILETURRET,18, 2)
        self.init_structures('T','upgradebuilding',UnitTypeId.ARMORY, 46, 3)
        self.init_structures('T','otherbuilding',UnitTypeId.BUNKER, 29, 3)
        self.init_structures('T','otherbuilding',UnitTypeId.SENSORTOWER, 18, 2)
        self.init_structures('T','upgradebuilding',UnitTypeId.GHOSTACADEMY, 20, 3)
        self.init_structures('T','lab',UnitTypeId.BARRACKSREACTOR, 36, 2)
        self.init_structures('T','lab',UnitTypeId.FACTORYREACTOR, 36, 2)
        self.init_structures('T','lab',UnitTypeId.STARPORTREACTOR, 36, 2)
        self.init_structures('T','lab',UnitTypeId.REACTOR, 36, 2)
        self.init_structures('T','otherbuilding',UnitTypeId.AUTOTURRET, 0, 2)
        # protoss
        self.init_structures('P','e',UnitTypeId.NEXUS, 71, 5)
        self.init_structures('P','e',UnitTypeId.PYLON, 18, 2)
        self.init_structures('P','e',UnitTypeId.ASSIMILATOR, 21, 3)
        self.init_structures('P','e',UnitTypeId.ASSIMILATORRICH, 21, 3)
        self.init_structures('P','e',UnitTypeId.GATEWAY, 46, 3)
        self.init_structures('P','e',UnitTypeId.FORGE, 32, 3)
        self.init_structures('P','e',UnitTypeId.PHOTONCANNON, 29, 2)
        self.init_structures('P','e',UnitTypeId.SHIELDBATTERY, 29, 2)
        self.init_structures('P','e',UnitTypeId.WARPGATE, 7, 3)
        self.init_structures('P','e',UnitTypeId.CYBERNETICSCORE, 36, 3)
        self.init_structures('P','e',UnitTypeId.TWILIGHTCOUNCIL, 36, 3)
        self.init_structures('P','e',UnitTypeId.ROBOTICSFACILITY, 46, 3)
        self.init_structures('P','e',UnitTypeId.STARGATE, 43, 3)
        self.init_structures('P','e',UnitTypeId.TEMPLARARCHIVE, 36, 3)
        self.init_structures('P','e',UnitTypeId.DARKSHRINE, 71, 2)
        self.init_structures('P','e',UnitTypeId.ROBOTICSBAY, 46, 3)
        self.init_structures('P','e',UnitTypeId.FLEETBEACON, 43, 3)
        self.init_structures('P','e',UnitTypeId.ORACLESTASISTRAP, 11, 1)
        # zerg
        self.init_structures('Z','e',UnitTypeId.HATCHERY, 71, 5)
        self.init_structures('Z','e',UnitTypeId.LAIR, 57, 5)
        self.init_structures('Z','e',UnitTypeId.HIVE, 71, 5)
        self.init_structures('Z','e',UnitTypeId.EXTRACTOR, 21, 3)
        self.init_structures('Z','e',UnitTypeId.EXTRACTORRICH, 21, 3)
        self.init_structures('Z','e',UnitTypeId.SPAWNINGPOOL, 46, 3)
        self.init_structures('Z','e',UnitTypeId.SPINECRAWLER, 36, 2)
        self.init_structures('Z','e',UnitTypeId.SPORECRAWLER, 21, 2)
        self.init_structures('Z','e',UnitTypeId.SPINECRAWLERUPROOTED, 36, 2)
        self.init_structures('Z','e',UnitTypeId.SPORECRAWLERUPROOTED, 21, 2)
        self.init_structures('Z','e',UnitTypeId.EVOLUTIONCHAMBER, 25, 3)
        self.init_structures('Z','e',UnitTypeId.ROACHWARREN, 39, 3)
        self.init_structures('Z','e',UnitTypeId.BANELINGNEST, 43, 3)
        self.init_structures('Z','e',UnitTypeId.HYDRALISKDEN, 29, 3)
        self.init_structures('Z','e',UnitTypeId.LURKERDENMP, 57, 3)
        self.init_structures('Z','e',UnitTypeId.SPIRE, 71, 3)
        self.init_structures('Z','e',UnitTypeId.GREATERSPIRE, 71, 3)
        self.init_structures('Z','e',UnitTypeId.NYDUSNETWORK, 36, 3)
        self.init_structures('Z','e',UnitTypeId.NYDUSCANAL, 14, 3)
        self.init_structures('Z','e',UnitTypeId.INFESTATIONPIT, 36, 3)
        self.init_structures('Z','e',UnitTypeId.ULTRALISKCAVERN, 46, 3)
        self.init_structures('Z','e',UnitTypeId.CREEPTUMOR, 11, 1)
        self.init_structures('Z','e',UnitTypeId.CREEPTUMORBURROWED, 11, 1)
        self.init_structures('Z','e',UnitTypeId.CREEPTUMORQUEEN, 11, 1)


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
                print('reading data/botnames.txt')
                pl = open(os.path.join('data','botnames.txt'),'r')
                lines = pl.read().splitlines()
                pl.close()
                self.botnames = {}
                for line in lines:
                    #print(line) # debug
                    words = line.split()
                    code = words[0]
                    human = words[1]
                    self.botnames[code] = human
                # chat
                await self._client.chat_send(self.bot_name, team_only=False)
                code = self.opponent[0:8]
                if code in self.botnames:
                    human = self.botnames[code]
                else:
                    human = code
                await self._client.chat_send('Good luck and have fun, ' + human, team_only=False)
                await self._client.chat_send('Tag:' + code, team_only=False)
                await self._client.chat_send('Tag:' + self.version, team_only=False)

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
                    print('reading data/overlords.txt')
                    pl = open(os.path.join('data','overlords.txt'),'r')
                    lines = pl.read().splitlines()
                    pl.close()
                    for line in lines:
                        #print(line) # debug
                        words = line.split()
                        if len(words) > 0:
                            if (words[0] == mapname) and (words[1] == startx) and (words[2] == starty):
                                self.overlords.add((float(words[3]), float(words[4]), float(words[5]), float(words[6])))
                    if len(self.overlords) == 0:
                        self.overlords.add((0, 0, self.enemymain.x, self.enemymain.y))
                        print('append to data/overlords.txt:')
                        print(mapname + ' ' + startx + ' ' + starty + ' 0 0 '+str(self.enemymain.x) + ' ' + str(self.enemymain.y))
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



