# pyright: reportGeneralTypeIssues=false
import sc2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

unit_creation_ability: dict[UnitTypeId, AbilityId] = {}
unit_created_from: dict[UnitTypeId, UnitTypeId] = {}

for bartype in sc2.dicts.unit_research_abilities.RESEARCH_INFO:
    for unit_type_id in sc2.dicts.unit_research_abilities.RESEARCH_INFO[bartype]:
        abi = sc2.dicts.unit_research_abilities.RESEARCH_INFO[bartype][unit_type_id]["ability"]
        unit_creation_ability[unit_type_id] = abi
for bartype in sc2.dicts.unit_train_build_abilities.TRAIN_INFO:
    for unit_type_id in sc2.dicts.unit_train_build_abilities.TRAIN_INFO[bartype]:
        abi = sc2.dicts.unit_train_build_abilities.TRAIN_INFO[bartype][unit_type_id]["ability"]
        unit_creation_ability[unit_type_id] = abi
unit_creation_ability[UnitTypeId.CHANGELING] = AbilityId.SPAWNCHANGELING_SPAWNCHANGELING
unit_creation_ability[UnitTypeId.LURKERMPBURROWED] = AbilityId.BURROWDOWN_LURKER
unit_creation_ability[UnitTypeId.ULTRALISKBURROWED] = AbilityId.BURROWDOWN_ULTRALISK
unit_creation_ability[UnitTypeId.DRONEBURROWED] = AbilityId.BURROWDOWN_DRONE
unit_creation_ability[UnitTypeId.CREEPTUMOR] = AbilityId.BUILD_CREEPTUMOR_TUMOR
unit_creation_ability[UnitTypeId.OVERSEERSIEGEMODE] = AbilityId.MORPH_OVERSIGHTMODE
unit_creation_ability[UnitTypeId.OVERSEER] = AbilityId.MORPH_OVERSEER
unit_creation_ability[UnitTypeId.OVERLORDTRANSPORT] = AbilityId.MORPH_OVERLORDTRANSPORT
unit_creation_ability[UnitTypeId.QUEENBURROWED] = AbilityId.BURROWDOWN_QUEEN
unit_creation_ability[UnitTypeId.RAVAGERBURROWED] = AbilityId.BURROWDOWN_RAVAGER
unit_creation_ability[UnitTypeId.ROACHBURROWED] = AbilityId.BURROWDOWN_ROACH
unit_creation_ability[UnitTypeId.SPINECRAWLERUPROOTED] = AbilityId.SPINECRAWLERUPROOT_SPINECRAWLERUPROOT
unit_creation_ability[UnitTypeId.SPORECRAWLERUPROOTED] = AbilityId.SPORECRAWLERUPROOT_SPORECRAWLERUPROOT
unit_creation_ability[UnitTypeId.SWARMHOSTBURROWEDMP] = AbilityId.BURROWDOWN_SWARMHOST
unit_creation_ability[UnitTypeId.ULTRALISKBURROWED] = AbilityId.BURROWDOWN_ULTRALISK
unit_creation_ability[UnitTypeId.ZERGLINGBURROWED] = AbilityId.BURROWDOWN_ZERGLING
unit_creation_ability[UnitTypeId.BANELINGBURROWED] = AbilityId.BURROWDOWN_BANELING
unit_creation_ability[UnitTypeId.LOCUSTMP] = AbilityId.EFFECT_LOCUSTSWOOP


for unit_type_id in sc2.dicts.unit_trained_from.UNIT_TRAINED_FROM:
    apiset = sc2.dicts.unit_trained_from.UNIT_TRAINED_FROM[unit_type_id]
    if len(apiset) == 1:
        unit_created_from[unit_type_id] = list(apiset)[0]
for unit_type_id in sc2.dicts.upgrade_researched_from.UPGRADE_RESEARCHED_FROM:
    unit_created_from[unit_type_id] = sc2.dicts.upgrade_researched_from.UPGRADE_RESEARCHED_FROM[unit_type_id]
unit_created_from[UnitTypeId.LURKERMPBURROWED] = UnitTypeId.LURKERMP
unit_created_from[UnitTypeId.ULTRALISKBURROWED] = UnitTypeId.ULTRALISK
unit_created_from[UnitTypeId.DRONEBURROWED] = UnitTypeId.DRONE
unit_created_from[UnitTypeId.CHANGELING] = UnitTypeId.OVERSEER
unit_created_from[UnitTypeId.CREEPTUMOR] = UnitTypeId.CREEPTUMORBURROWED
unit_created_from[UnitTypeId.CREEPTUMORBURROWED] = UnitTypeId.CREEPTUMOR
unit_created_from[UnitTypeId.QUEEN] = UnitTypeId.HATCHERY
unit_created_from[UnitTypeId.OVERSEER] = UnitTypeId.OVERLORD
unit_created_from[UnitTypeId.OVERLORDTRANSPORT] = UnitTypeId.OVERLORD
unit_created_from[UnitTypeId.OVERSEERSIEGEMODE] = UnitTypeId.OVERSEER
unit_created_from[UnitTypeId.QUEENBURROWED] = UnitTypeId.QUEEN
unit_created_from[UnitTypeId.RAVAGERBURROWED] = UnitTypeId.RAVAGER
unit_created_from[UnitTypeId.ROACHBURROWED] = UnitTypeId.ROACH
unit_created_from[UnitTypeId.SPINECRAWLERUPROOTED] = UnitTypeId.SPINECRAWLER
unit_created_from[UnitTypeId.SPORECRAWLERUPROOTED] = UnitTypeId.SPORECRAWLER
unit_created_from[UnitTypeId.SWARMHOSTBURROWEDMP] = UnitTypeId.SWARMHOSTMP
unit_created_from[UnitTypeId.LOCUSTMPFLYING] = UnitTypeId.SWARMHOSTMP
unit_created_from[UnitTypeId.ULTRALISKBURROWED] = UnitTypeId.ULTRALISK
unit_created_from[UnitTypeId.ZERGLINGBURROWED] = UnitTypeId.ZERGLING
unit_created_from[UnitTypeId.BANELINGBURROWED] = UnitTypeId.BANELING
unit_created_from[UnitTypeId.HYDRALISKBURROWED] = UnitTypeId.HYDRALISK
unit_created_from[UnitTypeId.INFESTORBURROWED] = UnitTypeId.INFESTOR
unit_created_from[UnitTypeId.LOCUSTMP] = UnitTypeId.LOCUSTMPFLYING
unit_created_from[UnitTypeId.EXTRACTORRICH] = UnitTypeId.DRONE
unit_created_from[UnitTypeId.BROODLING] = UnitTypeId.BROODLORD
