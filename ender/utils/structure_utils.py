from enum import Enum, auto

from sc2.ids.unit_typeid import UnitTypeId


# Fails to figure out races from sc2 race
class Race(Enum):
    Protoss = (auto(),)
    Terran = (auto(),)
    Zerg = (auto(),)


gas_extraction_structures = [
    UnitTypeId.REFINERY,
    UnitTypeId.REFINERYRICH,
    UnitTypeId.EXTRACTOR,
    UnitTypeId.EXTRACTORRICH,
    UnitTypeId.ASSIMILATOR,
    UnitTypeId.ASSIMILATORRICH,
]
structure_creation_duration: dict[UnitTypeId, int] = {}
structure_race: dict[UnitTypeId, Race] = {}
structure_radius: dict[UnitTypeId, int] = {}


def _init_structures(structure: UnitTypeId, race: Race, duration: int, radius: int):
    structure_creation_duration[structure] = duration
    structure_race[structure] = race
    structure_radius[structure] = radius


_init_structures(UnitTypeId.SUPPLYDEPOT, Race.Terran, 21, 2)
_init_structures(UnitTypeId.SUPPLYDEPOTLOWERED, Race.Terran, 21, 2)
_init_structures(UnitTypeId.BARRACKS, Race.Terran, 46, 3)
_init_structures(UnitTypeId.BARRACKSFLYING, Race.Terran, 46, 3)
_init_structures(UnitTypeId.REFINERY, Race.Terran, 21, 3)
_init_structures(UnitTypeId.REFINERYRICH, Race.Terran, 21, 3)
_init_structures(UnitTypeId.BARRACKSTECHLAB, Race.Terran, 18, 2)
_init_structures(UnitTypeId.FACTORY, Race.Terran, 43, 3)
_init_structures(UnitTypeId.FACTORYFLYING, Race.Terran, 43, 3)
_init_structures(UnitTypeId.FACTORYTECHLAB, Race.Terran, 18, 2)
_init_structures(UnitTypeId.STARPORT, Race.Terran, 36, 3)
_init_structures(UnitTypeId.STARPORTFLYING, Race.Terran, 36, 3)
_init_structures(UnitTypeId.STARPORTTECHLAB, Race.Terran, 18, 2)
_init_structures(UnitTypeId.TECHLAB, Race.Terran, 18, 2)
_init_structures(UnitTypeId.FUSIONCORE, Race.Terran, 46, 3)
_init_structures(UnitTypeId.COMMANDCENTER, Race.Terran, 71, 5)
_init_structures(UnitTypeId.COMMANDCENTERFLYING, Race.Terran, 71, 5)
_init_structures(UnitTypeId.PLANETARYFORTRESS, Race.Terran, 36, 5)
_init_structures(UnitTypeId.ORBITALCOMMAND, Race.Terran, 25, 5)
_init_structures(UnitTypeId.ORBITALCOMMANDFLYING, Race.Terran, 25, 5)
_init_structures(UnitTypeId.ENGINEERINGBAY, Race.Terran, 25, 3)
_init_structures(UnitTypeId.MISSILETURRET, Race.Terran, 18, 2)
_init_structures(UnitTypeId.ARMORY, Race.Terran, 46, 3)
_init_structures(UnitTypeId.BUNKER, Race.Terran, 29, 3)
_init_structures(UnitTypeId.SENSORTOWER, Race.Terran, 18, 2)
_init_structures(UnitTypeId.GHOSTACADEMY, Race.Terran, 20, 3)
_init_structures(UnitTypeId.BARRACKSREACTOR, Race.Terran, 36, 2)
_init_structures(UnitTypeId.FACTORYREACTOR, Race.Terran, 36, 2)
_init_structures(UnitTypeId.STARPORTREACTOR, Race.Terran, 36, 2)
_init_structures(UnitTypeId.REACTOR, Race.Terran, 36, 2)
_init_structures(UnitTypeId.AUTOTURRET, Race.Terran, 0, 2)
# protoss
_init_structures(UnitTypeId.NEXUS, Race.Protoss, 71, 5)
_init_structures(UnitTypeId.PYLON, Race.Protoss, 18, 2)
_init_structures(UnitTypeId.ASSIMILATOR, Race.Protoss, 21, 3)
_init_structures(UnitTypeId.ASSIMILATORRICH, Race.Protoss, 21, 3)
_init_structures(UnitTypeId.GATEWAY, Race.Protoss, 46, 3)
_init_structures(UnitTypeId.FORGE, Race.Protoss, 32, 3)
_init_structures(UnitTypeId.PHOTONCANNON, Race.Protoss, 29, 2)
_init_structures(UnitTypeId.SHIELDBATTERY, Race.Protoss, 29, 2)
_init_structures(UnitTypeId.WARPGATE, Race.Protoss, 7, 3)
_init_structures(UnitTypeId.CYBERNETICSCORE, Race.Protoss, 36, 3)
_init_structures(UnitTypeId.TWILIGHTCOUNCIL, Race.Protoss, 36, 3)
_init_structures(UnitTypeId.ROBOTICSFACILITY, Race.Protoss, 46, 3)
_init_structures(UnitTypeId.STARGATE, Race.Protoss, 43, 3)
_init_structures(UnitTypeId.TEMPLARARCHIVE, Race.Protoss, 36, 3)
_init_structures(UnitTypeId.DARKSHRINE, Race.Protoss, 71, 2)
_init_structures(UnitTypeId.ROBOTICSBAY, Race.Protoss, 46, 3)
_init_structures(UnitTypeId.FLEETBEACON, Race.Protoss, 43, 3)
_init_structures(UnitTypeId.ORACLESTASISTRAP, Race.Protoss, 11, 1)
# zerg
_init_structures(UnitTypeId.HATCHERY, Race.Zerg, 71, 5)
_init_structures(UnitTypeId.LAIR, Race.Zerg, 57, 5)
_init_structures(UnitTypeId.HIVE, Race.Zerg, 71, 5)
_init_structures(UnitTypeId.EXTRACTOR, Race.Zerg, 21, 3)
_init_structures(UnitTypeId.EXTRACTORRICH, Race.Zerg, 21, 3)
_init_structures(UnitTypeId.SPAWNINGPOOL, Race.Zerg, 46, 3)
_init_structures(UnitTypeId.SPINECRAWLER, Race.Zerg, 36, 2)
_init_structures(UnitTypeId.SPORECRAWLER, Race.Zerg, 21, 2)
_init_structures(UnitTypeId.SPINECRAWLERUPROOTED, Race.Zerg, 36, 2)
_init_structures(UnitTypeId.SPORECRAWLERUPROOTED, Race.Zerg, 21, 2)
_init_structures(UnitTypeId.EVOLUTIONCHAMBER, Race.Zerg, 25, 3)
_init_structures(UnitTypeId.ROACHWARREN, Race.Zerg, 39, 3)
_init_structures(UnitTypeId.BANELINGNEST, Race.Zerg, 43, 3)
_init_structures(UnitTypeId.HYDRALISKDEN, Race.Zerg, 29, 3)
_init_structures(UnitTypeId.LURKERDENMP, Race.Zerg, 57, 3)
_init_structures(UnitTypeId.SPIRE, Race.Zerg, 71, 3)
_init_structures(UnitTypeId.GREATERSPIRE, Race.Zerg, 71, 3)
_init_structures(UnitTypeId.NYDUSNETWORK, Race.Zerg, 36, 3)
_init_structures(UnitTypeId.NYDUSCANAL, Race.Zerg, 14, 3)
_init_structures(UnitTypeId.INFESTATIONPIT, Race.Zerg, 36, 3)
_init_structures(UnitTypeId.ULTRALISKCAVERN, Race.Zerg, 46, 3)
_init_structures(UnitTypeId.CREEPTUMOR, Race.Zerg, 11, 1)
_init_structures(UnitTypeId.CREEPTUMORBURROWED, Race.Zerg, 11, 1)
_init_structures(UnitTypeId.CREEPTUMORQUEEN, Race.Zerg, 11, 1)
