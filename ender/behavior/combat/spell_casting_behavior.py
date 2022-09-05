# spell_casting_behavior.py
import typing

from ender.map import InfluenceMap
from ender.unit.ability_command import AbilityCommand
from ender.utils.ability_utils import ability_cooldown, ability_range, ability_radius
from ender.utils.command_utils import CommandUtils
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


# TODO: Support other spells;
class SpellCastingBehavior(CommandUtils):
    supported_units: typing.Dict[UnitTypeId, typing.List[AbilityId]] = {
        UnitTypeId.RAVAGER: [AbilityId.EFFECT_CORROSIVEBILE]
    }
    DEFAULT_STRUCTURE_VALUE = 5
    SPECIAL_STRUCTURE_VALUE: typing.Dict[UnitTypeId, int] = {
        UnitTypeId.PHOTONCANNON: 20,
        UnitTypeId.MISSILETURRET: 20,
        UnitTypeId.BUNKER: 20,
        UnitTypeId.SPINECRAWLER: 20,
        UnitTypeId.SPORECRAWLER: 20,
        UnitTypeId.PLANETARYFORTRESS: 20,
        UnitTypeId.SHIELDBATTERY: 20,
        UnitTypeId.PYLON: 10,
    }
    DEFAULT_UNIT_VALUE = 1
    SPECIAL_UNIT_VALUE: typing.Dict[UnitTypeId, int] = {
        UnitTypeId.SIEGETANKSIEGED: 15,
        UnitTypeId.CARRIER: 10,
        UnitTypeId.LIBERATORAG: 10,
        UnitTypeId.MOTHERSHIP: 10,
        UnitTypeId.LURKERMPBURROWED: 10,
    }
    spell_cooldown: typing.Dict[int, float] = {}

    async def on_step_units(self, units: Units):
        my_units = units.filter(
            lambda unit: (unit.type_id in self.supported_units)
            and (unit.tag not in self.spell_cooldown or self.spell_cooldown[unit.tag] < self.bot_ai.time)
        )
        if my_units.empty:
            return
        influence_map = self.create_influence_map()
        if influence_map.max_value() <= 0:
            return

        for unit in my_units:
            tag = unit.tag
            if tag not in self.spell_cooldown:
                self.spell_cooldown[tag] = 0
            for ability in self.supported_units[unit.type_id]:
                target = influence_map.get_best_point(unit.position, ability_range[ability], 0)
                if target:
                    self.spell_cooldown[tag] = self.bot_ai.time + ability_cooldown[ability]
                    self.unit_interface.set_command(unit, AbilityCommand(ability, target, "SpellCasting"))
                    break

    def create_influence_map(self) -> InfluenceMap:
        influence_map = InfluenceMap(ability_radius[AbilityId.EFFECT_CORROSIVEBILE])
        for enemy in self.bot_ai.enemy_units:
            if enemy.type_id in self.SPECIAL_STRUCTURE_VALUE:
                weight = self.SPECIAL_STRUCTURE_VALUE[enemy.type_id]
            elif enemy.type_id in self.SPECIAL_UNIT_VALUE:
                weight = self.SPECIAL_UNIT_VALUE[enemy.type_id]
            elif enemy.is_structure:
                weight = self.DEFAULT_STRUCTURE_VALUE
            else:
                weight = self.DEFAULT_UNIT_VALUE
            influence_map.add_point(enemy.position, enemy.radius, weight)
        return influence_map
