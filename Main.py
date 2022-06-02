# Main.py, Ender

import random
from typing import List, Optional

import sc2
from ender.attack import Attack
from ender.creep import Creep
from ender.endstep import Endstep
from ender.making import Making
from ender.parts import Parts
from ender.queens import Queens
from ender.workers import Workers
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer
from test.test_base import TestBase
from test.defensive_spore_test import DefensiveSporeTest


#                          BotAI
#                            |
#                          Common
#                                       \
#                                        Tech
#                        /  |          /   \       \       \     \      \
#                  Attack Map_if Resources Strategy Queens Workers Parts Endstep
#                           |   \    |    /
#                         Creep   Making
#
#                       \   |       /            /      /      /     /
#
#                         Ender
#


class Ender(Attack, Creep, Making, Queens, Workers, Parts, Endstep):
    tests: Optional[List[TestBase]]

    def __init__(self, testing: bool = False):
        super().__init__()
        self.testing = testing
        self.tests = None

    async def on_step(self, iteration: int):
        self.did_common_onstep = False
        self.did_map_onstep = False
        self.did_tech_onstep = False
        self.iteration = iteration
        await Attack.on_step(self)
        await Creep.on_step(self)
        await Making.on_step(self)
        await Queens.on_step(self)
        await Workers.on_step(self)
        await Parts.on_step(self)
        await Endstep.on_step(self)
        if self.testing:
            if not self.tests:
                self.tests = [DefensiveSporeTest()]
                for test in self.tests:
                    test.setup(self)
            for test in self.tests:
                await test.on_step()


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
