from abc import ABC, abstractmethod
from inspect import signature
from typing import List, overload

from ender.job import Job
from ender.unit.unit_command import IUnitCommand
from sc2.unit import Unit


# TODO: Extract UnitInterface from common to make it easier to test
class IUnitInterface(ABC):

    @abstractmethod
    def set_command(self, unit: Unit, command: IUnitCommand):
        raise NotImplementedError()

    @abstractmethod
    def execute(self):
        raise NotImplementedError()

    @overload
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
    def job_count(self, job) -> int:
        raise NotImplementedError()


class UnitInterface(IUnitInterface):
    _commands: dict[Unit, list[IUnitCommand]]
    _unit_job: dict[int, Job]

    def __init__(self):
        self._commands = {}
        self._unit_job = {}

    def set_command(self, unit: Unit, command: IUnitCommand):
        self._commands[unit] = [command]

    def set_queue_command(self, unit: Unit, command: IUnitCommand):
        self._commands[unit].append(command)

    async def execute(self):
        for unit, commands in self._commands.items():
            first = True
            for command in commands:
                if first:
                    await command.execute(unit) # really? usually, a unit executes a command ...
                else:
                    await command.execute(unit) # ,queue=True
                first = False
        self._commands.clear()

    def job_of_unit(self, unit: Unit) -> Job:
        if unit.tag in self._unit_job:
            return self._unit_job[unit.tag]
        return Job.UNCLEAR

    def job_of_unittag(self, tag: int) -> Job:
        if tag in self._unit_job:
            return self._unit_job[tag]
        return Job.UNCLEAR

    def set_job_of_unit(self, unit: Unit, job: Job):
        self._unit_job[unit.tag] = job

    def set_job_of_unittag(self, tag: int, job: Job):
        self._unit_job[tag] = job

    def job_count(self, job) -> int:
        # do not call often
        count = 0
        for unt in self.units: # needed to prevent dead unit info
            current_job = self._unit_job[unt.tag]
            if current_job == job:
                count += 1
        return count
