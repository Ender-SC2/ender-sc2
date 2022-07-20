import sys

# Load bot
from Main import Ender
from __init__ import run_ladder_game
from sc2.data import Race
from sc2.player import Bot

bot = Bot(Race.Zerg, Ender())

# Start game
if __name__ == "__main__":
    if "--LadderServer" in sys.argv:
        # Ladder game started by LadderManager
        print("Starting ladder game...")
        result, opponentid = run_ladder_game(bot)
        print(f"{result} against opponent {opponentid}")
