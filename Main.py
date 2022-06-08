# Main.py, Ender

import random

import sc2
from ender.attack import Attack
from ender.creep import Creep
from ender.endstep import Endstep
from ender.making import Making
from ender.parts import Parts
from ender.queens import Queens
from ender.mining import Mining
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer


#                          BotAI
#                            |
#                          Common
#                                       \
#                                        Tech
#                        /  |          /   \       \       \     \      \
#                  Attack Map_if Resources Strategy Queens Mining Parts Endstep
#                           |   \    |    /
#                         Creep   Making
#
#                       \   |       /            /      /      /     /
#
#                         Ender
#


class Ender(Attack, Creep, Making, Queens, Mining, Parts, Endstep):

    def __init__(self):
        super().__init__()

    async def on_step(self, iteration: int):
        self.did_common_onstep = False
        self.did_map_onstep = False
        self.did_tech_onstep = False
        self.iteration = iteration
        await Attack.on_step(self)
        await Creep.on_step(self)
        await Making.on_step(self)
        await Queens.on_step(self)
        await Mining.on_step(self)
        await Parts.on_step(self)
        await Endstep.on_step(self)


# *********************************************************************************************************************
def main():
    # Easy/Medium/Hard/VeryHard
    all_maps = ['BlackburnAIE', 'CuriousMindsAIE', '2000AtmospheresAIE', 'GlitteringAshesAIE', 'HardwireAIE',
                'BerlingradAIE']
    map = random.choice(all_maps)
    # TO TEST use next line
    # map = '2000AtmospheresAIE'
    opponentspecies = random.choice([Race.Terran, Race.Zerg, Race.Protoss])
    # TO TEST use next line
    # opponentspecies = Race.Terran
    # Easy/Medium/Hard/VeryHard
    run_game(sc2.maps.get(map), [
        Bot(Race.Zerg, Ender()),
        Computer(opponentspecies, Difficulty.VeryHard)
    ], realtime=False)


if __name__ == "__main__":
    main()
