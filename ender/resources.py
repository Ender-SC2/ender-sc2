# resources.py, Ender

from enum import Enum, auto

from loguru import logger

from ender.job import Job
from ender.tech import Tech
from sc2.ids.unit_typeid import UnitTypeId


class Resources(Tech):

    __did_step0 = False
    # a claim is needed to make a LAIR, as it needs money and a hatchery not making a queen.
    # claimtype = (typ,resources,importance,expiration)
    claims = []  # of claimtype. Typ will be unique.
    orderdelay = []  # of claimtype. The order has been given but did not arrive yet.
    groupclaim = None  # things, in make_plan but not started, hold a claim at importance 700.
    example = UnitTypeId.SCV  # SCV if you want no example logged
    resource_now_tags = {}  # for resources that are a unit, tags are stored this frame. Not geysers

    def __step0(self):
        self.init_resources()

    async def on_step(self, iteration: int):
        await Tech.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.calc_resource_now()
        await self.claim_administration()

    class Resource(Enum):
        MINERALS = auto()
        VESPENE = auto()
        LARVAE = auto()
        DRONES = auto()
        SUPPLY = auto()
        EXPOS = auto()
        CORRUPTORS = auto()
        HYDRALISKS = auto()
        OVERLORDS = auto()
        ZERGLINGS = auto()
        SWARMHOSTS = auto()
        ROACHES = auto()
        GEYSERS = auto()
        BANELINGNESTS = auto()
        HATCHERIES = auto()
        EVOLUTIONCHAMBERS = auto()
        HYDRALISKDENS = auto()
        INFESTATIONPITS = auto()
        LURKERDENMPS = auto()
        NYDUSNETWORKS = auto()
        ROACHWARRENS = auto()
        SPAWNINGPOOLS = auto()
        SPIRES = auto()
        ULTRALISKCAVERNS = auto()
        OVERSEER50S = auto()

    zero_resources = dict((res, 0) for res in Resource)  # always .copy()
    claimed = []  # of (typ, resources, importance, expiration)
    resource_cost = {}  # per typ: resource
    resource_now_amount = {}  # in step init. Per resource, the amount.
    resource_of_buildingtype = {}  # match for upgrade buildings

    def init_resources(self):
        self.init_resource_of_buildingtype()
        #
        self.resource_cost = {}
        for typ in self.all_types:
            if typ not in self.all_eggtypes:
                creator = self.creator[typ]
                resources = self.zero_resources.copy()
                if typ not in {UnitTypeId.LARVA, UnitTypeId.EXTRACTORRICH, UnitTypeId.BROODLING}:
                    if typ not in self.all_changelings:
                        cost = self.calculate_cost(typ)
                        resources[self.Resource.MINERALS] = cost.minerals
                        resources[self.Resource.VESPENE] = cost.vespene
                if creator == UnitTypeId.HATCHERY:
                    resources[self.Resource.HATCHERIES] = 1
                if typ in {UnitTypeId.OVERLORD, UnitTypeId.DRONE}:
                    resources[self.Resource.LARVAE] = 1
                if typ in self.all_armytypes:
                    if creator == UnitTypeId.LARVA:
                        resources[self.Resource.LARVAE] = 1
                if typ in self.all_structuretypes:
                    if creator == UnitTypeId.DRONE:
                        resources[self.Resource.DRONES] = 1
                if typ == UnitTypeId.DRONE:
                    resources[self.Resource.SUPPLY] = 1
                if typ in self.all_armytypes:
                    resources[self.Resource.SUPPLY] = self.calculate_supply_cost(typ)  # morph supply cost
                if typ in self.all_upgrades:
                    resource = self.resource_of_buildingtype[creator]
                    resources[resource] = 1
                if typ == UnitTypeId.HATCHERY:
                    resources[self.Resource.EXPOS] = 1
                if typ == UnitTypeId.EXTRACTOR:
                    resources[self.Resource.GEYSERS] = 1
                if typ == UnitTypeId.BROODLORD:
                    resources[self.Resource.CORRUPTORS] = 1
                if creator == UnitTypeId.SPIRE:
                    resources[self.Resource.SPIRES] = 1
                if typ == UnitTypeId.LURKERMP:
                    resources[self.Resource.HYDRALISKS] = 1
                if creator == UnitTypeId.OVERLORD:
                    resources[self.Resource.OVERLORDS] = 1
                if creator == UnitTypeId.ZERGLING:
                    resources[self.Resource.ZERGLINGS] = 1
                if creator == UnitTypeId.SWARMHOSTMP:
                    resources[self.Resource.SWARMHOSTS] = 1
                if creator == UnitTypeId.NYDUSNETWORK:
                    resources[self.Resource.NYDUSNETWORKS] = 1
                if creator == UnitTypeId.ROACH:
                    resources[self.Resource.ROACHES] = 1
                if creator == UnitTypeId.OVERSEER:
                    resources[self.Resource.OVERSEER50S] = 1
                #
                self.resource_cost[typ] = resources
        # logger.info(self.resource_cost[UnitTypeId.GREATERSPIRE])
        self.zero_groupclaim()

    async def calc_resource_now(self):
        self.resource_now_tags = {}
        for res in self.Resource:
            self.resource_now_tags[res] = set()
        #
        for lar in self.larva:
            self.resource_now_tags[self.Resource.LARVAE].add(lar.tag)
        # drones may idle or be busy, but not build
        for unt in self.units(UnitTypeId.DRONE):
            if self.job_of_unit(unt) in [Job.WALKER, Job.BUILDER]:
                if self.frame >= self.listenframe_of_unit[unt.tag]:
                    self.resource_now_tags[self.Resource.DRONES].add(unt.tag)
        for unt in self.units(UnitTypeId.CORRUPTOR).idle:
            if self.job_of_unit(unt) == Job.DEFENDATTACK:
                if self.frame >= self.listenframe_of_unit[unt.tag]:
                    self.resource_now_tags[self.Resource.CORRUPTORS].add(unt.tag)
        for unt in self.units(UnitTypeId.HYDRALISK).idle:
            if self.job_of_unit(unt) == Job.DEFENDATTACK:
                if self.frame >= self.listenframe_of_unit[unt.tag]:
                    self.resource_now_tags[self.Resource.HYDRALISKS].add(unt.tag)
        for unt in self.units(UnitTypeId.OVERLORD):
            if self.job_of_unit(unt) != Job.CREEPLORD:
                if self.frame >= self.listenframe_of_unit[unt.tag]:
                    self.resource_now_tags[self.Resource.OVERLORDS].add(unt.tag)
        for unt in self.units(UnitTypeId.ZERGLING).idle:
            if self.job_of_unit(unt) == Job.DEFENDATTACK:
                if self.frame >= self.listenframe_of_unit[unt.tag]:
                    self.resource_now_tags[self.Resource.ZERGLINGS].add(unt.tag)
        for unt in self.units(UnitTypeId.SWARMHOSTMP).idle:  # here cooldown 43 sec?
            if self.frame >= self.listenframe_of_unit[unt.tag]:
                if unt.tag in self.cooldown_sh:
                    if self.frame >= self.cooldown_sh[unt.tag]:
                        self.resource_now_tags[self.Resource.SWARMHOSTS].add(unt.tag)
        for unt in self.units(UnitTypeId.ROACH).idle:
            if self.frame >= self.listenframe_of_unit[unt.tag]:
                self.resource_now_tags[self.Resource.ROACHES].add(unt.tag)
        for building in self.resource_of_buildingtype:
            resource = self.resource_of_buildingtype[building]
            for stru in self.structures(building).ready.idle:
                if self.frame >= self.listenframe_of_structure[stru.tag]:
                    self.resource_now_tags[resource].add(stru.tag)
        for ovi in self.units(UnitTypeId.OVERSEER):
            if self.frame >= self.listenframe_of_unit[ovi.tag]:
                if ovi.energy >= 50:
                    self.resource_now_tags[self.Resource.OVERSEER50S].add(ovi.tag)
        # resource_now_amount
        self.resource_now_amount = {}
        for res in self.Resource:
            if res in self.resource_now_tags:
                self.resource_now_amount[res] = len(self.resource_now_tags[res])
        self.resource_now_amount[self.Resource.MINERALS] = self.minerals
        self.resource_now_amount[self.Resource.VESPENE] = self.vespene
        self.resource_now_amount[self.Resource.SUPPLY] = self.supply_left
        self.resource_now_amount[self.Resource.EXPOS] = len(self.freeexpos)
        self.resource_now_amount[self.Resource.GEYSERS] = len(self.freegeysers)

    def resourcetags(self, typ):  # -> set of tags
        tagsset = set()
        typresources = self.resource_cost[typ]
        for res in self.Resource:
            if typresources[res] > 0:
                tagsset |= self.resource_now_tags[res]
        return tagsset

    def zero_groupclaim(self):
        self.groupclaim = self.zero_resources.copy()

    def add_groupclaim(self, typ, amount):
        resources = self.resource_cost[typ]
        for res in self.Resource:
            self.groupclaim[res] += amount * resources[res]

    def claim_resources(self, typ, importance):
        resources = self.resource_cost[typ]
        expiration = self.frame + self.minutes
        claim = (typ, resources, importance, expiration)
        #
        # in claims?
        # the importance of a claim can be increased
        todel = []
        inclaims = False
        for hclaim in self.claims:
            (htyp, hresource, himportance, hexpiration) = hclaim
            if htyp == typ:
                if importance > himportance:
                    todel.append(hclaim)
                else:
                    inclaims = True
        if not inclaims:
            self.claims.append(claim)
        for hclaim in todel:
            del self.claims[self.claims.index(hclaim)]

    def check_resources(self, typ, importance) -> bool:
        resources = self.resource_cost[typ]
        #
        # in claims?
        inclaims = False
        claimindex = 0
        for (ix, hclaim) in enumerate(self.claims):
            (htyp, hresource, himportance, hexpiration) = hclaim
            if htyp == typ:
                inclaims = True
                claimindex = ix
        if inclaims:
            # claims with importance above mine
            vipclaimed = self.zero_resources.copy()
            for hclaim in self.claims:
                (htyp, hresources, himportance, hexpiration) = hclaim
                if himportance > importance:
                    for res in self.Resource:
                        vipclaimed[res] += hresources[res]
            # to pay now
            for hclaim in self.orderdelay:
                (htyp, hresources, himportance, hexpiration) = hclaim
                for res in self.Resource:
                    vipclaimed[res] += hresources[res]
            # groupclaim at importance 700
            if importance < 700:
                for res in self.Resource:
                    vipclaimed[res] += self.groupclaim[res]
            #
            # build now?
            buildnow = True
            if self.tech_requirement_progress(typ) < 1:
                if typ == self.example:
                    logger.info("example lacking tech")
                buildnow = False
            for res in self.Resource:
                myres = resources[res]
                if myres > 0:
                    vipres = vipclaimed[res]
                    nowres = self.resource_now_amount[res]
                    if nowres < vipres + myres:
                        if typ == self.example:
                            logger.info("example lacking " + res.name)
                        buildnow = False
            #
            if buildnow:
                if typ == self.example:
                    logger.info("example has resources")
                return True
            else:
                return False
        else:
            return False

    def spend_resources(self, typ):
        # call after check_resources, if you are going to order build
        # should be in claims
        inclaims = False
        claimindex = 0
        for (ix, hclaim) in enumerate(self.claims):
            (htyp, hresource, himportance, hexpiration) = hclaim
            if htyp == typ:
                inclaims = True
                claimindex = ix
        if inclaims:
            (htyp, resources, importance, expiration) = self.claims[claimindex]
            del self.claims[claimindex]
            short = self.frame + self.seconds
            long = self.frame + 10 * self.seconds
            if typ in self.all_structuretypes:
                self.orderdelay.append((typ, resources, importance, long))
            else:
                self.orderdelay.append((typ, resources, importance, short))

    def unclaim_resources(self, typ):
        logger.info("Making a " + typ.name)
        lex = 9999999
        expiration = self.frame + 5
        for hclaim in self.orderdelay:
            (htyp, hresources, himportance, hexpiration) = hclaim
            if (htyp == typ) and (expiration < hexpiration < lex):
                lex = hexpiration
                old_claim = hclaim
                new_claim = (htyp, hresources, himportance, expiration)
        if lex < 9999999:
            self.orderdelay[self.orderdelay.index(old_claim)] = new_claim

    def have_free_resource(self, res, importance) -> bool:
        # use if you want to check whether you want to claim
        amfree = self.resource_now_amount[res]
        # claims (with importance atleast mine)
        vipclaimed = 0
        for hclaim in self.claims:
            (htyp, hresources, himportance, hexpiration) = hclaim
            if himportance >= importance:
                vipclaimed += hresources[res]
        amfree -= vipclaimed
        # to pay now
        spent = 0
        for hclaim in self.orderdelay:
            (htyp, hresources, himportance, hexpiration) = hclaim
            spent += hresources[res]
        amfree -= spent
        # groupclaim
        if importance < 700:
            amfree -= self.groupclaim[res]
        return amfree > 0

    def mineral_gap(self, typ) -> int:
        # typ should be in claims
        res = self.Resource.MINERALS
        importance = 99999
        need = True
        for hclaim in self.claims:
            (htyp, hresources, himportance, hexpiration) = hclaim
            if htyp == typ:
                importance = himportance
                need = hresources[res] > 0
        if not need:
            return 0
        amfree = self.resource_now_amount[res]
        # claims (with importance atleast mine)
        vipclaimed = 0
        for hclaim in self.claims:
            (htyp, hresources, himportance, hexpiration) = hclaim
            if himportance >= importance:
                vipclaimed += hresources[res]
        amfree -= vipclaimed
        # to pay now
        spent = 0
        for hclaim in self.orderdelay:
            (htyp, hresources, himportance, hexpiration) = hclaim
            spent += hresources[res]
        amfree -= spent
        # groupclaim
        if importance < 700:
            amfree -= self.groupclaim[res]
        return -amfree

    def vespene_gap(self, typ) -> int:
        # typ should be in claims
        res = self.Resource.VESPENE
        importance = 99999
        need = True
        for hclaim in self.claims:
            (htyp, hresources, himportance, hexpiration) = hclaim
            if htyp == typ:
                importance = himportance
                need = hresources[res] > 0
        if not need:
            return 0
        amfree = self.resource_now_amount[res]
        # claims (with importance atleast mine)
        vipclaimed = 0
        for hclaim in self.claims:
            (htyp, hresources, himportance, hexpiration) = hclaim
            if himportance >= importance:
                vipclaimed += hresources[res]
        amfree -= vipclaimed
        # to pay now
        spent = 0
        for hclaim in self.orderdelay:
            (htyp, hresources, himportance, hexpiration) = hclaim
            spent += hresources[res]
        amfree -= spent
        # groupclaim
        if importance < 700:
            amfree -= self.groupclaim[res]
        return -amfree

    async def claim_administration(self):
        # delete outdated info
        # often, expensive content.
        todel = []
        show = "claims: "
        for claim in self.claims:
            (typ, resources, importance, expiration) = claim
            show += typ.name + " "
            if self.frame >= expiration:
                todel.append(claim)
        for claim in todel:
            del self.claims[self.claims.index(claim)]
        todel = []
        for claim in self.orderdelay:
            (typ, resources, importance, expiration) = claim
            show += "(" + typ.name + ") "
            if self.frame >= expiration:
                todel.append(claim)
        for claim in todel:
            del self.orderdelay[self.orderdelay.index(claim)]
        # logger.info(show)

    def init_resource_of_buildingtype(self):
        # for upgrades
        self.resource_of_buildingtype[UnitTypeId.BANELINGNEST] = self.Resource.BANELINGNESTS
        self.resource_of_buildingtype[UnitTypeId.HATCHERY] = self.Resource.HATCHERIES
        self.resource_of_buildingtype[UnitTypeId.EVOLUTIONCHAMBER] = self.Resource.EVOLUTIONCHAMBERS
        self.resource_of_buildingtype[UnitTypeId.HYDRALISKDEN] = self.Resource.HYDRALISKDENS
        self.resource_of_buildingtype[UnitTypeId.INFESTATIONPIT] = self.Resource.INFESTATIONPITS
        self.resource_of_buildingtype[UnitTypeId.LURKERDENMP] = self.Resource.LURKERDENMPS
        self.resource_of_buildingtype[UnitTypeId.NYDUSNETWORK] = self.Resource.NYDUSNETWORKS
        self.resource_of_buildingtype[UnitTypeId.ROACHWARREN] = self.Resource.ROACHWARRENS
        self.resource_of_buildingtype[UnitTypeId.SPAWNINGPOOL] = self.Resource.SPAWNINGPOOLS
        self.resource_of_buildingtype[UnitTypeId.SPIRE] = self.Resource.SPIRES
        self.resource_of_buildingtype[UnitTypeId.ULTRALISKCAVERN] = self.Resource.ULTRALISKCAVERNS
