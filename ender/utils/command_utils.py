# command_utils.py

from typing import List, Optional
from ender.behavior.behavior import IBehavior
from math import sqrt

from loguru import logger

from ender.unit import AttackCommand, MoveCommand
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

class CommandUtils(IBehavior):

    hash = {}
    last_position = {}

    def txt_of_pos(self, pos: Point2) -> str:
        return '(' + str(round(pos.x * 100) / 100) + ',' +  str(round(pos.y * 100) / 100) + ')'
    
    def nospam_pos(self, daddy, unit, action, goal):
        if unit not in self.hash:
            self.hash[unit] = 0
        hhash = ord(action) + goal.x + goal.y
        if hhash != self.hash[unit]:
            self.hash[unit] = hhash
            if action == 'A':
                self.unit_interface.set_command(unit, AttackCommand(goal))
                logger.info(daddy + ' ' + unit.name + str(unit.tag) + ' attacking ' + self.txt_of_pos(goal) + ' at ' + str(self.frame))
            elif action == 'M':
                self.unit_interface.set_command(unit, MoveCommand(goal))
                logger.info(daddy + ' ' + unit.name + str(unit.tag) + ' moving ' + self.txt_of_pos(goal) + ' at ' + str(self.frame))

    def nospam_ene(self, daddy, unit, action, enemy):
        if unit not in self.hash:
            self.hash[unit] = 0
        hhash = ord(action) + enemy.tag
        if hhash != self.hash[unit]:
            self.hash[unit] = hhash
            if action == 'A':
                self.unit_interface.set_command(unit, AttackCommand(enemy))
                logger.info(daddy + ' ' + unit.name + str(unit.tag) + ' attacking ' + str(enemy.name) + str(enemy.tag) + ' at ' + str(self.frame))
            if action == 'M':
                self.unit_interface.set_command(unit, MoveCommand(enemy))
                logger.info(daddy + ' ' + unit.name + str(unit.tag) + ' moving ' + str(enemy.name) + str(enemy.tag) + ' at ' + str(self.frame))

    def distance(self, p, q) -> float:
        sd = (p.x-q.x)*(p.x-q.x) + (p.y-q.y)*(p.y-q.y)
        return sqrt(sd)

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

