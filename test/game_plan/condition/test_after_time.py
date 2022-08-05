import logging
import unittest
from unittest.mock import Mock

from ender.game_plan.condition import AfterTime

logging.basicConfig(level=logging.DEBUG)


class TestAfterTime(unittest.TestCase):
    def test_after_time_matching_condition(self):
        bot_ai = Mock()
        bot_ai.time = 15
        sut = AfterTime(10)
        sut.setup(bot_ai)
        self.assertTrue(sut.check())

    def test_after_time_not_matching_condition(self):
        bot_ai = Mock()
        bot_ai.time = 5
        sut = AfterTime(10)
        sut.setup(bot_ai)
        self.assertFalse(sut.check())

    def test_after_time_equal_time(self):
        bot_ai = Mock()
        bot_ai.time = 7
        sut = AfterTime(7)
        sut.setup(bot_ai)
        self.assertFalse(sut.check())


if __name__ == "__main__":
    unittest.main()
