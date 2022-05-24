# tech.py, Ender
# 23 may 2022

from ender.common import Common
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.unit_typeid import UnitTypeId


class Tech(Common):

    __did_step0 = False
    tech_chains = [] # We can make a thing only if the things before it are finished.
                     # Direct creator self.tech_chains are omitted.

    def __step0(self):
        self.tech_chains.append([UpgradeId.ZERGMISSILEWEAPONSLEVEL1, 
                                UnitTypeId.LAIR,
                                UpgradeId.ZERGMISSILEWEAPONSLEVEL2, UnitTypeId.HIVE,
                                UpgradeId.ZERGMISSILEWEAPONSLEVEL3])
        self.tech_chains.append([UpgradeId.ZERGMELEEWEAPONSLEVEL1,
                                UnitTypeId.LAIR,
                                UpgradeId.ZERGMELEEWEAPONSLEVEL2,
                                UnitTypeId.HIVE,
                                UpgradeId.ZERGMELEEWEAPONSLEVEL3])
        self.tech_chains.append([UpgradeId.ZERGGROUNDARMORSLEVEL1, UnitTypeId.LAIR,
                                UpgradeId.ZERGGROUNDARMORSLEVEL2, UnitTypeId.HIVE,
                                UpgradeId.ZERGGROUNDARMORSLEVEL3])
        self.tech_chains.append([UnitTypeId.HIVE, UpgradeId.ZERGLINGATTACKSPEED])
        self.tech_chains.append([UpgradeId.ZERGFLYERARMORSLEVEL1, UnitTypeId.LAIR,
                                UpgradeId.ZERGFLYERARMORSLEVEL2, UnitTypeId.HIVE,
                                UpgradeId.ZERGFLYERARMORSLEVEL3])
        self.tech_chains.append([UpgradeId.ZERGFLYERWEAPONSLEVEL1, UnitTypeId.LAIR,
                                UpgradeId.ZERGFLYERWEAPONSLEVEL2, UnitTypeId.HIVE,
                                UpgradeId.ZERGFLYERWEAPONSLEVEL3])
        self.tech_chains.append([UnitTypeId.LAIR, UpgradeId.LURKERRANGE])
        self.tech_chains.append([UnitTypeId.LAIR, UpgradeId.CENTRIFICALHOOKS])
        self.tech_chains.append([UnitTypeId.LAIR, UpgradeId.GLIALRECONSTITUTION])
        # self.tech_chains units and buildings
        self.tech_chains.append([UnitTypeId.HIVE, UnitTypeId.GREATERSPIRE, UnitTypeId.BROODLORD])
        self.tech_chains.append([UnitTypeId.SPAWNINGPOOL, UnitTypeId.QUEEN])
        self.tech_chains.append([UnitTypeId.SPAWNINGPOOL, UnitTypeId.SPINECRAWLER])
        self.tech_chains.append([UnitTypeId.SPAWNINGPOOL, UnitTypeId.SPORECRAWLER])
        self.tech_chains.append([UnitTypeId.SPAWNINGPOOL, UnitTypeId.BANELINGNEST, UnitTypeId.BANELING])
        self.tech_chains.append([UnitTypeId.HATCHERY, UnitTypeId.EVOLUTIONCHAMBER])
        self.tech_chains.append([UnitTypeId.LAIR, UnitTypeId.HYDRALISKDEN, UnitTypeId.HYDRALISK])
        self.tech_chains.append([UnitTypeId.LAIR, UnitTypeId.INFESTATIONPIT, UnitTypeId.HIVE,
                                UnitTypeId.ULTRALISKCAVERN, UnitTypeId.ULTRALISK])
        self.tech_chains.append([UnitTypeId.HYDRALISKDEN, UnitTypeId.LURKERDENMP, UnitTypeId.LURKERMP])
        self.tech_chains.append([UnitTypeId.LAIR, UnitTypeId.NYDUSNETWORK])
        self.tech_chains.append([UnitTypeId.HATCHERY, UnitTypeId.SPAWNINGPOOL, UnitTypeId.ROACHWARREN, UnitTypeId.ROACH])
        self.tech_chains.append([UnitTypeId.SPAWNINGPOOL, UnitTypeId.LAIR, UnitTypeId.SPIRE, UnitTypeId.CORRUPTOR])
        self.tech_chains.append([UnitTypeId.INFESTATIONPIT, UnitTypeId.INFESTOR])
        self.tech_chains.append([UnitTypeId.SPIRE, UnitTypeId.MUTALISK])
        self.tech_chains.append([UnitTypeId.INFESTATIONPIT, UnitTypeId.SWARMHOSTMP])
        self.tech_chains.append([UnitTypeId.HIVE, UnitTypeId.VIPER])
        self.tech_chains.append([UnitTypeId.SPAWNINGPOOL, UnitTypeId.ZERGLING])
        self.tech_chains.append([UnitTypeId.LAIR, UnitTypeId.OVERLORDTRANSPORT])
        self.tech_chains.append([UnitTypeId.LAIR, UnitTypeId.OVERSEER])
        self.tech_chains.append([UnitTypeId.HATCHERY, UnitTypeId.RAVAGER])

    async def on_step(self):
        await Common.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
