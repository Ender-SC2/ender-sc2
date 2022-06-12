from typing import Union

from ender.unit.unit_command import IUnitCommand
from sc2.position import Point2
from sc2.unit import Unit


class MoveCommand(IUnitCommand):
    def __init__(self, target: Union[Unit, Point2], queue: bool = False):
        self.target = target
        self.queue = queue

    async def execute(self, unit: Unit):
        # TODO: Don't execute if already executing this command
        unit.move(self.target, self.queue)
