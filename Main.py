# Main.py, Ender

import random
from datetime import datetime

import sc2
from ender.attack import Attack
from ender.creep import Creep
from ender.endstep import Endstep
from ender.making import Making
from ender.parts import Parts
from ender.lingscout import Lingscout
from ender.queens import Queens
from ender.overlords import Overlords
from ender.mining import Mining
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer


#                          BotAI
#                            |
#                          Common
#                                       \
#                                        Tech
#                        /  |          /   \       \       \         \      \     \        \
#                  Attack Map_if Resources Strategy Queens Overlords Mining Parts Lingscout Endstep
#                           |   \    |    /
#                         Creep   Making
#
#                       \   |       /            /      /      /     /     /          /
#
#                         Ender
#


class Ender(Attack, Creep, Making, Queens, Overlords, Mining, Parts, Lingscout, Endstep):
    def __init__(self):
        super().__init__()

    async def on_step(self, iteration: int):
        self.did_common_onstep = False
        self.did_map_onstep = False
        self.did_tech_onstep = False
        self.iteration = iteration
        await Attack.on_step(self, iteration)
        await Creep.on_step(self, iteration)
        await Making.on_step(self, iteration)
        await Queens.on_step(self, iteration)
        await Overlords.on_step(self, iteration)
        await Mining.on_step(self, iteration)
        await Parts.on_step(self, iteration)
        await Lingscout.on_step(self, iteration)
        await Endstep.on_step(self, iteration)


# *********************************************************************************************************************
def main():
    # Easy/Medium/Hard/VeryHard
    all_maps = [
        "BlackburnAIE",
        "CuriousMindsAIE",
        "2000AtmospheresAIE",
        "GlitteringAshesAIE",
        "HardwireAIE",
        "BerlingradAIE",
    ]
    map = random.choice(all_maps)
    # TO TEST use next line
    # map = '2000AtmospheresAIE'
    opponentspecies = random.choice([Race.Terran, Race.Zerg, Race.Protoss])
    # TO TEST use next line
    # opponentspecies = Race.Terran
    # VeryEasy/Easy/Medium/Hard/VeryHard
    run_game(
        sc2.maps.get(map),
        [Bot(Race.Zerg, Ender()), Computer(opponentspecies, Difficulty.VeryHard)],
        save_replay_as=f"{datetime.utcnow().strftime('%Y%m%d_%H%M')}.SC2Replay",
        realtime=False,
    )


if __name__ == "__main__":
    main()
