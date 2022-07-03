# spell_effect_dodging_behavior.py
from typing import List, Optional, Dict

from loguru import logger

from ender.job import Job
from ender.map import InfluenceMap
from ender.unit import MoveCommand
from ender.utils.ability_utils import ability_duration, ability_range, ability_radius, AbilityDamageType, \
    ability_damage_type, ability_damage
from ender.utils.command_utils import CommandUtils
from ender.utils.effect_utils import effect_ability
from sc2.ids.ability_id import AbilityId
from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


# Differ persistent damage (psi storm) from landing damage (bile)
# Information on influence map so later we can look for pathing and look for a safe place close to unit.
# Increased weight for landing spells when the spell gets closer to landing
# Lower weight for persistent spells as time passes (as most of the damage is already done)
# TODO: Add support for nuke
# TODO: Move enemy tracking into a different class
class SpellEffectDodgingBehavior(CommandUtils):
    supported_spells: list[EffectId] = [EffectId.RAVAGERCORROSIVEBILECP, EffectId.PSISTORMPERSISTENT]
    extra_dodge_range = 1

    def __init__(self, unit_types: Optional[List[UnitTypeId]] = None, jobs: Optional[List[Job]] = None):
        self.unit_types: Optional[List[UnitTypeId]] = unit_types
        self.jobs: Optional[List[Job]] = jobs
        self.spells: Dict[(Point2, EffectId), List[float]] = {}  # Position, Effect, Expected end time

    async def on_step(self, iteration: int):
        my_units = self.bot_ai.units.filter(
            lambda unit: (not self.jobs or self.unit_interface.job_of_unit(unit) in self.jobs) and (
                    not self.unit_types or unit.type_id in self.unit_types)
        )
        if my_units.empty:
            return
        self.check_existing_spells()
        influence_map = self.create_influence_map()
        for unit in my_units:
            in_danger = self.in_dangerous_area(unit)
            if in_danger:
                # TODO: Find a better dodge distance
                safest_point = influence_map.get_closest_point(unit.position, unit.radius, 3, -10)
                if safest_point and safest_point != unit.position:
                    self.unit_interface.set_command(unit, MoveCommand(safest_point, "SpellDodging"))
                else:
                    logger.error(f"Could not find a safe point close to {unit.position}")

    def check_existing_spells(self):
        game_time = self.bot_ai.time
        # Delete old spells
        to_delete = set()
        for key in self.spells.keys():
            self.spells[key] = [time for time in self.spells[key] if time > game_time]
            if len(self.spells[key]) == 0:
                to_delete.add(key)
        for key in to_delete:
            self.spells.pop(key)
        # New spells
        spell_counter = {}
        for effect in self.bot_ai.state.effects:
            if effect.id in self.supported_spells:
                for position in effect.positions:
                    key = (position, effect.id)
                    if key not in spell_counter:
                        spell_counter[key] = 0
                    spell_counter[key] += 1
                    if key not in self.spells:
                        self.spells[key] = []
                    if spell_counter[key] > len(self.spells[key]):
                        self.spells[key].append(game_time + ability_duration[effect_ability[effect.id]])

    def in_dangerous_area(self, unit) -> bool:
        for (location, spell) in self.spells.keys():
            if location.distance_to(unit.position) < ability_range[effect_ability[spell]] + self.extra_dodge_range:
                return True
        return False

    def create_influence_map(self) -> InfluenceMap:
        influence_map = InfluenceMap(ability_radius[AbilityId.EFFECT_CORROSIVEBILE])
        for (position, effect), times in self.spells.items():
            ability = effect_ability[effect]
            for time in times:
                time_to_end = (time - self.bot_ai.time) / ability_duration[ability]
                if ability_damage_type[ability] == AbilityDamageType.PERSISTENT:
                    damage = ability_damage[ability] * (1 - time_to_end)
                else:
                    damage = ability_damage[ability] * time_to_end * time_to_end
                influence_map.add_point(position, ability_radius[ability] + self.extra_dodge_range, -damage)
        return influence_map
