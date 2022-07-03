from typing import Dict

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit


def range_vs(unit: Unit, target: Unit) -> float:
    ground_range = 0
    air_range = 0
    if unit.can_attack_ground and not target.is_flying:
        ground_range = unit.ground_range
    elif unit.can_attack_air and (target.is_flying or target.type_id == UnitTypeId.COLOSSUS):
        air_range = unit.air_range
    return max(ground_range, air_range)


def calculate_combat_value(bot_ai: BotAI, unit: Unit) -> float:
    unit_value = bot_ai.calculate_unit_value(unit.type_id)
    return unit.shield_health_percentage * (unit_value.minerals + unit_value.vespene)

