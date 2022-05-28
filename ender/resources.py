# resources.py, Ender

from enum import Enum, auto

import sc2
from ender.tech import Tech
from sc2.ids.unit_typeid import UnitTypeId


class Resources(Tech):

    __did_step0 = False
    # a claim is needed to make a LAIR, as it needs money and a hatchery not making a queen.
    # claimtype = (typ,resources,importance,expiration)
    claims = [] # of claimtype. Typ will be unique.
    orderdelay = [] # of claimtype. The order has been given but did not arrive yet.
    example = UnitTypeId.EXTRACTOR

    def __step0(self):
        self.init_resources()

    async def on_step(self):
        await Tech.on_step(self)
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
        OVERSEERS = auto()
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
    zero_resources  = dict((res,0) for res in Resource) # always .copy()
    claimed = [] # of (typ, resources, importance, expiration)
    resource_cost = {} # per typ: resource
    resource_now = {} # in step init.
    resource_of_buildingtype = {} # match for upgrade buildings

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
                    resources[self.Resource.SUPPLY] = self.calculate_supply_cost(typ)
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
                if creator == UnitTypeId.OVERSEER:
                    resources[self.Resource.OVERSEERS] = 1
                if creator == UnitTypeId.SWARMHOSTMP:
                    resources[self.Resource.SWARMHOSTS] = 1
                if creator == UnitTypeId.NYDUSNETWORK:
                    resources[self.Resource.NYDUSNETWORKS] = 1
                if creator == UnitTypeId.ROACH:
                    resources[self.Resource.ROACHES] = 1
                #
                self.resource_cost[typ] = resources
        # print(self.resource_cost[UnitTypeId.GREATERSPIRE])

    async def calc_resource_now(self):
        self.resource_now = {}
        self.resource_now[self.Resource.MINERALS] = self.minerals
        self.resource_now[self.Resource.VESPENE] = self.vespene
        self.resource_now[self.Resource.LARVAE] = len(self.larva)
        # drones may idle but not build
        drones = 0
        for unt in self.units(UnitTypeId.DRONE):
            if self.job_of_unit[unt.tag] not in {self.Job.APPRENTICE, self.Job.WALKER, self.Job.BUILDER}:
                drones += 1
        self.resource_now[self.Resource.DRONES] = drones
        self.resource_now[self.Resource.SUPPLY] = self.supply_left
        self.resource_now[self.Resource.EXPOS] = len(self.freeexpos)
        self.resource_now[self.Resource.GEYSERS] = len(self.freegeysers)
        self.resource_now[self.Resource.CORRUPTORS] = len(self.units(UnitTypeId.CORRUPTOR).idle)
        self.resource_now[self.Resource.HYDRALISKS] = len(self.units(UnitTypeId.HYDRALISK).idle)
        self.resource_now[self.Resource.OVERLORDS] = len(self.units(UnitTypeId.OVERLORD).idle)
        lings = 0
        for unt in self.units(UnitTypeId.ZERGLING).idle:
            if self.job_of_unit[unt.tag] in {self.Job.UNCLEAR, self.Job.DEFENDATTACK}:
                lings += 1
        self.resource_now[self.Resource.ZERGLINGS] = lings
        self.resource_now[self.Resource.OVERSEERS] = len(self.units(UnitTypeId.OVERSEER).idle)
        self.resource_now[self.Resource.SWARMHOSTS] = len(self.units(UnitTypeId.SWARMHOSTMP).idle)
        self.resource_now[self.Resource.ROACHES] = len(self.units(UnitTypeId.ROACH).idle)
        for building in self.resource_of_buildingtype:
            resource = self.resource_of_buildingtype[building]
            self.resource_now[resource] = len(self.structures(building).ready.idle)

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
        for (ix,hclaim) in enumerate(self.claims):
            (htyp, hresource, himportance, hexpiration) = hclaim
            if htyp == typ:
                inclaims = True
                claimindex = ix
        if inclaims:
            # claims with importance above mine
            vipclaimed = self.zero_resources.copy() 
            for hclaim in self.claims:
                (htyp,hresources,himportance,hexpiration) = hclaim
                if himportance > importance:
                    for res in self.Resource:
                        vipclaimed[res] += hresources[res]
            # to pay now
            for hclaim in self.orderdelay:
                (htyp,hresources,himportance,hexpiration) = hclaim
                for res in self.Resource:
                    vipclaimed[res] += hresources[res]
            #
            # build now?
            buildnow = True
            if self.tech_requirement_progress(typ) < 1:
                if typ == self.example:
                    print('example lacking tech')
                buildnow = False
            for res in self.Resource:
                myres = resources[res]
                if myres > 0:
                    vipres = vipclaimed[res]
                    nowres = self.resource_now[res]
                    if (nowres < vipres + myres):
                        if typ == self.example:
                            print('example lacking ' + res.name)
                        buildnow = False
            #
            if buildnow:
                if typ == self.example:
                    print('example will build')
                del self.claims[claimindex]
                short = self.frame + self.seconds
                long = self.frame + self.minutes
                if typ in self.all_structuretypes:
                    self.orderdelay.append((typ,resources,importance,long))
                else:
                    self.orderdelay.append((typ,resources,importance,short))
                return True
            else:
                return False
        else:
            return False

    def unclaim_resources(self, typ):
        lex = 9999999
        expiration = self.frame + 5
        for hclaim in self.orderdelay:
            (htyp,hresources,himportance,hexpiration) = hclaim
            if (htyp == typ) and (expiration < hexpiration < lex):
                lex = hexpiration
                old_claim = hclaim
                new_claim = (htyp,hresources,himportance,expiration) 
        if lex < 9999999:
            self.orderdelay[self.orderdelay.index(old_claim)] = new_claim

    def have_free_resource(self, res, importance) -> bool:
        # use if you want to check whether you want to claim
        amfree = self.resource_now[res]
        # claims (with importance atleast mine)
        vipclaimed = 0 
        for hclaim in self.claims:
            (htyp,hresources,himportance,hexpiration) = hclaim
            if himportance >= importance:
                vipclaimed += hresources[res]
        amfree -= vipclaimed
        # to pay now
        spent = 0
        for hclaim in self.orderdelay:
            (htyp,hresources,himportance,hexpiration) = hclaim
            spent += hresources[res]
        amfree -= spent
        return (amfree > 0)

    def mineral_gap(self, typ) -> int:
        # typ should be in claims
        res = self.Resource.MINERALS
        importance = 99999
        for hclaim in self.claims:
            (htyp,hresources,himportance,hexpiration) = hclaim
            if htyp == typ:
                importance = himportance
        amfree = self.resource_now[res]
        # claims (with importance atleast mine)
        vipclaimed = 0 
        for hclaim in self.claims:
            (htyp,hresources,himportance,hexpiration) = hclaim
            if himportance >= importance:
                vipclaimed += hresources[res]
        amfree -= vipclaimed
        # to pay now
        spent = 0
        for hclaim in self.orderdelay:
            (htyp,hresources,himportance,hexpiration) = hclaim
            spent += hresources[res]
        amfree -= spent
        return - amfree
    
    def vespene_gap(self, typ) -> int:
        # typ should be in claims
        res = self.Resource.VESPENE
        importance = 99999
        for hclaim in self.claims:
            (htyp,hresources,himportance,hexpiration) = hclaim
            if htyp == typ:
                importance = himportance
        amfree = self.resource_now[res]
        # claims (with importance atleast mine)
        vipclaimed = 0 
        for hclaim in self.claims:
            (htyp,hresources,himportance,hexpiration) = hclaim
            if himportance >= importance:
                vipclaimed += hresources[res]
        amfree -= vipclaimed
        # to pay now
        spent = 0
        for hclaim in self.orderdelay:
            (htyp,hresources,himportance,hexpiration) = hclaim
            spent += hresources[res]
        amfree -= spent
        return - amfree
    
        
    async def claim_administration(self):
        # delete outdated info
        # often, expensive content.
        todel = []
        show = 'claims: '
        for claim in self.claims:
            (typ,resources,importance,expiration) = claim
            show += typ.name + ' '
            if self.frame >= expiration:
                todel.append(claim)
        for claim in todel:
            del self.claims[self.claims.index(claim)] 
        todel = []
        for claim in self.orderdelay:
            (typ,resources,importance,expiration) = claim
            show += '(' + typ.name + ') '
            if self.frame >= expiration:
                todel.append(claim)
        for claim in todel:
            del self.orderdelay[self.orderdelay.index(claim)] 
        # print(show)

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


