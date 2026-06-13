import sys
import pytest

from sqlalchemy.ext import asyncio
from unittest import IsolatedAsyncioTestCase, mock
from freezegun import freeze_time

from usagiBot.tests.utils import *


@pytest.fixture(autouse=True)
def clear_imports():
    from usagiBot.db.base import Base
    Base.metadata.clear()
    initial_modules = dict(sys.modules)
    yield
    for module in list(sys.modules.keys()):
        if module not in initial_modules:
            del sys.modules[module]


class TestEndfieldCommands(IsolatedAsyncioTestCase):
    @mock.patch("usagiBot.cogs.ArknightsEndfield.arknights_utils.EndfieldClient")
    @mock.patch("usagiBot.cogs.Main.schemas.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch(
        "usagiBot.cogs.ArknightsEndfield.schemas.UsagiGryphline",
        new_callable=mock.AsyncMock,
    )
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(
        self, mock_engine, mock_UsagiGryphline, mock_UsagiConfig, mock_EndfieldClient
    ) -> None:
        from usagiBot.cogs.ArknightsEndfield.index import Endfield

        self.Endfield = Endfield
        self.mock_UsagiGryphline = mock_UsagiGryphline
        self.mock_UsagiConfig = mock_UsagiConfig
        self.mock_EndfieldClient = mock_EndfieldClient

        self.Endfield.bot = mock.AsyncMock()
        self.Endfield.bot.logger = mock.MagicMock()
        self.Endfield.bot.i18n = init_i18n()
        self.Endfield.bot.language = {}

        self.ctx = mock.AsyncMock()
        self.ctx.guild.id = "g1"
        self.ctx.author.id = "u1"

    async def test_endfield_profile_no_user_awaits_response(self) -> None:
        self.mock_UsagiGryphline.get_all_by.return_value = []
        await self.Endfield.endfield_profile.callback(self.Endfield, self.ctx)
        self.ctx.respond.assert_awaited()

    async def test_endfield_sanity_no_user_awaits_response(self) -> None:
        self.mock_UsagiGryphline.get_all_by.return_value = []
        await self.Endfield.endfield_sanity.callback(self.Endfield, self.ctx)
        self.ctx.respond.assert_awaited()

    async def test_endfield_settings_no_account_awaits_response(self) -> None:
        self.mock_UsagiGryphline.get.return_value = None
        await self.Endfield.endfield_settings.callback(
            self.Endfield, self.ctx, option="Daily reward", uid=123
        )
        self.ctx.respond.assert_awaited()

    async def test_endfield_delete_no_account_awaits_response(self) -> None:
        self.mock_UsagiGryphline.get.return_value = None
        await self.Endfield.endfield_delete.callback(self.Endfield, self.ctx, uid=123)
        self.ctx.respond.assert_awaited()

    @freeze_time("2026-06-13 16:00:00")  # 19:00 Europe/Moscow, when the loop runs
    async def test_claim_loop_skips_attendance_after_failed_signin(self) -> None:
        self.mock_UsagiGryphline.get_all_by_or.return_value = [
            mock.MagicMock(guild_id="g1", user_id="u1", token="t1")
        ]
        self.mock_UsagiConfig.get.return_value = mock.MagicMock(generic_id=42)

        client = self.mock_EndfieldClient.return_value
        client.start = mock.AsyncMock()
        client.close = mock.AsyncMock()
        client.sign_in = mock.AsyncMock(return_value=False)
        client.get_attendance = mock.AsyncMock()

        await self.Endfield.claim_endfield_daily_reward.coro(self.Endfield)

        client.sign_in.assert_awaited()
        client.get_attendance.assert_not_called()
