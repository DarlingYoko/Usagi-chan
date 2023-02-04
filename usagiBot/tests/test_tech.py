import datetime

from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase


class TestTechMethods(IsolatedAsyncioTestCase):

    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Tech.index import Tech
        self.Tech = Tech

        self.bot = mock.AsyncMock()
        self.ctx = mock.AsyncMock()
        self.ctx.author.name = "test_author"

        self.message = mock.AsyncMock()

    async def test_pin_message(self) -> None:

        await self.Tech.pin_message(self.Tech, self.ctx, self.message)

        self.message.pin.assert_called_with(reason=f"Pinned by test_author")
        self.ctx.respond.assert_called_with(f"Message was pinned", ephemeral=True)

    async def test_go_sleep(self) -> None:
        await self.Tech.go_sleep(self.ctx, 20)
        self.ctx.author.timeout_for.assert_called_with(
            duration=datetime.timedelta(seconds=72000),
            reason="Timeout for sleep"
        )
        self.ctx.respond.assert_called_with("Good night, see you in 20 hours.", ephemeral=True)

    async def test_go_sleep_wrong_hours(self) -> None:
        await self.Tech.go_sleep(self.ctx, 80)
        self.ctx.respond.assert_called_with("You entered the wrong amount of time.", ephemeral=True)
        self.ctx.author.timeout_for.assert_not_called()

