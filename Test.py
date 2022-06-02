# Main.py, Ender

import random

import sc2
from Main import Ender
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer


# *********************************************************************************************************************
def test():
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
        Bot(Race.Zerg, Ender(True)),
        Computer(opponentspecies, Difficulty.VeryHard)
    ], realtime=False)


if __name__ == "__main__":
    test()
