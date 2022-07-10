from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from test.setup.test_setup import ITestSetup


class CreateUnitsTestSetup(ITestSetup):
    def __init__(self, unit_type: UnitTypeId, amount: int, offset: Point2):
        self.unit_type = unit_type
        self.amount = amount
        self.offset = offset

    async def setup(self, bot_ai: BotAI):
        await bot_ai.client.debug_create_unit(
            [
                [
                    self.unit_type,
                    self.amount,
                    bot_ai.game_info.map_center + self.offset,
                    bot_ai.player_id,
                ]
            ]
        )
