# endstep.py, Merkbot, Zerg sandbox bot
# 25 may 2022
from loguru import logger

from ender.common import Common
from sc2.ids.unit_typeid import UnitTypeId
import sc2


class Endstep(Common):

    __did_step0 = False

    def __step0(self):
        pass

    async def on_step(self, iteration: int):
        await Common.on_step(self, iteration)
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
        #
        await self.may_resign()
        
    async def may_resign(self):
        resign = False
        if len(self.units(UnitTypeId.DRONE)) < 2:
            logger.info("Resign, too few workers")
            resign = True
        if resign:
            await self._client.quit()

