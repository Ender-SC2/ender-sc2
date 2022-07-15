# command_utils.py

from math import sqrt

from ender.behavior.behavior import IBehavior
from sc2.position import Point2


class CommandUtils(IBehavior):

    hash = {}
    last_position = {}

    def next_position(self, unt) -> Point2:
        nowpos = unt.position
        if unt.tag in self.last_position:
            lastpos = self.last_position[unt.tag]
            nextpos = 2 * nowpos - lastpos
            return nextpos
        else:
            return nowpos

    def save_position(self):
        for unt in self.bot_ai.enemy_units:
            nowpos = unt.position
            self.last_position[unt.tag] = nowpos
        for unt in self.bot_ai.units:
            nowpos = unt.position
            self.last_position[unt.tag] = nowpos

