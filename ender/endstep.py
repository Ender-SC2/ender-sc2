# endstep.py, Merkbot, Zerg sandbox bot
# 20 may 2022

from ender.common import Common


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
        
    
