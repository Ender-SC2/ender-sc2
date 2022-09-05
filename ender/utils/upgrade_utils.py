from typing import List, Dict, Optional

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

upgrade_research_at: Dict[UpgradeId, List[UnitTypeId]] = {}
upgrade_requirement_buildings: Dict[UpgradeId, List[UnitTypeId]] = {}
upgrade_requirement_upgrades: Dict[UpgradeId, UpgradeId] = {}


def _init_upgrade(
    upgrade: UpgradeId,
    research_at: List[UnitTypeId],
    requirement_buildings: List[UnitTypeId],
    requirement_upgrade: Optional[UpgradeId],
):
    upgrade_research_at[upgrade] = research_at
    upgrade_requirement_buildings[upgrade] = requirement_buildings
    if requirement_upgrade:
        upgrade_requirement_upgrades[upgrade] = requirement_upgrade


_init_upgrade(UpgradeId.BURROW, [UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE], [], None)
_init_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED, [UnitTypeId.SPAWNINGPOOL], [UnitTypeId.LAIR, UnitTypeId.HIVE], None)
_init_upgrade(UpgradeId.TUNNELINGCLAWS, [UnitTypeId.ROACHWARREN], [UnitTypeId.LAIR, UnitTypeId.HIVE], None)
_init_upgrade(
    UpgradeId.ZERGMELEEWEAPONSLEVEL1,
    [UnitTypeId.EVOLUTIONCHAMBER],
    [UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE],
    None,
)
_init_upgrade(
    UpgradeId.ZERGMISSILEWEAPONSLEVEL1,
    [UnitTypeId.EVOLUTIONCHAMBER],
    [UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE],
    None,
)
_init_upgrade(
    UpgradeId.ZERGGROUNDARMORSLEVEL1,
    [UnitTypeId.EVOLUTIONCHAMBER],
    [UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE],
    None,
)
_init_upgrade(
    UpgradeId.ZERGMELEEWEAPONSLEVEL2,
    [UnitTypeId.EVOLUTIONCHAMBER],
    [UnitTypeId.LAIR, UnitTypeId.HIVE],
    UpgradeId.ZERGMELEEWEAPONSLEVEL1,
)
_init_upgrade(
    UpgradeId.ZERGMISSILEWEAPONSLEVEL2,
    [UnitTypeId.EVOLUTIONCHAMBER],
    [UnitTypeId.LAIR, UnitTypeId.HIVE],
    UpgradeId.ZERGMISSILEWEAPONSLEVEL1,
)
_init_upgrade(
    UpgradeId.ZERGGROUNDARMORSLEVEL2,
    [UnitTypeId.EVOLUTIONCHAMBER],
    [UnitTypeId.LAIR, UnitTypeId.HIVE],
    UpgradeId.ZERGGROUNDARMORSLEVEL1,
)
_init_upgrade(
    UpgradeId.ZERGMELEEWEAPONSLEVEL3,
    [UnitTypeId.EVOLUTIONCHAMBER],
    [UnitTypeId.HIVE],
    UpgradeId.ZERGMELEEWEAPONSLEVEL2,
)
_init_upgrade(
    UpgradeId.ZERGMISSILEWEAPONSLEVEL3,
    [UnitTypeId.EVOLUTIONCHAMBER],
    [UnitTypeId.HIVE],
    UpgradeId.ZERGMISSILEWEAPONSLEVEL2,
)
_init_upgrade(
    UpgradeId.ZERGGROUNDARMORSLEVEL3,
    [UnitTypeId.EVOLUTIONCHAMBER],
    [UnitTypeId.HIVE],
    UpgradeId.ZERGGROUNDARMORSLEVEL2,
)
