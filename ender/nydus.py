# nydus.py, Ender

from enum import Enum, auto

from loguru import logger

from ender.common import Common
from ender.job import Job
from ender.utils.point_utils import distance
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class Nytravel(Enum):
    PLANNED = auto()
    TOWARDS = auto()
    SUCCED = auto()
    IN = auto()
    SPIT = auto()


class Nydus(Common):

    __did_step0 = False
    #
    attackgoal = {}  # for units pointattacking, where it is going
    nydus_ports: Units  # Ready canals and networks. Multiframe units so use only position and tag.
    future_nydus_ports: Units  # same, but need not be ready.
    nydus_ports_hash = 0  # detect changes
    nydus_in_tag = {}  # per unittag: tag of a nydus_port
    nydus_out_tag = {}  # per unittag: tag of a nydus_port
    nydees = {}  # per unittag the Nytravel
    # nydees also have an attackgoal
    nydees_typ = {}  # per unittag, if in nydees, store the type_id
    nydus_queue = []  # unittags in fifo order. For nydees Nytravel.SUCCED or Nytravel.IN or Nytravel.SPIT
    now_spitting = False  # an unload_all command is given
    now_spitter = None  # the nydusport that is the exit (if now_spitting)

    def __step0(self):
        pass

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        await self.check_ports()
        await self.do_nydus()

    async def check_ports(self):
        if self.function_listens("check_ports", 10):
            self.future_nydus_ports = self.structures.of_type(UnitTypeId.NYDUSNETWORK) | self.structures.of_type(
                UnitTypeId.NYDUSCANAL
            )
            ports = (
                self.structures.of_type(UnitTypeId.NYDUSNETWORK).ready
                | self.structures.of_type(UnitTypeId.NYDUSCANAL).ready
            )
            ports_hash = 0
            for port in ports:
                ports_hash += port.tag
            if self.nydus_ports_hash != ports_hash:
                self.nydus_ports_hash = ports_hash
                self.nydus_ports = ports
                # change triggered actions:
                todel = set()
                for tag in self.nydees:
                    phase = self.nydees[tag]
                    if phase in [
                        Nytravel.PLANNED,
                        Nytravel.TOWARDS,
                        Nytravel.SUCCED,
                    ]:
                        nita = self.nydus_in_tag[tag]
                        seen = False
                        for port in self.future_nydus_ports:
                            if nita == port.tag:
                                seen = True
                        if not seen:
                            todel.add(tag)
                for tag in todel:
                    del self.nydees[tag]
                    del self.nydees_typ[tag]
                    del self.nydus_in_tag[tag]
                    del self.nydus_out_tag[tag]
                    for unt in self.units:
                        if unt.tag == tag:
                            self.attack_via_nydus(unt)

    async def do_nydus(self):
        ### log
        if len(self.nydees) > 0:
            stri = "nydees: "
            for tag in self.nydees:
                stri += self.nydees[tag].name + " "
            logger.info(stri)
        if len(self.nydus_queue) > 0:
            stri = "nydus_queue: "
            for tag in self.nydus_queue:
                if tag in self.nydees:
                    stri += self.nydees[tag].name + " "
                else:
                    stri += str(tag) + " "
                first = True
                for net in self.structures(UnitTypeId.NYDUSNETWORK):
                    if first:
                        first = False
                        if tag not in net.passengers_tags:
                            stri += "X  "
            logger.info(stri)
        ###
        if len(self.future_nydus_ports) == 0:
            # loose all passengers
            self.nydus_queue = []
            self.nydees = {}
            self.nydees_typ = {}
            self.nydus_in_tag = {}
            self.nydus_out_tag = {}
        if len(self.future_nydus_ports) == 1:
            # everybody out!
            porttag = self.future_nydus_ports[0].tag
            for tag in self.nydees:
                if self.nydees[tag] == Nytravel.IN:
                    self.nydus_out_tag[tag] = porttag
        if len(self.future_nydus_ports) >= 2:
            for tag in self.nydees:
                if self.nydees[tag] == Nytravel.SUCCED:
                    if tag not in self.living:
                        self.nydees[tag] = Nytravel.IN
            if len(self.nydus_queue) == 0:
                self.now_spitting = False
            else:  # there are units in the nydus_queue
                tag = self.nydus_queue[0]
                if self.nydees[tag] == Nytravel.IN:
                    ntotag = self.nydus_out_tag[tag]
                    if self.frame >= self.listenframe_of_structure[ntotag]:
                        if self.now_spitting:
                            for port in self.nydus_ports:
                                if port.tag == self.now_spitter:
                                    if self.now_spitter == ntotag:
                                        self.nydees[tag] = Nytravel.SPIT
                                        self.listenframe_of_unit[tag] = self.frame + 5
                                        # stop-ahead:
                                        if len(self.nydus_queue) >= 2:
                                            nexttag = self.nydus_queue[1]
                                            nextntotag = self.nydus_out_tag[nexttag]
                                            if self.now_spitter != nextntotag:
                                                port(AbilityId.STOP_STOP)
                                                self.now_spitting = False
                                                self.listenframe_of_structure[ntotag] = self.frame + 0.9 * self.seconds
                                        # somehow it halted
                                        if len(port.orders) == 0:
                                            if port.type_id == UnitTypeId.NYDUSNETWORK:
                                                port(AbilityId.UNLOADALL_NYDASNETWORK)  # no typo here
                                            else:
                                                port(AbilityId.UNLOADALL_NYDUSWORM)
                                            self.listenframe_of_structure[ntotag] = self.frame + 5
                                    else:  # wrong one spits
                                        port(AbilityId.STOP_STOP)
                                        self.now_spitting = False
                                        self.listenframe_of_structure[ntotag] = self.frame + 0.9 * self.seconds
                        else:  # not now_spitting
                            for port in self.nydus_ports:
                                if port.tag == ntotag:
                                    self.now_spitting = True
                                    self.now_spitter = ntotag
                                    if port.type_id == UnitTypeId.NYDUSNETWORK:
                                        port(AbilityId.UNLOADALL_NYDASNETWORK)  # no typo here
                                    else:
                                        port(AbilityId.UNLOADALL_NYDUSWORM)
                                    self.listenframe_of_structure[ntotag] = self.frame + 0.9 * self.seconds
                                    # next programloop, top unit may be out already
                                    self.nydees[tag] = Nytravel.SPIT
                                    self.listenframe_of_unit[tag] = self.frame + 5
                        seen = False
                        for port in self.future_nydus_ports:
                            if port.tag == ntotag:
                                seen = True
                        if not seen:
                            # repair for a lost port
                            goal = self.attackgoal[tag]
                            # len(self.nydus_ports) >= 2
                            distbb = 99999
                            for nydus in self.future_nydus_ports:
                                dist = distance(nydus.position, goal)
                                if dist < distbb:
                                    distbb = dist
                                    nydus_out = nydus
                            if distbb < 99999:
                                self.nydus_out_tag[tag] = nydus_out.tag
                elif self.nydees[tag] == Nytravel.SPIT:
                    if not self.now_spitting:
                        self.nydees[tag] == Nytravel.IN
            types = set()
            for tag in self.nydees_typ:
                types.add(self.nydees_typ[tag])
            for typ in types:
                for unt in self.units(typ):
                    tag = unt.tag
                    if tag in self.nydees:
                        pos = unt.position
                        goal = self.attackgoal[tag]
                        stat = self.nydees[tag]
                        nydus_in_tag = self.nydus_in_tag[tag]
                        if stat == Nytravel.PLANNED:
                            if self.frame > self.listenframe_of_unit[tag]:
                                for port in self.future_nydus_ports:
                                    if port.tag == nydus_in_tag:
                                        unt.attack(port.position)
                                        self.nydees[tag] = Nytravel.TOWARDS
                                        self.nydees_typ[tag] = typ
                                        self.listenframe_of_unit[tag] = self.frame + 5
                                        self.set_job_of_unittag(tag, Job.NYDUSUSER)
                        elif stat == Nytravel.TOWARDS:
                            if self.frame >= self.listenframe_of_structure[nydus_in_tag]:
                                for port in self.nydus_ports:
                                    if port.tag == nydus_in_tag:
                                        margin = 0.2
                                        if distance(pos, port.position) < 1.5 + unt.radius + margin:
                                            self.nydees[tag] = Nytravel.SUCCED
                                            if port.type_id == UnitTypeId.NYDUSNETWORK:
                                                port(AbilityId.LOAD_NYDUSNETWORK, unt)
                                            else:
                                                port(AbilityId.LOAD_NYDUSWORM, unt)
                                            self.nydus_queue.append(tag)
                                            self.listenframe_of_structure[nydus_in_tag] = (
                                                self.frame + 0.18 * self.seconds
                                            )
                                        else:  # not near port
                                            if len(unt.orders) == 0:
                                                unt.attack(port.position)
                                                self.listenframe_of_unit[tag] = self.frame + 5
                        elif stat == Nytravel.SPIT:
                            if self.frame > self.listenframe_of_unit[tag]:
                                unt.attack(goal)
                                del self.nydees[tag]
                                del self.nydees_typ[tag]
                                del self.nydus_in_tag[tag]
                                del self.nydus_out_tag[tag]
                                del self.nydus_queue[self.nydus_queue.index(tag)]  # usually 0
                                self.listenframe_of_unit[tag] = self.frame + 5
                                self.set_job_of_unittag(tag, Job.UNCLEAR)
                        elif stat == Nytravel.IN:
                            # Must be spit out of order. Repair.
                            amspit = 0
                            for atag in self.nydees:
                                if self.nydees[atag] == Nytravel.SPIT:
                                    amspit += 1
                                    spittag = atag
                            if amspit == 1:
                                self.nydees[spittag] = Nytravel.IN
                            self.nydees[tag] = Nytravel.SPIT

    def attack_via_nydus(self, unt):
        # attackgoal position must be set
        tag = unt.tag
        typ = unt.type_id
        pos = unt.position
        goal = self.attackgoal[tag]
        nyd = len(self.future_nydus_ports) >= 2
        if unt.is_flying:
            nyd = False
        if typ in self.all_changelings:
            nyd = False
        if nyd:
            distland = distance(pos, goal)
            distaa = 99999
            for nydus in self.future_nydus_ports:
                dist = distance(pos, nydus.position)
                if dist < distaa:
                    distaa = dist
                    nydus_in = nydus
            distbb = 99999
            for nydus in self.future_nydus_ports:
                dist = distance(nydus.position, goal)
                if dist < distbb:
                    distbb = dist
                    nydus_out = nydus
            # in next line, distance 5 estimates nydusloadtime distance
            if distaa + distbb + 5 < distland:
                # travel via nydus
                self.nydees[tag] = Nytravel.PLANNED
                self.nydees_typ[tag] = typ
                self.nydus_in_tag[tag] = nydus_in.tag
                self.nydus_out_tag[tag] = nydus_out.tag
            else:
                unt.attack(goal)
        else:
            unt.attack(goal)
