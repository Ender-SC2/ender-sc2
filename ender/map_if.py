# map_if.py, Ender

from enum import Enum, auto

import numpy
from loguru import logger

from ender.common import Common
from ender.rocks_if import Rocks_if
from sc2.position import Point2


class Map_if(Common):

    __did_step0 = False

    class Mapcolor(Enum):
        OUT = auto()
        FLY = auto()  # can fly but not walk
        STAND = auto()  # can stand but not build
        FREE = auto()  # can build, walk or fly, creep
        NOCREEP = auto()  # can build, walk, fly, not creep
        BUILT = auto()  # my or neutral or enemy building
        PLAN = auto()  # reserved, overwriting free
        GAS = auto()  # geyser without building

    map = None
    plans = set()  # of (pos, size, expiration, oldcolor)
    drawings = set()  # of (pos, size, typ) to enable erasing if not in self.structures
    _last_structures_hash = 0  # to react on changes
    enemy_drawings = set()  # of (pos, size, typ) to enable erasing if not in self.enemy_struc_mem
    _last_enemy_struc_mem_hash = 0  # to react on changes
    plan_timeout = 0
    gaspositions = set()
    #

    def __step0(self):
        self.plan_timeout = 3 * self.minutes
        self.map = numpy.ndarray(shape=(200, 200), dtype=self.Mapcolor)
        for right in range(200):
            for up in range(200):
                if (self.map_left <= right < self.map_right) and (self.map_bottom <= up < self.map_top):
                    point = Point2((right, up))
                    if self.game_info.pathing_grid[point] == 0:
                        self.map[right, up] = self.Mapcolor.FLY
                    else:
                        if self.game_info.placement_grid[point] == 0:
                            self.map[right, up] = self.Mapcolor.STAND
                        else:
                            self.map[right, up] = self.Mapcolor.FREE
                else:
                    self.map[right, up] = self.Mapcolor.OUT
        self._prebuilt()

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        if not self.did_map_onstep:
            self.did_map_onstep = True
            await self.map_administration()
            #

    def map_grid(self, pos, size) -> Point2:
        if size % 2 == 0:
            res = Point2((round(pos.x), round(pos.y)))
        else:
            res = Point2((round(pos.x - 0.5) + 0.5, round(pos.y - 0.5) + 0.5))
        return res

    def map_around(self, pos, size) -> Point2:
        point = self.map_grid(pos, size)
        ok = self.map_can_plan(point, size)
        radius = 0
        dx = 0
        dy = 0
        center = point
        while not ok:
            dx += 1
            if dx > radius:
                dy += 1
                dx = -radius
                if dy > radius:
                    radius += 1
                    dy = -radius
                    dx = -radius
                    if radius == 25:
                        logger.error("hanging in around()")
            point = Point2((center.x + dx, center.y + dy))
            ok = self.map_can_plan(point, size)
        return point

    def map_can_plan_creep(self, pos, size) -> bool:
        # Call with half-pos when size is odd.
        can = True
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                can = can and (self.read_map(px, py) == self.Mapcolor.FREE)
        return can

    def map_can_plan(self, pos, size) -> bool:
        # Call with half-pos when size is odd.
        can = True
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                can = can and (self.read_map(px, py) in {self.Mapcolor.FREE, self.Mapcolor.NOCREEP})
        return can

    def map_can_plan_gas(self, pos, size) -> bool:
        # Call with half-pos when size is odd.
        can = True
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                can = can and (self.read_map(px, py) == self.Mapcolor.GAS)
        return can

    def map_nocreep(self, pos, size):
        # Call with half-pos when size is odd.
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                if self.map[px, py] == self.Mapcolor.FREE:
                    self.map[px, py] = self.Mapcolor.NOCREEP

    def map_plan(self, pos, size):
        # Call with half-pos when size is odd.
        disx = size / 2
        disy = size / 2
        oldcolor = self.Mapcolor.FREE
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                if self.map[px, py] in {self.Mapcolor.FREE, self.Mapcolor.NOCREEP}:
                    oldcolor = self.map[px, py]
                    self.map[px, py] = self.Mapcolor.PLAN
        self.plans.add((pos, size, self.frame + self.plan_timeout, oldcolor))

    def map_plan_gas(self, pos, size):
        # Call with half-pos when size is odd.
        disx = size / 2
        disy = size / 2
        oldcolor = self.Mapcolor.GAS
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                if self.map[px, py] == oldcolor:
                    self.map[px, py] = self.Mapcolor.PLAN
        self.plans.add((pos, size, self.frame + self.plan_timeout, oldcolor))

    def map_can_build(self, pos, size) -> bool:
        # Call with half-pos when size is odd.
        can = True
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                can = can and (self.map[px, py] == self.Mapcolor.PLAN)
        return can

    def map_build(self, pos, size, typ):
        # Call with half-pos when size is odd.
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                self.map[px, py] = self.Mapcolor.BUILT
                self.drawings.add((pos, size, typ))

    def map_build_nodel(self, pos, size):
        # Call with half-pos when size is odd.
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                self.map[px, py] = self.Mapcolor.BUILT

    def map_enemy_build(self, pos, size, typ):
        # Call with half-pos when size is odd.
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                self.map[px, py] = self.Mapcolor.BUILT
                self.enemy_drawings.add((pos, size, typ))

    def map_unbuild(self, pos, size):
        # Call with half-pos when size is odd.
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                if self.map[px, py] == self.Mapcolor.BUILT:
                    self.map[px, py] = self.Mapcolor.FREE

    def map_unbuild_gas(self, pos, size):
        # Call with half-pos when size is odd.
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                if self.map[px, py] == self.Mapcolor.BUILT:
                    self.map[px, py] = self.Mapcolor.GAS

    def read_map(self, px, py) -> Mapcolor:
        if (self.map_left <= px < self.map_right) and (self.map_bottom <= py < self.map_top):
            return self.map[px, py]
        else:
            return self.Mapcolor.OUT

    # ---------- private ---------
    def map_unplan(self, pos, size, oldcolor):
        # Call with half-pos when size is odd.
        # called by map_administration when a plan expires
        disx = size / 2
        disy = size / 2
        for tx in range(0, size):
            px = round(pos.x + tx - disx)
            for ty in range(0, size):
                py = round(pos.y + ty - disy)
                if self.map[px, py] == self.Mapcolor.PLAN:
                    self.map[px, py] = oldcolor

    def _prebuilt(self):
        for mim in self.mineral_field:
            mimpos = mim.position
            # mimpos always x whole, y half
            self.map[round(mimpos.x - 1), round(mimpos.y - 0.5)] = self.Mapcolor.BUILT
            self.map[round(mimpos.x + 0), round(mimpos.y - 0.5)] = self.Mapcolor.BUILT
        for gas in self.vespene_geyser:
            self._create_block_gas(gas.position, (3, 3))
            self.gaspositions.add(gas.position)
        for tow in self.watchtowers:
            self._create_block(tow.position, (2, 2))
        for anyu in self.all_units:
            if anyu.name.find("Inhibitor") >= 0:
                gridpos = Point2((round(anyu.position.x + 0.5) - 0.5, round(anyu.position.y + 0.5) - 0.5))
                # print(self.txt(gridpos))
                self.map[round(gridpos.x - 0.5), round(gridpos.y - 0.5)] = self.Mapcolor.BUILT
        for rock in self.destructables:  # copied from Sharpy
            rock_type = rock.type_id
            if rock.name == "MineralField450":
                # Attempts to solve the issue with sc2 linux 4.10 vs Windows 4.11
                self._create_rockblock(rock.position, (2, 1))
            elif rock_type in Rocks_if.unbuildable_rocks:
                self._create_unbuildable(rock.position)
            elif rock_type in Rocks_if.breakable_rocks_2x2:
                self._create_rockblock(rock.position, (2, 2))
            elif rock_type in Rocks_if.breakable_rocks_4x4:
                self._create_rockblock(rock.position, (4, 3))
                self._create_rockblock(rock.position, (3, 4))
            elif rock_type in Rocks_if.breakable_rocks_6x6:
                self._create_rockblock(rock.position, (6, 4))
                self._create_rockblock(rock.position, (5, 5))
                self._create_rockblock(rock.position, (4, 6))
            elif rock_type in Rocks_if.breakable_rocks_4x2:
                self._create_rockblock(rock.position, (4, 2))
            elif rock_type in Rocks_if.breakable_rocks_2x4:
                self._create_rockblock(rock.position, (2, 4))
            elif rock_type in Rocks_if.breakable_rocks_6x2:
                self._create_rockblock(rock.position, (6, 2))
            elif rock_type in Rocks_if.breakable_rocks_2x6:
                self._create_rockblock(rock.position, (2, 6))
            elif rock_type in Rocks_if.breakable_rocks_diag_BLUR:
                for y in range(-4, 6):
                    if y == -4:
                        self._create_rockblock(rock.position + Point2((y + 2, y)), (1, 1))
                    elif y == 5:
                        self._create_rockblock(rock.position + Point2((y - 2, y)), (1, 1))
                    elif y == -3:
                        self._create_rockblock(rock.position + Point2((y - 1, y)), (3, 1))
                    elif y == 4:
                        self._create_rockblock(rock.position + Point2((y + 1, y)), (3, 1))
                    else:
                        self._create_rockblock(rock.position + Point2((y, y)), (5, 1))
            elif rock_type in Rocks_if.breakable_rocks_diag_ULBR:
                for y in range(-4, 6):
                    if y == -4:
                        self._create_rockblock(rock.position + Point2((-y - 2, y)), (1, 1))
                    elif y == 5:
                        self._create_rockblock(rock.position + Point2((-y + 2, y)), (1, 1))
                    elif y == -3:
                        self._create_rockblock(rock.position + Point2((-y + 1, y)), (3, 1))
                    elif y == 4:
                        self._create_rockblock(rock.position + Point2((-y - 1, y)), (3, 1))
                    else:
                        self._create_rockblock(rock.position + Point2((-y, y)), (5, 1))

    def _create_rockblock(self, pos, measure):
        # Integer pos. Called with odd as well as with even measure.
        disx = measure[0] - (measure[0] // 2)
        disy = measure[1] - (measure[1] // 2)
        for tx in range(0, measure[0]):
            px = round(pos.x + tx - disx)
            for ty in range(0, measure[1]):
                py = round(pos.y + ty - disy)
                self.map[px, py] = self.Mapcolor.BUILT

    def _create_unbuildable(self, pos):
        for tx in range(0, 2):
            px = round(pos.x + tx - 1)
            for ty in range(0, 2):
                py = round(pos.y + ty - 1)
                self.map[px, py] = self.Mapcolor.STAND

    def _create_block(self, pos, measure):
        # Call with half-pos when measure is odd.
        disx = measure[0] / 2
        disy = measure[1] / 2
        for tx in range(0, measure[0]):
            px = round(pos.x + tx - disx)
            for ty in range(0, measure[1]):
                py = round(pos.y + ty - disy)
                self.map[px, py] = self.Mapcolor.BUILT

    def _create_block_gas(self, pos, measure):
        # Call with half-pos when measure is odd.
        disx = measure[0] / 2
        disy = measure[1] / 2
        for tx in range(0, measure[0]):
            px = round(pos.x + tx - disx)
            for ty in range(0, measure[1]):
                py = round(pos.y + ty - disy)
                self.map[px, py] = self.Mapcolor.GAS

    async def map_administration(self):
        # delete outdated info
        if self.frame % 13 == 12:  # rarely
            # plans
            todel = set()
            for cons in self.plans:
                (position, size, expiration, oldcolor) = cons
                if self.frame >= expiration:
                    todel.add(cons)
                    self.map_unplan(position, size, oldcolor)
                    logger.info("outdated plan " + str(size) + " at " + str(position.x) + "," + str(position.y))
            self.plans -= todel
            # drawings
            if self.structures_hash != self._last_structures_hash:
                self._last_structures_hash = self.structures_hash
                todel = set()
                for cons in self.drawings:
                    (position, size, typ) = cons
                    seen = False
                    for stru in self.structures(typ):
                        if stru.position == position:
                            seen = True
                    if not seen:
                        todel.add(cons)
                for cons in todel:
                    self.drawings.remove(cons)
                    (position, size, typ) = cons
                    if position in self.gaspositions:
                        self.map_unbuild_gas(position, size)
                    else:
                        self.map_unbuild(position, size)
            if self.enemy_struc_mem_hash != self._last_enemy_struc_mem_hash:
                self._last_enemy_struc_mem_hash = self.enemy_struc_mem_hash
                todel = set()
                for cons in self.enemy_drawings:
                    (position, size, typ) = cons
                    seen = False
                    for postag in self.enemy_struc_mem:
                        (strutyp, struposition) = self.enemy_struc_mem[postag]
                        if (struposition == position) and (strutyp == typ):
                            seen = True
                    if not seen:
                        todel.add(cons)
                for cons in todel:
                    self.enemy_drawings.remove(cons)
                    (position, size, typ) = cons
                    if position in self.gaspositions:
                        self.map_unbuild_gas(position, size)
                    else:
                        self.map_unbuild(position, size)
                # draw enemy buildings
                for postag in self.enemy_struc_mem:
                    (typ, position) = self.enemy_struc_mem[postag]
                    size = self.size_of_structure[typ]
                    cons = (position, size, typ)
                    if cons not in self.enemy_drawings:
                        self.map_enemy_build(position, size, typ)
