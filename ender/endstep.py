# endstep.py, Ender

from loguru import logger

from ender.common import Common
from sc2.ids.unit_typeid import UnitTypeId


class Endstep(Common):

    __did_step0 = False
    resign_frame = 999999

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
        # some criteria
        if len(self.units(UnitTypeId.DRONE)) < 4:
            if self.frame > 4 * self.minutes:
                self.resign = True
        health = 0
        for hatch in self.structures(UnitTypeId.HATCHERY):
            health = max(hatch.health, health)
        if health < 500:  # max / 3
            self.resign = True
        # resign handling
        if self.resign:
            if self.resign_frame == 999999:
                await self.client.chat_send("Resigning, gg", team_only=False)
                logger.info("Resigning, gg")
                self.resign_frame = self.frame + 6 * self.seconds
            if self.frame > self.resign_frame:
                await self.client.quit()
