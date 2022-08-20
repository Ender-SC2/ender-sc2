from typing import Dict, List

from ender.cache.cache_entry import CacheEntry, UnitInfo
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId


class EnemyCache:
    """
    Tracks recently seen enemy units and structures
    """
    cache: Dict[int, CacheEntry]

    def __init__(self):
        self.cache = {}

    '''
    Mutable, update positions, type and refresh timeout
    '''
    def update(self, bot_ai: BotAI):
        self.cache = {key: value for key, value in self.cache.items() if value.last_seen > bot_ai.time - 30}
        for unit in bot_ai.enemy_units:
            self.cache[unit.tag] = CacheEntry(unit_info=UnitInfo(unit_type=unit.type_id, position=unit.position),
                                              last_seen=bot_ai.time)
        for structure in bot_ai.enemy_structures:
            self.cache[structure.tag] = CacheEntry(
                unit_info=UnitInfo(unit_type=structure.type_id, position=structure.position), last_seen=bot_ai.time)

    '''
    Mutable, clear killed enemies
    '''
    def unit_destroyed(self, unit_tag: int):
        if unit_tag in self.cache:
            self.cache.pop(unit_tag)

    def of_type(self, unit_type: UnitTypeId) -> List[UnitInfo]:
        return [entry.unit_info for entry in self.cache.values() if entry.unit_info.unit_type == unit_type]
