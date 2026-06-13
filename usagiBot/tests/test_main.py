import sys
import pytest

import discord
from sqlalchemy.ext import asyncio
from unittest import IsolatedAsyncioTestCase, mock

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


def _not_found():
    return discord.errors.NotFound(
        mock.MagicMock(status=404, reason="Not Found"), "gone"
    )


class TestMainCommands(IsolatedAsyncioTestCase):
    @mock.patch(
        "usagiBot.cogs.Main.schemas.UsagiAutoRolesData", new_callable=mock.AsyncMock
    )
    @mock.patch(
        "usagiBot.cogs.Main.schemas.UsagiAutoRoles", new_callable=mock.AsyncMock
    )
    @mock.patch("usagiBot.cogs.Main.schemas.UsagiTimer", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(
        self, mock_engine, mock_Timer, mock_AutoRoles, mock_AutoRolesData
    ) -> None:
        from usagiBot.cogs.Main.index import Main

        self.Main = Main
        self.mock_Timer = mock_Timer
        self.mock_AutoRoles = mock_AutoRoles
        self.mock_AutoRolesData = mock_AutoRolesData

        self.Main.bot = mock.AsyncMock()
        self.Main.bot.i18n = init_i18n()
        self.Main.bot.language = {}

        self.ctx = mock.AsyncMock()
        self.ctx.guild.id = "g1"
        self.ctx.guild_id = "g1"
        self.ctx.author.name = "Yoko"

    async def test_add_timer_invalid_date_responds(self) -> None:
        channel = mock.MagicMock()
        await self.Main.add_timer.callback(self.Main, self.ctx, channel, "garbage")
        self.ctx.respond.assert_awaited()
        self.mock_Timer.get.assert_not_called()

    async def test_remove_auto_role_handles_notfound(self) -> None:
        msg = mock.AsyncMock()
        msg.delete.side_effect = _not_found()
        channel = mock.AsyncMock()
        channel.fetch_message.return_value = msg
        self.ctx.guild.fetch_channel.return_value = channel
        self.ctx.bot.auto_roles = {"g1": {"123": {"channel_id": 1, "name": "n"}}}

        await self.Main.remove_auto_role_message.callback(self.Main, self.ctx, "123")

        self.ctx.send_followup.assert_awaited()
