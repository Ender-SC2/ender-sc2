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
    def get_unit_job(self, unit: Unit) -> Job:
        raise NotImplementedError()

    @abstractmethod
    def get_unit_job(self, tag: int) -> Job:
        raise NotImplementedError()

    @abstractmethod
    def set_unit_job(self, unit: Unit, job: Job):
        raise NotImplementedError()

    @abstractmethod
    def job_count(self, job) -> int:
        raise NotImplementedError()


class UnitInterface(IUnitInterface):
    _commands: dict[Unit, IUnitCommand]
    _unit_job: dict[int, Job]

    def __init__(self):
        self._commands = {}
        self._unit_job = {}

    def set_command(self, unit: Unit, command: IUnitCommand):
        self._commands[unit] = command

    async def execute(self):
        for unit, command in self._commands.items():
            await command.execute(unit)
        self._commands.clear()

    @overload
    def get_unit_job(self, unit: Unit) -> Job:
        return self.get_unit_job(unit.tag)

    def get_unit_job(self, tag: int) -> Job:
        if tag in self._unit_job:
            return self._unit_job[tag]
        return Job.UNCLEAR

    @overload
    def set_unit_job(self, unit: Unit, job: Job):
        self._unit_job[unit.tag] = job

    def set_unit_job(self, tag: int, job: Job):
        self._unit_job[tag] = job

    def job_count(self, job) -> int:
        # do not call often
        count = 0
        for current_job in self._unit_job:
            if current_job == job:
                count += 1
        return count
