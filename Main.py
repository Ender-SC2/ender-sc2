# Main.py, Ender, Zerg bot
# 20 may 2022
#
from attack import Attack
from creep import Creep
from making import Making
from queens import Queens
from workers import Workers
from parts import Parts
from endstep import Endstep 
#
import sc2
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer
import random
#                          BotAI
#                            |
#                          Common
#                        /  |       \       \       \       \     \      \
#                  Attack Map_if Resources Strategy Queens Workers Parts Endstep
#                            |   \    |    /
#                           Creep   Making
#
#                        \   |       /            /      /      /     /
#
#                          Ender
#
class Ender(Attack, Creep, Making, Queens, Workers, Parts, Endstep):

    async def on_step(self, iteration: int):
        self.did_common_onstep = False
        self.did_map_onstep = False
        self.iteration = iteration
        if self.frame >= 12 * self.minutes: # debug
            breakthis = True # debug
        await Attack.on_step(self)
        await Creep.on_step(self)
        await Making.on_step(self)
        await Queens.on_step(self)
        await Workers.on_step(self)
        await Parts.on_step(self)
        await Endstep.on_step(self)

#*********************************************************************************************************************
def main():
    # Easy/Medium/Hard/VeryHard
    all_maps = ['BlackburnAIE','CuriousMindsAIE','2000AtmospheresAIE','GlitteringAshesAIE','HardwireAIE','BerlingradAIE']
    map = random.choice(all_maps)
    # TO TEST use next line
    #map = '2000AtmospheresAIE'
    opponentspecies = random.choice([Race.Terran,Race.Zerg,Race.Protoss])
    # TO TEST use next line
    #opponentspecies = Race.Protoss
    # Easy/Medium/Hard/VeryHard
    run_game(sc2.maps.get(map), [
        Bot(Race.Zerg, Ender()),
        Computer(opponentspecies, Difficulty.VeryHard)
        ], realtime = False)

if __name__ == "__main__":
    main()
