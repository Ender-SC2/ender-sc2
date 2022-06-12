from ender.unit.unit_command import IUnitCommand
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class BuildCommand(IUnitCommand):
    def __init__(self, unit_type: UnitTypeId, position: Point2, queue: bool = False):
        self.unit_type = unit_type
        self.position = position
        self.queue = queue

    async def execute(self, unit: Unit):
        # TODO: Don't execute if already executing this command
        unit.build(self.unit_type, self.position, self.queue)
