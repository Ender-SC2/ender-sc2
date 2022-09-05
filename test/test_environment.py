from loguru import logger

import sc2
from sc2.data import Result, Race
from sc2.main import run_game
from sc2.player import Bot
from test.ender_test_bot import EnderTestBot

battle_maps = ["Empty128"]
basic_maps = [
    "BlackburnAIE",
    "CuriousMindsAIE",
    "2000AtmospheresAIE",
    "GlitteringAshesAIE",
    "HardwireAIE",
    "BerlingradAIE",
]


class TestEnvironment:
    def test(self, map: str, winner: EnderTestBot, loser: EnderTestBot) -> Result:
        try:
            return run_game(
                sc2.maps.get(map),  # pyright: ignore
                [Bot(Race.Random, winner), Bot(Race.Random, loser)],
                realtime=False,
            )
        except ConnectionResetError:
            logger.debug("Exception")
