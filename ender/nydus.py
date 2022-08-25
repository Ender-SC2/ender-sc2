# nydus.py, Ender

from loguru import logger
from enum import Enum, auto

from ender.common import Common
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from ender.utils.point_utils import distance


class Nytravel(Enum):
    PLANNED = auto()
    TOWARDS = auto()
    SUCCED = auto()
    IN = auto()
    SPIT = auto()


class Nydus(Common):

    __did_step0 = False
    #
    nydus_ports = set()  # Ready canals and networks. Multiframe units so use only position and tag.
    future_nydus_ports = set()  # same, but need not be ready.
    nydus_ports_hash = 0  # detect changes
    nydus_in_tag = {}  # per unittag: tag of a nydus_port
    nydus_out_tag = {}  # per unittag: tag of a nydus_port
    nydees = {}  # per unittag the Nytravel
    # nydees also have an attackgoal
    nydus_queue = []  # unittags in fifo order. For nydees Nytravel.SUCCED or Nytravel.IN or Nytravel.SPIT

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
            self.future_nydus_ports = self.structures(UnitTypeId.NYDUSNETWORK) | self.structures(UnitTypeId.NYDUSCANAL)
            ports = self.structures(UnitTypeId.NYDUSNETWORK).ready | self.structures(UnitTypeId.NYDUSCANAL).ready
            ports_hash = 0
            for port in ports:
                ports_hash += port.position.x
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
                    del self.nydus_in_tag[tag]
                    del self.nydus_out_tag[tag]
                    for unt in self.units:
                        if unt.tag == tag:
                            self.attack_via_nydus(unt)

    async def do_nydus(self):
        if len(self.future_nydus_ports) == 0:
            # loose all passengers
            self.nydus_queue = []
            self.nydees = []
            self.nydus_in_tag = {}
            self.nydus_out_tag = {}
        if len(self.future_nydus_ports) >= 2:
            for tag in self.nydees:
                if self.nydees[tag] == Nytravel.SUCCED:
                    if tag not in self.living:
                        self.nydees[tag] == Nytravel.IN
            if len(self.nydus_queue) > 0:
                tag = self.nydus_queue[0]
                if self.nydees[tag] == Nytravel.IN:
                    ntotag = self.nydus_out_tag[tag]
                    if self.frame >= self.listenframe_of_unit[ntotag]:
                        for port in self.nydus_ports:
                            if port.tag == ntotag:
                                self.nydees[tag] = Nytravel.SPIT
                                port(AbilityId.SMART)  # out
                                self.listenframe_of_unit[ntotag] = self.frame + 0.9 * self.seconds
                                self.listenframe_of_unit[tag] = self.frame + 5
                        seen = False
                        for port in self.future_nydus_ports:
                            if port.tag == ntotag:
                                seen = True
                        if not seen:
                            # repair for a lost port
                            goal = self.attack_goal[tag]
                            # len(self.nydus_ports) >= 2
                            distbb = 99999
                            for nydus in self.future_nydus_ports:
                                dist = distance(nydus, goal)
                                if dist < distbb:
                                    distbb = dist
                                    nydus_out = nydus
                            if distbb < 99999:
                                self.nydus_out_tag[tag] = nydus_out.tag
            for unt in self.units:
                tag = unt.tag
                if tag in self.nydees:
                    pos = unt.position
                    goal = self.attack_goal[tag]
                    stat = self.nydees[tag]
                    nydus_in_tag = self.nydus_in_tag[tag]
                    if stat == Nytravel.PLANNED:
                        if self.frame > self.listenframe_of_unit[tag]:
                            for port in self.future_nydus_ports:
                                if port.tag == nydus_in_tag:
                                    unt.attack(port.position)
                                    self.nydees[tag] = Nytravel.TOWARDS
                                    self.listenframe_of_unit[tag] = self.frame + 5
                    elif stat == Nytravel.TOWARDS:
                        if self.frame >= self.listenframe_of_unit[nydus_in_tag]:
                            for port in self.nydus_ports:
                                if port.tag == nydus_in_tag:
                                    margin = 0.2
                                    if distance(pos, port.position) < 1.5 + unt.radius + margin:
                                        self.nydees[tag] = Nytravel.SUCCED
                                        port(AbilityId.LOAD_NYDUSNETWORK, unt)
                                        self.nydus_queue.append(tag)
                                        self.listenframe_of_unit[nydus_in_tag] = self.frame + 0.18 * self.seconds
                    elif stat == Nytravel.SPIT:
                        if self.frame > self.listenframe_of_unit[tag]:
                            unt.attack(goal)
                            del self.nydees[tag]
                            del self.nydus_in_tag[tag]
                            del self.nydus_out_tag[tag]
                            del self.nydus_queue[self.nydus_queue.index(tag)]  # usually 0
                            self.listenframe_of_unit[tag] = self.frame + 5
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
        pos = unt.position
        goal = self.attack_goal[tag]
        nyd = len(self.future_nydus_ports) >= 2
        if unt.is_flying:
            nyd = False
        if unt.type_id in self.all_changelings:
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
                self.nydus_in_tag[tag] = nydus_in.tag
                self.nydus_out_tag[tag] = nydus_out.tag
            else:
                unt.attack(goal)
        else:
            unt.attack(goal)
