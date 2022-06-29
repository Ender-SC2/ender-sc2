from abc import ABC, abstractmethod

from ender.job import Job
from ender.unit.unit_command import IUnitCommand
from sc2.unit import Unit


# TODO: Extract UnitInterface from common to make it easier to test
class IUnitInterface(ABC):

    @abstractmethod
    def set_command(self, unit: Unit, command: IUnitCommand):
        raise NotImplementedError()

    @abstractmethod
    def queue_command(self, unit: Unit, command: IUnitCommand):
        raise NotImplementedError()

    @abstractmethod
    def execute(self):
        raise NotImplementedError()

    @abstractmethod
    def job_of_unit(self, unit: Unit) -> Job:
        raise NotImplementedError()

    @abstractmethod
    def job_of_unittag(self, tag: int) -> Job:
        raise NotImplementedError()

    @abstractmethod
    def set_job_of_unit(self, unit: Unit, job: Job):
        raise NotImplementedError()

    @abstractmethod
    def set_job_of_unittag(self, tag: int, job: Job):
        raise NotImplementedError()

    @abstractmethod
    def job_count(self, job: Job) -> int:
        raise NotImplementedError()


class UnitInterface(IUnitInterface):

    def __init__(self):
        self._previousCommands: dict[Unit, list[IUnitCommand]] = {}
        self._commands: dict[Unit, list[IUnitCommand]] = {}
        self._unit_job: dict[int, Job] = {}

    def set_command(self, unit: Unit, command: IUnitCommand):
        self._commands[unit] = [command]

    def queue_command(self, unit: Unit, command: IUnitCommand):
        if unit not in self._commands:
            self._commands[unit] = []
        self._commands[unit].append(command)

    async def execute(self):
        for unit, commands in self._commands.items():
            first = True
            new_commands = True
            if unit in self._previousCommands:
                previous_commands = self._previousCommands[unit]
                new_commands = commands != previous_commands
            if new_commands:
                for command in commands:
                    if first:
                        await command.execute(unit)
                    else:
                        await command.execute(unit, True)
                    first = False
        self._previousCommands = self._commands
        self._commands = {}

    def job_of_unit(self, unit: Unit) -> Job:
        return self.job_of_unittag(unit.tag)

    def job_of_unittag(self, tag: int) -> Job:
        if tag in self._unit_job:
            return self._unit_job[tag]
        return Job.UNCLEAR

    def set_job_of_unit(self, unit: Unit, job: Job):
        self.set_job_of_unittag(unit.tag, job)

    def set_job_of_unittag(self, tag: int, job: Job):
        self._unit_job[tag] = job

    def job_count(self, job: Job) -> int:
        # do not call often
        count = 0
        for unt in self.units: # needed to prevent dead unit info
            current_job = self._unit_job[unt.tag]
            if current_job == job:
                count += 1
        return count
