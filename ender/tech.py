# tech.py, Ender

from ender.common import Common
from ender.utils.unit_creation_utils import unit_created_from
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


class Tech(Common):

    __did_step0 = False
    tech_chains = []  # We can make a thing only if the things before it are finished.
    # Direct creator self.tech_chains are omitted.
    creator = {}  # per unittype the unit making it.
    morph = {}  # morph[UnitTypeId.RAVAGER] = UnitTypeId.ROACH
    # morph[UnitTypeId.OVERSEER] = UnitTypeId.OVERLORD
    # morph[UnitTypeId.OVERLORDTRANSPORT] = UnitTypeId.OVERLORD
    # larva morphs are omitted
    ind_upgrade_use = {}  # the unittype that benefits from this upgrade most.
    speed = {}  # in griddist/sec
    supply_of_unittype = {}  # total supply e.g. ravager 3

    def __step0(self):
        self.tech_chains.append(
            [
                UpgradeId.ZERGMISSILEWEAPONSLEVEL1,
                UpgradeId.ZERGMISSILEWEAPONSLEVEL2,
                UpgradeId.ZERGMISSILEWEAPONSLEVEL3,
            ]
        )
        self.tech_chains.append([UnitTypeId.LAIR, UpgradeId.ZERGMISSILEWEAPONSLEVEL2])
        self.tech_chains.append([UnitTypeId.HIVE, UpgradeId.ZERGMISSILEWEAPONSLEVEL3])
        self.tech_chains.append(
            [UpgradeId.ZERGMELEEWEAPONSLEVEL1, UpgradeId.ZERGMELEEWEAPONSLEVEL2, UpgradeId.ZERGMELEEWEAPONSLEVEL3]
        )
        self.tech_chains.append([UnitTypeId.LAIR, UpgradeId.ZERGMELEEWEAPONSLEVEL2])
        self.tech_chains.append([UnitTypeId.HIVE, UpgradeId.ZERGMELEEWEAPONSLEVEL3])
        self.tech_chains.append(
            [UpgradeId.ZERGGROUNDARMORSLEVEL1, UpgradeId.ZERGGROUNDARMORSLEVEL2, UpgradeId.ZERGGROUNDARMORSLEVEL3]
        )
        self.tech_chains.append([UnitTypeId.LAIR, UpgradeId.ZERGGROUNDARMORSLEVEL2])
        self.tech_chains.append([UnitTypeId.HIVE, UpgradeId.ZERGGROUNDARMORSLEVEL3])
        self.tech_chains.append([UnitTypeId.HIVE, UpgradeId.ZERGLINGATTACKSPEED])
        self.tech_chains.append(
            [UpgradeId.ZERGFLYERARMORSLEVEL1, UpgradeId.ZERGFLYERARMORSLEVEL2, UpgradeId.ZERGFLYERARMORSLEVEL3]
        )
        self.tech_chains.append([UnitTypeId.LAIR, UpgradeId.ZERGFLYERARMORSLEVEL2])
        self.tech_chains.append([UnitTypeId.HIVE, UpgradeId.ZERGFLYERARMORSLEVEL3])
        self.tech_chains.append(
            [UpgradeId.ZERGFLYERWEAPONSLEVEL1, UpgradeId.ZERGFLYERWEAPONSLEVEL2, UpgradeId.ZERGFLYERWEAPONSLEVEL3]
        )
        self.tech_chains.append([UnitTypeId.LAIR, UpgradeId.ZERGFLYERWEAPONSLEVEL2])
        self.tech_chains.append([UnitTypeId.HIVE, UpgradeId.ZERGFLYERWEAPONSLEVEL3])
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
        self.tech_chains.append(
            [
                UnitTypeId.LAIR,
                UnitTypeId.INFESTATIONPIT,
                UnitTypeId.HIVE,
                UnitTypeId.ULTRALISKCAVERN,
                UnitTypeId.ULTRALISK,
            ]
        )
        self.tech_chains.append([UnitTypeId.HYDRALISKDEN, UnitTypeId.LURKERDENMP, UnitTypeId.LURKERMP])
        self.tech_chains.append([UnitTypeId.LAIR, UnitTypeId.NYDUSNETWORK])
        self.tech_chains.append(
            [UnitTypeId.HATCHERY, UnitTypeId.SPAWNINGPOOL, UnitTypeId.ROACHWARREN, UnitTypeId.ROACH]
        )
        self.tech_chains.append([UnitTypeId.SPAWNINGPOOL, UnitTypeId.LAIR, UnitTypeId.SPIRE, UnitTypeId.CORRUPTOR])
        self.tech_chains.append([UnitTypeId.INFESTATIONPIT, UnitTypeId.INFESTOR])
        self.tech_chains.append([UnitTypeId.SPIRE, UnitTypeId.MUTALISK])
        self.tech_chains.append([UnitTypeId.INFESTATIONPIT, UnitTypeId.SWARMHOSTMP])
        self.tech_chains.append([UnitTypeId.HIVE, UnitTypeId.VIPER])
        self.tech_chains.append([UnitTypeId.SPAWNINGPOOL, UnitTypeId.ZERGLING])
        self.tech_chains.append([UnitTypeId.LAIR, UnitTypeId.OVERLORDTRANSPORT])
        self.tech_chains.append([UnitTypeId.LAIR, UnitTypeId.OVERSEER])
        self.tech_chains.append([UnitTypeId.HATCHERY, UnitTypeId.RAVAGER])
        # morph is used for counting zerglings
        # morph is also used for disappearing creators
        # both sides are units (not larvae, eggs or cocoons).
        # cannot administrate here that a burrowed lurker counts as a lurker
        self.morph[UnitTypeId.RAVAGER] = UnitTypeId.ROACH
        self.morph[UnitTypeId.BROODLORD] = UnitTypeId.CORRUPTOR
        self.morph[UnitTypeId.BANELING] = UnitTypeId.ZERGLING
        self.morph[UnitTypeId.LURKERMP] = UnitTypeId.HYDRALISK
        self.morph[UnitTypeId.OVERSEER] = UnitTypeId.OVERLORD
        self.morph[UnitTypeId.OVERLORDTRANSPORT] = UnitTypeId.OVERLORD
        self.morph[UnitTypeId.OBSERVERSIEGEMODE] = UnitTypeId.OVERLORD
        for unt in self.all_burrowtypes:  # e.g. banelingburrowed
            crea = unit_created_from[unt]  # e.g. baneling
            if crea in self.morph:
                crea = self.morph[crea]  # e.g. zergling
            self.morph[unt] = crea
        #
        self.ind_upgrade_use[UpgradeId.OVERLORDSPEED] = UnitTypeId.OVERSEER
        self.ind_upgrade_use[UpgradeId.BURROW] = UnitTypeId.ROACH
        self.ind_upgrade_use[UpgradeId.ZERGLINGMOVEMENTSPEED] = UnitTypeId.ZERGLING
        self.ind_upgrade_use[UpgradeId.ZERGLINGATTACKSPEED] = UnitTypeId.ZERGLING
        self.ind_upgrade_use[UpgradeId.CHITINOUSPLATING] = UnitTypeId.ULTRALISK
        self.ind_upgrade_use[UpgradeId.LURKERRANGE] = UnitTypeId.LURKERMP
        self.ind_upgrade_use[UpgradeId.CENTRIFICALHOOKS] = UnitTypeId.BANELING
        self.ind_upgrade_use[UpgradeId.EVOLVEGROOVEDSPINES] = UnitTypeId.LURKERMP
        self.ind_upgrade_use[UpgradeId.EVOLVEMUSCULARAUGMENTS] = UnitTypeId.HYDRALISK
        self.ind_upgrade_use[UpgradeId.NEURALPARASITE] = UnitTypeId.INFESTOR
        self.ind_upgrade_use[UpgradeId.GLIALRECONSTITUTION] = UnitTypeId.ROACH
        #
        self.supply_of_unittype[UnitTypeId.CHANGELING] = 0
        self.supply_of_unittype[UnitTypeId.CHANGELINGMARINE] = 0
        self.supply_of_unittype[UnitTypeId.CHANGELINGMARINESHIELD] = 0
        self.supply_of_unittype[UnitTypeId.CHANGELINGZEALOT] = 0
        self.supply_of_unittype[UnitTypeId.CHANGELINGZERGLING] = 0
        self.supply_of_unittype[UnitTypeId.CHANGELINGZERGLINGWINGS] = 0
        self.supply_of_unittype[UnitTypeId.QUEEN] = 2
        self.supply_of_unittype[UnitTypeId.ROACH] = 2
        self.supply_of_unittype[UnitTypeId.MUTALISK] = 2
        self.supply_of_unittype[UnitTypeId.ZERGLING] = 0.5
        self.supply_of_unittype[UnitTypeId.OVERSEER] = 0
        self.supply_of_unittype[UnitTypeId.CORRUPTOR] = 2
        self.supply_of_unittype[UnitTypeId.BROODLORD] = 4
        self.supply_of_unittype[UnitTypeId.INFESTOR] = 2
        self.supply_of_unittype[UnitTypeId.BROODLING] = 0
        self.supply_of_unittype[UnitTypeId.HYDRALISK] = 2
        self.supply_of_unittype[UnitTypeId.LURKERMP] = 3
        self.supply_of_unittype[UnitTypeId.OVERLORDTRANSPORT] = 0
        self.supply_of_unittype[UnitTypeId.VIPER] = 3
        self.supply_of_unittype[UnitTypeId.BANELING] = 0.5
        self.supply_of_unittype[UnitTypeId.ULTRALISK] = 6
        self.supply_of_unittype[UnitTypeId.LOCUSTMP] = 0
        self.supply_of_unittype[UnitTypeId.LOCUSTMPFLYING] = 0
        self.supply_of_unittype[UnitTypeId.OVERSEERSIEGEMODE] = 0
        self.supply_of_unittype[UnitTypeId.RAVAGER] = 0
        self.supply_of_unittype[UnitTypeId.SWARMHOSTMP] = 3
        self.supply_of_unittype[UnitTypeId.LURKERMPBURROWED] = 3
        self.supply_of_unittype[UnitTypeId.ZERGLINGBURROWED] = 0.5
        self.supply_of_unittype[UnitTypeId.BANELINGBURROWED] = 0.5
        self.supply_of_unittype[UnitTypeId.ULTRALISKBURROWED] = 6
        self.supply_of_unittype[UnitTypeId.DRONEBURROWED] = 1
        self.supply_of_unittype[UnitTypeId.HYDRALISKBURROWED] = 2
        self.supply_of_unittype[UnitTypeId.INFESTORBURROWED] = 2
        self.supply_of_unittype[UnitTypeId.QUEENBURROWED] = 2
        self.supply_of_unittype[UnitTypeId.RAVAGERBURROWED] = 3
        self.supply_of_unittype[UnitTypeId.SWARMHOSTBURROWEDMP] = 3
        self.supply_of_unittype[UnitTypeId.EGG] = 2  # can have other values
        self.supply_of_unittype[UnitTypeId.BROODLORDCOCOON] = 4
        self.supply_of_unittype[UnitTypeId.RAVAGERCOCOON] = 3
        self.supply_of_unittype[UnitTypeId.BANELINGCOCOON] = 0.5
        self.supply_of_unittype[UnitTypeId.TRANSPORTOVERLORDCOCOON] = 0
        self.supply_of_unittype[UnitTypeId.OVERLORDCOCOON] = 0
        self.supply_of_unittype[UnitTypeId.LURKERMPEGG] = 3
        self.supply_of_unittype[UnitTypeId.DRONE] = 1
        self.supply_of_unittype[UnitTypeId.LARVA] = 0
        self.supply_of_unittype[UnitTypeId.OVERLORD] = 0
        #
        # speed values copied from Liquipedia, dist per second
        self.speed[UnitTypeId.LARVA] = 0.79
        self.speed[UnitTypeId.OVERLORD] = 0.902
        self.speed[UnitTypeId.OVERLORDTRANSPORT] = 0.902
        self.speed[UnitTypeId.QUEEN] = 1.31
        self.speed[UnitTypeId.SPINECRAWLER] = 1.4
        self.speed[UnitTypeId.SPORECRAWLER] = 1.4
        self.speed[UnitTypeId.BROODLORD] = 1.97
        self.speed[UnitTypeId.LOCUSTMP] = 2.62
        self.speed[UnitTypeId.LOCUSTMPFLYING] = 2.62
        self.speed[UnitTypeId.OVERSEER] = 2.62
        self.speed[UnitTypeId.ROACH] = 3.15
        self.speed[UnitTypeId.HYDRALISK] = 3.15
        self.speed[UnitTypeId.INFESTOR] = 3.15
        self.speed[UnitTypeId.SWARMHOSTMP] = 3.15
        for typ in self.all_changelings:
            self.speed[typ] = 3.15
        self.speed[UnitTypeId.CHANGELINGZERGLING] = 4.13
        self.speed[UnitTypeId.CHANGELINGZERGLINGWINGS] = 4.13
        self.speed[UnitTypeId.BANELING] = 3.5
        self.speed[UnitTypeId.RAVAGER] = 3.85
        self.speed[UnitTypeId.DRONE] = 3.94
        self.speed[UnitTypeId.ZERGLING] = 4.13
        self.speed[UnitTypeId.LURKERMP] = 4.13
        self.speed[UnitTypeId.ULTRALISK] = 4.13
        self.speed[UnitTypeId.VIPER] = 4.13
        self.speed[UnitTypeId.CORRUPTOR] = 4.725
        self.speed[UnitTypeId.BROODLING] = 5.37
        self.speed[UnitTypeId.MUTALISK] = 5.6

    def correct_speed(self):
        # speed corrections on upgrades, from Liquipedia
        if UpgradeId.OVERLORDSPEED in self.state.upgrades:
            self.speed[UnitTypeId.OVERLORD] = 2.63
            self.speed[UnitTypeId.OVERLORDTRANSPORT] = 2.63
            self.speed[UnitTypeId.OVERSEER] = 4.72
        if UpgradeId.ZERGLINGMOVEMENTSPEED in self.state.upgrades:
            self.speed[UnitTypeId.ZERGLING] = 6.58
        if UpgradeId.CENTRIFICALHOOKS in self.state.upgrades:
            self.speed[UnitTypeId.BANELING] = 4.13
        if UpgradeId.EVOLVEMUSCULARAUGMENTS in self.state.upgrades:
            self.speed[UnitTypeId.HYDRALISK] = 3.93
        if UpgradeId.GLIALRECONSTITUTION in self.state.upgrades:
            self.speed[UnitTypeId.ROACH] = 4.2

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        if not self.did_tech_onstep:
            self.did_tech_onstep = True

    # utility
    def worth(self, typ: UnitTypeId) -> float:
        worth = 0
        if typ in self.game_data.units:
            cost = self.game_data.units[typ].cost
            worth = cost.minerals + 1.6875 * cost.vespene
        return worth
