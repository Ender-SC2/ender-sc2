# common.py, Ender

from loguru import logger

from ender.cache.enemy_cache import EnemyCache
from ender.job import Job
from ender.production.emergency import EmergencyQueue
from ender.unit.unit_command import IUnitCommand
from ender.unit.unit_interface import IUnitInterface, UnitInterface
from ender.utils.point_utils import distance
from sc2.bot_ai import BotAI  # parent class we inherit from
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit


class Common(BotAI, IUnitInterface):

    # Unit Interface
    _unit_interface: IUnitInterface = UnitInterface()
    enemy_cache: EnemyCache = EnemyCache()

    # constants after step0:
    nowhere = Point2((1, 1))
    notag = -1
    game_step = 4  # the amount of frames between program-step-runs
    enemymain = nowhere
    ourmain = nowhere
    seconds = 22.4
    minutes = seconds * 60
    expansion_locations = []
    all_halltypes = {
        UnitTypeId.COMMANDCENTER,
        UnitTypeId.ORBITALCOMMAND,
        UnitTypeId.PLANETARYFORTRESS,
        UnitTypeId.HATCHERY,
        UnitTypeId.LAIR,
        UnitTypeId.HIVE,
        UnitTypeId.NEXUS,
    }
    all_tumortypes = {UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORQUEEN}
    all_changelings = {
        UnitTypeId.CHANGELING,
        UnitTypeId.CHANGELINGMARINE,
        UnitTypeId.CHANGELINGMARINESHIELD,
        UnitTypeId.CHANGELINGZEALOT,
        UnitTypeId.CHANGELINGZERGLING,
        UnitTypeId.CHANGELINGZERGLINGWINGS,
    }
    all_armytypes = all_changelings | {
        UnitTypeId.QUEEN,
        UnitTypeId.ROACH,
        UnitTypeId.MUTALISK,
        UnitTypeId.ZERGLING,
        UnitTypeId.OVERSEER,
        UnitTypeId.CORRUPTOR,
        UnitTypeId.BROODLORD,
        UnitTypeId.INFESTOR,
        UnitTypeId.BROODLING,
        UnitTypeId.HYDRALISK,
        UnitTypeId.LURKERMP,
        UnitTypeId.OVERLORDTRANSPORT,
        UnitTypeId.VIPER,
        UnitTypeId.BANELING,
        UnitTypeId.ULTRALISK,
        UnitTypeId.LOCUSTMP,
        UnitTypeId.LOCUSTMPFLYING,
        UnitTypeId.OVERSEERSIEGEMODE,
        UnitTypeId.RAVAGER,
        UnitTypeId.SWARMHOSTMP,
    }
    all_burrowtypes = {
        UnitTypeId.LURKERMPBURROWED,
        UnitTypeId.ZERGLINGBURROWED,
        UnitTypeId.BANELINGBURROWED,
        UnitTypeId.ULTRALISKBURROWED,
        UnitTypeId.DRONEBURROWED,
        UnitTypeId.HYDRALISKBURROWED,
        UnitTypeId.INFESTORBURROWED,
        UnitTypeId.QUEENBURROWED,
        UnitTypeId.RAVAGERBURROWED,
        UnitTypeId.SWARMHOSTBURROWEDMP,
    }
    all_num_upgrades = {
        UpgradeId.ZERGMISSILEWEAPONSLEVEL1,
        UpgradeId.ZERGMELEEWEAPONSLEVEL1,
        UpgradeId.ZERGGROUNDARMORSLEVEL1,
        UpgradeId.ZERGMISSILEWEAPONSLEVEL2,
        UpgradeId.ZERGMELEEWEAPONSLEVEL2,
        UpgradeId.ZERGGROUNDARMORSLEVEL2,
        UpgradeId.ZERGMISSILEWEAPONSLEVEL3,
        UpgradeId.ZERGMELEEWEAPONSLEVEL3,
        UpgradeId.ZERGGROUNDARMORSLEVEL3,
        UpgradeId.ZERGFLYERARMORSLEVEL1,
        UpgradeId.ZERGFLYERARMORSLEVEL2,
        UpgradeId.ZERGFLYERARMORSLEVEL3,
        UpgradeId.ZERGFLYERWEAPONSLEVEL1,
        UpgradeId.ZERGFLYERWEAPONSLEVEL2,
        UpgradeId.ZERGFLYERWEAPONSLEVEL3,
    }
    all_ind_upgrades = {
        UpgradeId.OVERLORDSPEED,
        UpgradeId.BURROW,
        UpgradeId.ZERGLINGMOVEMENTSPEED,
        UpgradeId.ZERGLINGATTACKSPEED,
        UpgradeId.CHITINOUSPLATING,
        UpgradeId.LURKERRANGE,
        UpgradeId.CENTRIFICALHOOKS,
        UpgradeId.EVOLVEGROOVEDSPINES,
        UpgradeId.EVOLVEMUSCULARAUGMENTS,
        UpgradeId.NEURALPARASITE,
        UpgradeId.GLIALRECONSTITUTION,
    }
    all_upgrades = all_num_upgrades | all_ind_upgrades
    # all means: known to this bot
    all_eggtypes = {
        UnitTypeId.EGG,
        UnitTypeId.BROODLORDCOCOON,
        UnitTypeId.RAVAGERCOCOON,
        UnitTypeId.BANELINGCOCOON,
        UnitTypeId.TRANSPORTOVERLORDCOCOON,
        UnitTypeId.OVERLORDCOCOON,
        UnitTypeId.LURKERMPEGG,
    }
    all_unittypes = (
        all_armytypes | all_burrowtypes | all_eggtypes | {UnitTypeId.DRONE, UnitTypeId.LARVA, UnitTypeId.OVERLORD}
    )
    all_sporetypes = {
        UnitTypeId.SPORECRAWLER,
        UnitTypeId.SPINECRAWLER,
        UnitTypeId.SPORECRAWLERUPROOTED,
        UnitTypeId.SPINECRAWLERUPROOTED,
    }
    all_normalstructuretypes = {
        UnitTypeId.HATCHERY,
        UnitTypeId.SPAWNINGPOOL,
        UnitTypeId.EXTRACTOR,
        UnitTypeId.EXTRACTORRICH,
        UnitTypeId.EVOLUTIONCHAMBER,
        UnitTypeId.ROACHWARREN,
        UnitTypeId.LAIR,
        UnitTypeId.SPIRE,
        UnitTypeId.HIVE,
        UnitTypeId.INFESTATIONPIT,
        UnitTypeId.GREATERSPIRE,
        UnitTypeId.HYDRALISKDEN,
        UnitTypeId.LURKERDENMP,
        UnitTypeId.BANELINGNEST,
        UnitTypeId.ULTRALISKCAVERN,
        UnitTypeId.NYDUSCANAL,
        UnitTypeId.NYDUSNETWORK,
    }
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
    frame = 0  # will have even numbers if game_step=2
    nbases = 1  # own halls > 80% ready
    nenemybases = 1  # enemy halls seen (started)
    enemy_struc_mem = {}  # structures out of sight still are there (expected). Using postag to make position unique.
    enemy_struc_mem_hash = 0  # to react on changes
    enemy_unit_mem = {}  # enemy units, about each second, per tag: (type, last seen place)
    eum_frame = 0
    structures_hash = 0  # to react on changes
    freeexpos = []
    freegeysers = []
    living = set()  # all tags of own units and structures
    last_living = set()  # last programrun
    last_health = {}
    hospital = None
    extractors = []  # extractors not empty
    drones_supply_used = 12
    queens_supply_used = 0
    army_supply_used = 0
    supplycap_drones = 90
    supplycap_queens = 20
    supplycap_army = 90
    lairtech = False
    #
    # variables:
    listenframe_of_unit = {}  # frame the command will have arrived
    listenframe_of_structure = {}  # frame the command will have arrived
    listenframe_of_function = {}  # frame the command will have arrived
    limbo = {}  # per tag of a disappeared unit: the frame to forget it
    wave_count = 0  # report from attack to strategy
    bigattacking = False  # report from attack
    supplytricking = False  # report from making
    next_expansion = None  # report from making to attack
    current_expandings = {}  # report from making to attack
    to_root = set()  # sporespinecrawlers uprooted to be picked up by 'making'.
    resign = False
    queen_of_hall = {}  # a queen with tag in queen_of_hall.values() behaves different...
    cooldown_sh = {}  # per swarmhost tag the moment it can make locusts.
    auto_groupqueen = False
    agression = False  # panic
    #
    __did_step0 = False
    _last_structures_len = 0  # internal speedup
    _last_enemy_struc_mem_len = 0  # internal speedup
    emergency: EmergencyQueue = EmergencyQueue()  # A thing in emergency will build with 2000 importance.

    async def __step0(self):
        self.enemymain = self.enemy_start_locations[0].position
        self.ourmain = self.start_location
        postag = self.postag_of_pos(self.enemymain)
        self.enemy_struc_mem[postag] = (UnitTypeId.COMMANDCENTER, self.enemymain)
        self.map_center = self.game_info.map_center
        self.map_left = self.game_info.playable_area.x
        self.map_right = self.game_info.playable_area.width + self.game_info.playable_area.x
        self.map_bottom = self.game_info.playable_area.y
        self.map_top = self.game_info.playable_area.height + self.game_info.playable_area.y
        self.hospital = self.ourmain.towards(self.map_center, -7)
        self.expansion_locations = self.expansion_locations_list.copy()
        # mapspecific
        if self.game_info.map_name == "2000 Atmospheres AIE":
            mispoint = Point2((67.5, 130.5))
            correctpoint = Point2((66.5, 131.5))
            del self.expansion_locations[self.expansion_locations.index(mispoint)]
            self.expansion_locations.append(correctpoint)
            mispoint = Point2((156.5, 73.5))
            correctpoint = Point2((157.5, 72.5))
            del self.expansion_locations[self.expansion_locations.index(mispoint)]
            self.expansion_locations.append(correctpoint)
        #

    async def on_start(self):
        self.client.game_step = self.game_step
        # if running realtime speed, this will be overwritten?

    async def on_step(self, iteration):
        # game init
        if not self.__did_step0:
            await self.__step0()
            self.__did_step0 = True
        if not self.did_common_onstep:
            self.did_common_onstep = True
            self.enemy_cache.update(self)
            # frame
            self.game_step = self.client.game_step
            self.frame = self.iteration * self.game_step
            logger.info("---------------- " + str(self.frame) + " -------------------")
            # nbases
            self.nbases = 0
            for typ in self.all_halltypes:
                for stru in self.structures(typ):
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
                if not stru.is_flying:  # moving, like BARRACKSFLYING
                    if stru.type_id not in {UnitTypeId.SPINECRAWLERUPROOTED, UnitTypeId.SPORECRAWLERUPROOTED}:
                        if stru.type_id not in self.all_tumortypes:  # too much
                            postag = self.postag_of_pos(stru.position)
                            self.enemy_struc_mem[postag] = (stru.type_id, stru.position)
            todel = set()
            for postag in self.enemy_struc_mem:
                tp = self.enemy_struc_mem[postag]
                (typ, pos) = tp
                if self.is_visible(pos):
                    seen = False
                    for ene in self.enemy_structures:
                        if ene.position == pos:
                            seen = True
                    if not seen:
                        todel.add(postag)
            for postag in todel:
                del self.enemy_struc_mem[postag]
            # enemy_unit_mem
            if self.frame > self.eum_frame:
                self.eum_frame = self.frame + 21
                for ene in self.enemy_units:
                    self.enemy_unit_mem[ene.tag] = (ene.type_id, ene.position)
            # nenemybases
            self.nenemybases = 0
            for postag in self.enemy_struc_mem:
                (typ, pos) = self.enemy_struc_mem[postag]
                if typ in self.all_halltypes:
                    self.nenemybases += 1
            # enemy_struc_mem_hash
            enemy_struc_mem_len = len(self.enemy_struc_mem)
            if enemy_struc_mem_len != self._last_enemy_struc_mem_len:
                self._last_enemy_struc_mem_len = enemy_struc_mem_len
                ehash = 0
                for postag in self.enemy_struc_mem:
                    ehash += postag
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
            goodgeysers = [
                gey for gey in self.vespene_geyser if any(gey.distance_to(base) <= 12 for base in self.townhalls.ready)
            ]
            for geyser in goodgeysers:
                free = True
                for stru in self.structures(typ):
                    if geyser.position == stru.position:
                        free = False
                for stru in self.structures(alt):
                    if geyser.position == stru.position:
                        free = False
                for postag in self.enemy_struc_mem:
                    (enetyp, enepos) = self.enemy_struc_mem[postag]
                    if enepos == geyser.position:
                        free = False
                if free:
                    self.freegeysers.append(geyser)
            # print('freegeysers: ' + str(len(self.freegeysers)))
            # freeexpos
            self.freeexpos = []
            for pos in self.expansion_locations:
                free = True
                for typ in self.all_halltypes:
                    for stru in self.structures(typ):
                        if distance(stru.position, pos) < 3:
                            free = False
                for postag in self.enemy_struc_mem:
                    (enetyp, enepos) = self.enemy_struc_mem[postag]
                    if distance(enepos, pos) < 3:
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
                if tag in self.living:
                    todel.add(tag)
            for tag in todel:
                del self.limbo[tag]
            # extractors
            if self.frame % 11 == 10:
                geysers_nonemp = self.vespene_geyser.filter(lambda gey: gey.has_vespene)
                geysers_nonemp_pos = [gey.position for gey in geysers_nonemp]
                self.extractors = self.structures(UnitTypeId.EXTRACTOR).ready.filter(
                    lambda gb: gb.position in geysers_nonemp_pos
                )
                self.extractors |= self.structures(UnitTypeId.EXTRACTORRICH).ready.filter(
                    lambda gb: gb.position in geysers_nonemp_pos
                )
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
            # lairtech
            self.lairtech = len(self.structures(UnitTypeId.LAIR).ready) + len(self.structures(UnitTypeId.HIVE)) > 0
            await self.execute()

    def function_listens(self, name, delay) -> bool:
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

    # SHOULD MOVE TO UNIT_INTERFACE. TEMPORARILY HERE TO RUN.
    def job_count(self, job: Job) -> int:
        return self._unit_interface.job_count(job)

    # COMMON UTILITIES
    def postag_of_pos(self, pos) -> int:
        return round(400 * pos.x + 2 * pos.y)

    def blue_half(self, tag) -> bool:
        return abs(tag) % 10 in {0, 3, 5, 6, 9}  # half of them

    def t_of_p(self, point: Point2) -> str:
        x = round(point.x * 10) / 10
        y = round(point.y * 10) / 10
        return "(" + str(x) + "," + str(y) + ")"

    async def on_unit_destroyed(self, unit_tag: int):
        self.enemy_cache.unit_destroyed(unit_tag)
