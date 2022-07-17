# tech.py, Ender

from ender.common import Common
import sc2
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.unit_typeid import UnitTypeId


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
        #
        # creator
        for martype in sc2.dicts.unit_trained_from.UNIT_TRAINED_FROM:
            apiset = sc2.dicts.unit_trained_from.UNIT_TRAINED_FROM[martype]
            if len(apiset) == 1:
                api = list(apiset)[0]
                self.creator[martype] = api
        for martype in sc2.dicts.upgrade_researched_from.UPGRADE_RESEARCHED_FROM:
            api = sc2.dicts.upgrade_researched_from.UPGRADE_RESEARCHED_FROM[martype]
            self.creator[martype] = api
        for unt in self.all_changelings:
            if unt != UnitTypeId.CHANGELING:
                self.creator[unt] = UnitTypeId.CHANGELING
        self.creator[UnitTypeId.LURKERMPBURROWED] = UnitTypeId.LURKERMP
        self.creator[UnitTypeId.ULTRALISKBURROWED] = UnitTypeId.ULTRALISK
        self.creator[UnitTypeId.DRONEBURROWED] = UnitTypeId.DRONE
        self.creator[UnitTypeId.CHANGELING] = UnitTypeId.OVERSEER
        self.creator[UnitTypeId.CREEPTUMOR] = UnitTypeId.CREEPTUMORBURROWED
        self.creator[UnitTypeId.CREEPTUMORBURROWED] = UnitTypeId.CREEPTUMOR
        self.creator[UnitTypeId.QUEEN] = UnitTypeId.HATCHERY  # also lair etc
        self.creator[UnitTypeId.OVERSEER] = UnitTypeId.OVERLORD
        self.creator[UnitTypeId.OVERLORDTRANSPORT] = UnitTypeId.OVERLORD
        self.creator[UnitTypeId.OVERSEERSIEGEMODE] = UnitTypeId.OVERSEER
        self.creator[UnitTypeId.QUEENBURROWED] = UnitTypeId.QUEEN
        self.creator[UnitTypeId.RAVAGERBURROWED] = UnitTypeId.RAVAGER
        self.creator[UnitTypeId.ROACHBURROWED] = UnitTypeId.ROACH
        self.creator[UnitTypeId.SPINECRAWLERUPROOTED] = UnitTypeId.SPINECRAWLER
        self.creator[UnitTypeId.SPORECRAWLERUPROOTED] = UnitTypeId.SPORECRAWLER
        self.creator[UnitTypeId.SWARMHOSTBURROWEDMP] = UnitTypeId.SWARMHOSTMP
        self.creator[UnitTypeId.LOCUSTMPFLYING] = UnitTypeId.SWARMHOSTMP
        self.creator[UnitTypeId.ULTRALISKBURROWED] = UnitTypeId.ULTRALISK
        self.creator[UnitTypeId.ZERGLINGBURROWED] = UnitTypeId.ZERGLING
        self.creator[UnitTypeId.BANELINGBURROWED] = UnitTypeId.BANELING
        self.creator[UnitTypeId.HYDRALISKBURROWED] = UnitTypeId.HYDRALISK
        self.creator[UnitTypeId.INFESTORBURROWED] = UnitTypeId.INFESTOR
        self.creator[UnitTypeId.LOCUSTMP] = UnitTypeId.LOCUSTMPFLYING
        self.creator[UnitTypeId.EGG] = UnitTypeId.LARVA
        self.creator[UnitTypeId.EXTRACTORRICH] = UnitTypeId.DRONE
        self.creator[UnitTypeId.LARVA] = UnitTypeId.HATCHERY
        self.creator[UnitTypeId.BROODLING] = UnitTypeId.BROODLORD
        #
        # list of structures, with species, builddura, size. Can be flying, can be lowered.
        # terran
        self.init_structures("T", UnitTypeId.SUPPLYDEPOT, 21, 2)
        self.init_structures("T", UnitTypeId.SUPPLYDEPOTLOWERED, 21, 2)
        self.init_structures("T", UnitTypeId.BARRACKS, 46, 3)
        self.init_structures("T", UnitTypeId.BARRACKSFLYING, 46, 3)
        self.init_structures("T", UnitTypeId.REFINERY, 21, 3)
        self.init_structures("T", UnitTypeId.REFINERYRICH, 21, 3)
        self.init_structures("T", UnitTypeId.BARRACKSTECHLAB, 18, 2)
        self.init_structures("T", UnitTypeId.FACTORY, 43, 3)
        self.init_structures("T", UnitTypeId.FACTORYFLYING, 43, 3)
        self.init_structures("T", UnitTypeId.FACTORYTECHLAB, 18, 2)
        self.init_structures("T", UnitTypeId.STARPORT, 36, 3)
        self.init_structures("T", UnitTypeId.STARPORTFLYING, 36, 3)
        self.init_structures("T", UnitTypeId.STARPORTTECHLAB, 18, 2)
        self.init_structures("T", UnitTypeId.TECHLAB, 18, 2)
        self.init_structures("T", UnitTypeId.FUSIONCORE, 46, 3)
        self.init_structures("T", UnitTypeId.COMMANDCENTER, 71, 5)
        self.init_structures("T", UnitTypeId.COMMANDCENTERFLYING, 71, 5)
        self.init_structures("T", UnitTypeId.PLANETARYFORTRESS, 36, 5)
        self.init_structures("T", UnitTypeId.ORBITALCOMMAND, 25, 5)
        self.init_structures("T", UnitTypeId.ORBITALCOMMANDFLYING, 25, 5)
        self.init_structures("T", UnitTypeId.ENGINEERINGBAY, 25, 3)
        self.init_structures("T", UnitTypeId.MISSILETURRET, 18, 2)
        self.init_structures("T", UnitTypeId.ARMORY, 46, 3)
        self.init_structures("T", UnitTypeId.BUNKER, 29, 3)
        self.init_structures("T", UnitTypeId.SENSORTOWER, 18, 2)
        self.init_structures("T", UnitTypeId.GHOSTACADEMY, 20, 3)
        self.init_structures("T", UnitTypeId.BARRACKSREACTOR, 36, 2)
        self.init_structures("T", UnitTypeId.FACTORYREACTOR, 36, 2)
        self.init_structures("T", UnitTypeId.STARPORTREACTOR, 36, 2)
        self.init_structures("T", UnitTypeId.REACTOR, 36, 2)
        self.init_structures("T", UnitTypeId.AUTOTURRET, 0, 2)
        # protoss
        self.init_structures("P", UnitTypeId.NEXUS, 71, 5)
        self.init_structures("P", UnitTypeId.PYLON, 18, 2)
        self.init_structures("P", UnitTypeId.ASSIMILATOR, 21, 3)
        self.init_structures("P", UnitTypeId.ASSIMILATORRICH, 21, 3)
        self.init_structures("P", UnitTypeId.GATEWAY, 46, 3)
        self.init_structures("P", UnitTypeId.FORGE, 32, 3)
        self.init_structures("P", UnitTypeId.PHOTONCANNON, 29, 2)
        self.init_structures("P", UnitTypeId.SHIELDBATTERY, 29, 2)
        self.init_structures("P", UnitTypeId.WARPGATE, 7, 3)
        self.init_structures("P", UnitTypeId.CYBERNETICSCORE, 36, 3)
        self.init_structures("P", UnitTypeId.TWILIGHTCOUNCIL, 36, 3)
        self.init_structures("P", UnitTypeId.ROBOTICSFACILITY, 46, 3)
        self.init_structures("P", UnitTypeId.STARGATE, 43, 3)
        self.init_structures("P", UnitTypeId.TEMPLARARCHIVE, 36, 3)
        self.init_structures("P", UnitTypeId.DARKSHRINE, 71, 2)
        self.init_structures("P", UnitTypeId.ROBOTICSBAY, 46, 3)
        self.init_structures("P", UnitTypeId.FLEETBEACON, 43, 3)
        self.init_structures("P", UnitTypeId.ORACLESTASISTRAP, 11, 1)
        # zerg
        self.init_structures("Z", UnitTypeId.HATCHERY, 71, 5)
        self.init_structures("Z", UnitTypeId.LAIR, 57, 5)
        self.init_structures("Z", UnitTypeId.HIVE, 71, 5)
        self.init_structures("Z", UnitTypeId.EXTRACTOR, 21, 3)
        self.init_structures("Z", UnitTypeId.EXTRACTORRICH, 21, 3)
        self.init_structures("Z", UnitTypeId.SPAWNINGPOOL, 46, 3)
        self.init_structures("Z", UnitTypeId.SPINECRAWLER, 36, 2)
        self.init_structures("Z", UnitTypeId.SPORECRAWLER, 21, 2)
        self.init_structures("Z", UnitTypeId.SPINECRAWLERUPROOTED, 36, 2)
        self.init_structures("Z", UnitTypeId.SPORECRAWLERUPROOTED, 21, 2)
        self.init_structures("Z", UnitTypeId.EVOLUTIONCHAMBER, 25, 3)
        self.init_structures("Z", UnitTypeId.ROACHWARREN, 39, 3)
        self.init_structures("Z", UnitTypeId.BANELINGNEST, 43, 3)
        self.init_structures("Z", UnitTypeId.HYDRALISKDEN, 29, 3)
        self.init_structures("Z", UnitTypeId.LURKERDENMP, 57, 3)
        self.init_structures("Z", UnitTypeId.SPIRE, 71, 3)
        self.init_structures("Z", UnitTypeId.GREATERSPIRE, 71, 3)
        self.init_structures("Z", UnitTypeId.NYDUSNETWORK, 36, 3)
        self.init_structures("Z", UnitTypeId.NYDUSCANAL, 14, 3)
        self.init_structures("Z", UnitTypeId.INFESTATIONPIT, 36, 3)
        self.init_structures("Z", UnitTypeId.ULTRALISKCAVERN, 46, 3)
        self.init_structures("Z", UnitTypeId.CREEPTUMOR, 11, 1)
        self.init_structures("Z", UnitTypeId.CREEPTUMORBURROWED, 11, 1)
        self.init_structures("Z", UnitTypeId.CREEPTUMORQUEEN, 11, 1)
        #
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
            crea = self.creator[unt]  # e.g. baneling
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

    def init_structures(self, species, barra, builddura, size):
        self.builddura_of_structure[barra] = builddura
        self.size_of_structure[barra] = size
        self.species_of_structure[barra] = species

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        if not self.did_tech_onstep:
            self.did_tech_onstep = True

    # utility
    def worth(self, typ) -> int:
        worth = 0
        if typ not in {UnitTypeId.MULE, UnitTypeId.AUTOTURRET, UnitTypeId.LARVA, UnitTypeId.BROODLING}:
            if typ not in (self.all_eggtypes | self.all_changelings):
                cost = self.calculate_cost(typ)
                worth = 2 * cost.minerals + 3 * cost.vespene
        return worth
