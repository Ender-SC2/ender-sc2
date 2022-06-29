# common.py, Ender

from math import sqrt
from typing import List, overload

from loguru import logger

from ender.job import Job
from ender.unit.unit_command import IUnitCommand
from ender.unit.unit_interface import IUnitInterface, UnitInterface
from sc2.bot_ai import BotAI  # parent class we inherit from
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit


class Common(BotAI, IUnitInterface):

    # Unit Interface
    _unit_interface: IUnitInterface = UnitInterface()

    # constants after step0:
    nowhere = Point2((1,1))
    notag = -1
    game_step = 4 # the amount of frames between program-step-runs
    __did_step0 = False
    enemymain = nowhere
    ourmain = nowhere
    seconds = 22.4
    minutes = seconds * 60
    all_halltypes = {UnitTypeId.COMMANDCENTER,UnitTypeId.ORBITALCOMMAND,UnitTypeId.PLANETARYFORTRESS,
                     UnitTypeId.HATCHERY,UnitTypeId.LAIR,UnitTypeId.HIVE,UnitTypeId.NEXUS}
    all_tumortypes = {UnitTypeId.CREEPTUMORBURROWED,UnitTypeId.CREEPTUMOR,UnitTypeId.CREEPTUMORQUEEN}
    all_changelings = {UnitTypeId.CHANGELING, UnitTypeId.CHANGELINGMARINE, UnitTypeId.CHANGELINGMARINESHIELD,
                       UnitTypeId.CHANGELINGZEALOT, UnitTypeId.CHANGELINGZERGLING,
                       UnitTypeId.CHANGELINGZERGLINGWINGS}
    all_armytypes = all_changelings | {UnitTypeId.QUEEN, UnitTypeId.ROACH, UnitTypeId.MUTALISK, UnitTypeId.ZERGLING,
                     UnitTypeId.OVERSEER, UnitTypeId.CORRUPTOR, UnitTypeId.BROODLORD, UnitTypeId.INFESTOR,
                     UnitTypeId.BROODLING, UnitTypeId.HYDRALISK, UnitTypeId.LURKERMP,
                     UnitTypeId.OVERLORDTRANSPORT, UnitTypeId.VIPER, UnitTypeId.BANELING, UnitTypeId.ULTRALISK,
                    UnitTypeId.LOCUSTMP, UnitTypeId.LOCUSTMPFLYING, UnitTypeId.OVERSEERSIEGEMODE,
                    UnitTypeId.RAVAGER, UnitTypeId.SWARMHOSTMP}
    all_burrowtypes = {UnitTypeId.LURKERMPBURROWED, UnitTypeId.ZERGLINGBURROWED, UnitTypeId.BANELINGBURROWED,
                       UnitTypeId.ULTRALISKBURROWED, UnitTypeId.DRONEBURROWED, UnitTypeId.HYDRALISKBURROWED,
                       UnitTypeId.INFESTORBURROWED, UnitTypeId.QUEENBURROWED, UnitTypeId.RAVAGERBURROWED,
                       UnitTypeId.SWARMHOSTBURROWEDMP}
    all_num_upgrades = {UpgradeId.ZERGMISSILEWEAPONSLEVEL1, UpgradeId.ZERGMELEEWEAPONSLEVEL1,
                        UpgradeId.ZERGGROUNDARMORSLEVEL1,
                        UpgradeId.ZERGMISSILEWEAPONSLEVEL2, UpgradeId.ZERGMELEEWEAPONSLEVEL2,
                        UpgradeId.ZERGGROUNDARMORSLEVEL2,
                        UpgradeId.ZERGMISSILEWEAPONSLEVEL3, UpgradeId.ZERGMELEEWEAPONSLEVEL3,
                        UpgradeId.ZERGGROUNDARMORSLEVEL3,
                        UpgradeId.ZERGFLYERARMORSLEVEL1, UpgradeId.ZERGFLYERARMORSLEVEL2,
                        UpgradeId.ZERGFLYERARMORSLEVEL3, UpgradeId.ZERGFLYERWEAPONSLEVEL1,
                        UpgradeId.ZERGFLYERWEAPONSLEVEL2, UpgradeId.ZERGFLYERWEAPONSLEVEL3}
    all_ind_upgrades = {UpgradeId.OVERLORDSPEED,
                        UpgradeId.BURROW,
                        UpgradeId.ZERGLINGMOVEMENTSPEED,
                        UpgradeId.ZERGLINGATTACKSPEED,
                        UpgradeId.CHITINOUSPLATING,
                        UpgradeId.LURKERRANGE,
                        UpgradeId.CENTRIFICALHOOKS,
                        UpgradeId.EVOLVEGROOVEDSPINES,
                        UpgradeId.EVOLVEMUSCULARAUGMENTS,
                        UpgradeId.NEURALPARASITE,
                        UpgradeId.GLIALRECONSTITUTION}
    all_upgrades = all_num_upgrades | all_ind_upgrades
                    # all means: known to this bot
    all_eggtypes = {UnitTypeId.EGG, UnitTypeId.BROODLORDCOCOON, UnitTypeId.RAVAGERCOCOON, UnitTypeId.BANELINGCOCOON,
                    UnitTypeId.TRANSPORTOVERLORDCOCOON, UnitTypeId.OVERLORDCOCOON, UnitTypeId.LURKERMPEGG}
    all_unittypes = all_armytypes | all_burrowtypes | all_eggtypes | {UnitTypeId.DRONE, UnitTypeId.LARVA,
                     UnitTypeId.OVERLORD}
    all_sporetypes = {UnitTypeId.SPORECRAWLER, UnitTypeId.SPINECRAWLER, UnitTypeId.SPORECRAWLERUPROOTED,
                      UnitTypeId.SPINECRAWLERUPROOTED}
    all_normalstructuretypes = \
        {UnitTypeId.HATCHERY, UnitTypeId.SPAWNINGPOOL, UnitTypeId.EXTRACTOR, UnitTypeId.EXTRACTORRICH,
         UnitTypeId.EVOLUTIONCHAMBER, UnitTypeId.ROACHWARREN,UnitTypeId.LAIR, UnitTypeId.SPIRE, UnitTypeId.HIVE,
         UnitTypeId.INFESTATIONPIT, UnitTypeId.GREATERSPIRE, UnitTypeId.HYDRALISKDEN, UnitTypeId.LURKERDENMP,
         UnitTypeId.BANELINGNEST, UnitTypeId.ULTRALISKCAVERN, UnitTypeId.NYDUSCANAL, UnitTypeId.NYDUSNETWORK}
    all_structuretypes = all_tumortypes | all_sporetypes | all_normalstructuretypes
    all_types = all_upgrades | all_structuretypes | all_unittypes
    all_workertypes = {UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.MULE}
    # constants for this map:
    map_center = nowhere
    map_left = 0
    map_top = 0
    map_right = 0
    map_bottom = 0
    #
    builddura_of_structure = {}
    size_of_structure = {}
    species_of_structure = {}
    #
    #
    # constant in the step (after init_step):
    did_common_onstep = False
    did_map_onstep = False
    did_tech_onstep = False
    iteration = 0
    frame = 0 # will have even numbers if game_step=2
    nbases = 1 # own halls > 80% ready
    enemy_struc_mem = set() # structures out of sight still are there (expected)
    enemy_struc_mem_hash = 0 # to react on changes
    structures_hash = 0 # to react on changes
    freeexpos = []
    freegeysers = []
    living = set() # all tags of own units and structures
    last_living = set() # last programrun
    last_health = {}
    hospital = None
    extractors = [] # extractors not empty
    drones_supply_used = 12
    queens_supply_used = 0
    army_supply_used = 0
    supplycap_drones = 90
    supplycap_queens = 20
    supplycap_army = 90
    #
    # variables:
    listenframe_of_unit = {} # frame the command will have arrived
    listenframe_of_structure = {} # frame the command will have arrived
    listenframe_of_function = {} # frame the command will have arrived
    limbo = {} # per tag of a disappeared unit: the frame to forget it
    bigattack_count = 0 # report from attack to strategy
    bigattacking = False # report from attack
    supplytricking = False # report from making
    next_expansion = None # report from making to attack (block)
    current_expandings = {} # report from making to attack (block)
    to_root = set() # sporespinecrawlers uprooted to be picked up by 'making'.
    resign = False
    queen_of_hall = {}
    #
    __did_step0 = False
    _last_structures_len = 0 # internal speedup
    _last_enemy_struc_mem_len = 0 # internal speedup


    async def __step0(self):
        self.enemymain = self.enemy_start_locations[0].position
        self.ourmain = self.start_location
        self.enemy_struc_mem.add((UnitTypeId.COMMANDCENTER,self.enemymain))
        self.map_center = self.game_info.map_center
        self.map_left = self.game_info.playable_area.x
        self.map_right = self.game_info.playable_area.width+self.game_info.playable_area.x
        self.map_bottom = self.game_info.playable_area.y
        self.map_top = self.game_info.playable_area.height+self.game_info.playable_area.y
        self.hospital = self.ourmain.towards(self.map_center,-7)

    async def on_start(self):
        self._client.game_step = self.game_step
        # if running realtime speed, this will be overwritten?

    async def on_step(self, iteration):
        # game init
        if not self.__did_step0:
            await self.__step0()
            self.__did_step0 = True
        if not self.did_common_onstep:
            self.did_common_onstep = True
            # frame
            self.game_step = self._client.game_step
            self.frame = self.iteration * self.game_step
            logger.info('---------------- ' + str(self.frame) + ' -------------------' )
            # nbases
            self.nbases = 0
            for typ in self.all_halltypes:
                for stru in (self.structures(typ)):
                    if stru.build_progress >= 0.8:
                        self.nbases += 1
            # living
            # for speed do not check all_tumortypes
            self.living: set[int] = set()
            for unt in self.units:
                self.living.add(unt.tag)
            for typ in self.all_structuretypes:
                if typ not in self.all_tumortypes:
                    for stru in self.structures(typ):
                            self.living.add(stru.tag)
            for ovi in self.units(UnitTypeId.OVERLORDTRANSPORT):
                for pastag in ovi.passengers_tags:
                    self.living.add(pastag)
            # listenframe
            todel = []
            for tag in self.listenframe_of_unit:
                if tag not in self.living:
                    todel.append(tag)
            for tag in todel:
                del self.listenframe_of_unit[tag]
            for unt in self.units:
                if unt.tag not in self.listenframe_of_unit:
                    self.listenframe_of_unit[unt.tag] = 0
            for typ in self.all_structuretypes:
                if typ not in self.all_tumortypes:
                    for stru in self.structures(typ):
                        if stru.tag not in self.listenframe_of_structure:
                            self.listenframe_of_structure[stru.tag] = 0
            # enemy_struc_mem
            for stru in self.enemy_structures:
                if not stru.is_flying: # moving, like BARRACKSFLYING
                    if stru.type_id not in {UnitTypeId.SPINECRAWLERUPROOTED,UnitTypeId.SPORECRAWLERUPROOTED}:
                        if stru.type_id not in self.all_tumortypes: # too much
                            self.enemy_struc_mem.add((stru.type_id,stru.position))
            todel = set()
            for tp in self.enemy_struc_mem:
                (typ,pos) = tp
                if self.is_visible(pos):
                    seen = False
                    for ene in self.enemy_structures:
                        if (ene.position == pos):
                            seen = True
                    if not seen:
                        todel.add(tp)
            self.enemy_struc_mem -= todel
            # enemy_struc_mem_hash
            enemy_struc_mem_len = len(self.enemy_struc_mem)
            if enemy_struc_mem_len != self._last_enemy_struc_mem_len:
                self._last_enemy_struc_mem_len = enemy_struc_mem_len
                ehash = 0
                for tp in self.enemy_struc_mem:
                    (typ,pos) = tp
                    ehash += pos.x
                self.enemy_struc_mem_hash = ehash
            # structures_hash
            structures_len = len(self.structures)
            if structures_len != self._last_structures_len:
                self._last_structures_len = structures_len
                ehash = 0
                for typ in self.all_normalstructuretypes:
                    for stru in self.structures(typ):
                        ehash += stru.position.x
                self.structures_hash = ehash
            #
            # freegeysers
            self.freegeysers = []
            typ = UnitTypeId.EXTRACTOR
            alt = UnitTypeId.EXTRACTORRICH
            goodgeysers = [gey for gey in self.vespene_geyser
                            if any(gey.distance_to(base) <= 12 for base in self.townhalls.ready)]
            for geyser in goodgeysers:
                free = True
                for stru in self.structures(typ):
                    if geyser.position == stru.position:
                        free = False
                for stru in self.structures(alt):
                    if geyser.position == stru.position:
                        free = False
                for (enetyp,enepos) in self.enemy_struc_mem:
                    if enepos == geyser.position:
                        free = False
                if free:
                    self.freegeysers.append(geyser)
            # print('freegeysers: ' + str(len(self.freegeysers)))
            # freeexpos
            self.freeexpos = []
            for pos in self.expansion_locations_list:
                free = True
                for typ in self.all_halltypes:
                    for stru in self.structures(typ):
                        if self.distance(stru.position,pos) < 3:
                            free = False
                for (enetyp,enepos) in self.enemy_struc_mem:
                    if self.distance(enepos,pos) < 3:
                        free = False
                if free:
                    self.freeexpos.append(pos)
            # print('freeexpos: ' + str(len(self.freeexpos)))
            # limbo
            # disappeared unit tags are in limbo for 60 frames
            for tag in self.last_living:
                if tag not in self.living:
                   self.limbo[tag] = self.frame + 60
            # cleanup limbo
            todel = set()
            for tag in self.limbo:
                if self.limbo[tag] < self.frame:
                    todel.add(tag)
            for tag in todel:
                del self.limbo[tag]
            # extractors
            if self.frame % 11 == 10:
                geysers_nonemp = self.vespene_geyser.filter(lambda gey: gey.has_vespene)
                geysers_nonemp_pos = [gey.position for gey in geysers_nonemp]
                self.extractors = self.structures(UnitTypeId.EXTRACTOR).ready.filter(lambda gb: gb.position in geysers_nonemp_pos)
                self.extractors |= self.structures(UnitTypeId.EXTRACTORRICH).ready.filter(lambda gb: gb.position in geysers_nonemp_pos)
            # drones_supply_used
            self.drones_supply_used = len(self.units(UnitTypeId.DRONE))
            for tag in self.limbo:
                if self.job_of_unittag(tag) == Job.GASMINER:
                    self.drones_supply_used += 1
            for egg in self.units(UnitTypeId.EGG):
                for order in egg.orders:
                    if order.ability.exact_id == AbilityId.LARVATRAIN_DRONE:
                        self.drones_supply_used += 1
            # queens_supply_used
            self.queens_supply_used = 2 * len(self.units(UnitTypeId.QUEEN))
            for hatchtype in self.all_halltypes:
                for hatch in self.structures(hatchtype):
                    for order in hatch.orders:
                        if order.ability.exact_id == AbilityId.TRAINQUEEN_QUEEN:
                            self.queens_supply_used += 2
            # army_supply_used
            self.army_supply_used = self.supply_used - (self.drones_supply_used + self.queens_supply_used)

    def distance(self, p, q) -> float:
        sd = (p.x-q.x)*(p.x-q.x) + (p.y-q.y)*(p.y-q.y)
        return sqrt(sd)

    def range_vs(self, unit: Unit, target: Unit) -> float:
        ground_range = 0
        air_range = 0
        if unit.can_attack_ground and not target.is_flying:
            ground_range = unit.ground_range
        elif unit.can_attack_air and (target.is_flying or target.type_id == UnitTypeId.COLOSSUS):
            air_range = unit.air_range
        return max(ground_range, air_range)

    def function_listens(self, name,delay) -> bool:
        # forces 'delay' frames between function calls.
        # init
        if name not in self.listenframe_of_function:
            self.listenframe_of_function[name] = -99999
        # very rarely, the delay is lowered
        if self.listenframe_of_function[name] > self.frame + delay:
            self.listenframe_of_function[name] = self.frame + delay
        # decide if the function will run
        if self.frame >= self.listenframe_of_function[name]:
            self.listenframe_of_function[name] = self.frame + delay
            return True
        return False

    def set_command(self, unit: Unit, command: IUnitCommand):
        self._unit_interface.set_command(unit, command)

    def queue_command(self, unit: Unit, command: IUnitCommand):
        self._unit_interface.queue_command(unit, command)

    async def execute(self):
        self._unit_interface.execute()

    def job_of_unit(self, unit: Unit) -> Job:
        return self._unit_interface.job_of_unit(unit)

    def job_of_unittag(self, tag: int) -> Job:
        return self._unit_interface.job_of_unittag(tag)

    def set_job_of_unit(self, unit: Unit, job: Job):
        self._unit_interface.set_job_of_unit(unit, job)

    def set_job_of_unittag(self, tag: int, job: Job):
        self._unit_interface.set_job_of_unittag(tag, job)

    def job_count(self, job: Job) -> int:
        return self._unit_interface.job_count(job)
