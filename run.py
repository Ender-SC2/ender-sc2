# Imports have to be in this order, leave this comment here to fall back to it if they get messed up
# import sc2, sys
# from __init__ import run_ladder_game
# from sc2 import Race, Difficulty
# from sc2.player import Bot, Computer
# import random
import sc2
import sys

# Load bot
from Main import Ender
from __init__ import run_ladder_game
from sc2.data import Race, Difficulty
from sc2.player import Bot, Computer

bot = Bot(Race.Zerg, Ender())

# Start game
if __name__ == "__main__":
    if "--LadderServer" in sys.argv:
        # Ladder game started by LadderManager
        print("Starting ladder game...")
        result, opponentid = run_ladder_game(bot)
        print(f"{result} against opponent {opponentid}")
    else:
        # Local game
        print("Starting local game...")
        # map_name = "(2)16-BitLE"
        sc2.run_game(
            sc2.maps.get(map_name),
            [
                # Human(Race.Terran),
                bot,
                Computer(Race.Random, Difficulty.VeryHard),  # CheatInsane VeryHard
            ],
            realtime=False,
            save_replay_as="Example.SC2Replay",
        )
