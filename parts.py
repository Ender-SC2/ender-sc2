# parts.py, Merkbot, Zerg sandbox bot
# 20 may 2022
from common import Common
import sc2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.buff_id import BuffId
from sc2.position import Point2
from enum import Enum
from math import sqrt,cos,sin,pi,acos
import random

class Parts(Common):

    __did_step0 = False
    #

    def __step0(self):
        self.init_all_structures()

    async def on_step(self):
        await Common.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
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
