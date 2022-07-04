import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from ender.unit import UnitInterface, AttackCommand, MoveCommand
from sc2.position import Point2


class TestUnitInterface(IsolatedAsyncioTestCase):

    async def test_command_execute(self):
        unit = Mock()
        target = Point2()
        sut = UnitInterface()
        sut.set_command(unit, AttackCommand(target))
        await sut.execute()
        unit.attack.assert_called_once()

    async def test_equalcommand_skip(self):
        unit = Mock()
        target = Point2()
        sut = UnitInterface()
        sut.set_command(unit, AttackCommand(target))
        await sut.execute()
        sut.set_command(unit, AttackCommand(target))
        await sut.execute()
        unit.attack.assert_called_once()

    async def test_differentunit_dontskip(self):
        unit1 = Mock()
        unit2 = Mock()
        target = Point2()
        sut = UnitInterface()
        sut.set_command(unit1, AttackCommand(target))
        await sut.execute()
        sut.set_command(unit2, AttackCommand(target))
        await sut.execute()
        unit2.attack.assert_called_once()

    async def test_differentcommand_dontskip(self):
        unit1 = Mock()
        target = Point2()
        sut = UnitInterface()
        sut.set_command(unit1, AttackCommand(target))
        await sut.execute()
        sut.set_command(unit1, MoveCommand(target))
        await sut.execute()
        unit1.move.assert_called_once()

    async def test_samebutdifferentcommand_dontskip(self):
        unit1 = Mock()
        target1 = Point2()
        target2 = Point2("100, 0")
        sut = UnitInterface()
        sut.set_command(unit1, AttackCommand(target1))
        await sut.execute()
        unit1.reset_mock()
        sut.set_command(unit1, AttackCommand(target2))
        await sut.execute()
        unit1.attack.assert_called_once()

    async def test_replacecommand_executelast(self):
        unit1 = Mock()
        target1 = Point2()
        target2 = Point2("100, 0")
        sut = UnitInterface()
        sut.set_command(unit1, AttackCommand(target1))
        sut.set_command(unit1, MoveCommand(target2))
        await sut.execute()
        unit1.attack.assert_not_called()
        unit1.move.assert_called_once()

    async def test_queuecommand_executeall(self):
        unit1 = Mock()
        target1 = Point2()
        target2 = Point2("100, 0")
        sut = UnitInterface()
        sut.set_command(unit1, AttackCommand(target1))
        sut.queue_command(unit1, MoveCommand(target2))
        await sut.execute()
        unit1.attack.assert_called_once_with(unittest.mock.ANY, False)
        unit1.move.assert_called_once_with(unittest.mock.ANY, True)


if __name__ == '__main__':
    unittest.main()
