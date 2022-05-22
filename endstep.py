# endstep.py, Merkbot, Zerg sandbox bot
# 20 may 2022
from common import Common
import sc2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.buff_id import BuffId
from sc2.position import Point2
from enum import Enum
from math import sqrt,cos,sin,pi,acos
import random

class Endstep(Common):

    __did_step0 = False

    def __step0(self):
        pass

    async def on_step(self):
        await Common.on_step(self)
        if not self.__did_step0:
            self.__step0()
            self.__did_step0 = True
        #
        # collect health for next step
        for myn in self.units:
            self.last_health[myn.tag] = myn.health
        for myn in self.structures:
            if myn.type_id not in self.all_tumortypes:
                self.last_health[myn.tag] = myn.health
        # last_living
        self.last_living = self.living
        
    
