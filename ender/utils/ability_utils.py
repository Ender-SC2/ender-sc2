from enum import Enum, auto
from typing import Dict, List

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId


class AbilityDamageType(Enum):
    PERSISTENT = auto()
    ON_IMPACT = auto()


# Can an ability be casted by multiple unit types?
ability_caster: Dict[AbilityId, UnitTypeId] = {}
caster_abilities: Dict[UnitTypeId, List[AbilityId]] = {}

ability_range: Dict[AbilityId, float] = {}
ability_cooldown: Dict[AbilityId, float] = {}
ability_radius: Dict[AbilityId, float] = {}
ability_duration: Dict[AbilityId, float] = {}
ability_damage: Dict[AbilityId, float] = {}
ability_damage_type: Dict[AbilityId, AbilityDamageType] = {}


def _init_ability(
    ability: AbilityId,
    caster: UnitTypeId,
    range: float,
    cooldown: float,
    radius: float,
    duration: float,
    damage: float,
    damage_type: AbilityDamageType,
):
    ability_caster[ability] = caster
    ability_range[ability] = range
    ability_cooldown[ability] = cooldown
    ability_radius[ability] = radius
    ability_duration[ability] = duration
    ability_damage[ability] = damage
    ability_damage_type[ability] = damage_type
    if caster not in caster_abilities:
        caster_abilities[caster] = []
    caster_abilities[caster].append(ability)


# TODO: Add more abilities
_init_ability(AbilityId.EFFECT_CORROSIVEBILE, UnitTypeId.RAVAGER, 9, 7, 0.5, 2.5, 60, AbilityDamageType.ON_IMPACT)
_init_ability(
    AbilityId.PSISTORM_PSISTORM, UnitTypeId.HIGHTEMPLAR, 9, 1.25, 1.5, 2.85, 80, AbilityDamageType.PERSISTENT
)
# TODO: Confirm data
_init_ability(AbilityId.HEROARMNUKE_NUKEARM, UnitTypeId.GHOST, 12, 15, 8, 14, 300, AbilityDamageType.ON_IMPACT)
