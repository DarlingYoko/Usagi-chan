import sys
import pytest

import discord
from datetime import datetime, timedelta
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
        self.Main.bot.logger = mock.MagicMock()
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

    async def test_remove_auto_role_pops_cache(self) -> None:
        channel = mock.AsyncMock()
        channel.fetch_message.return_value = mock.AsyncMock()
        self.ctx.guild.fetch_channel.return_value = channel
        self.ctx.bot.auto_roles = {"g1": {"123": {"channel_id": 1, "name": "n"}}}

        await self.Main.remove_auto_role_message.callback(self.Main, self.ctx, "123")

        self.assertNotIn("123", self.ctx.bot.auto_roles["g1"])

    async def test_update_timer_clamps_expired(self) -> None:
        past = datetime.now() - timedelta(hours=1)
        self.mock_Timer.get_all.return_value = [
            mock.MagicMock(channel_id="c1", date=past)
        ]
        channel = mock.AsyncMock()
        self.Main.bot.get_channel = mock.MagicMock(return_value=channel)

        await self.Main.update_timer.coro(self.Main)

        channel.edit.assert_awaited_with(name=" 0 h. 0 m.", reason="Update timer.")

    async def test_update_timer_survives_deleted_channel(self) -> None:
        future = datetime.now() + timedelta(hours=2)
        self.mock_Timer.get_all.return_value = [
            mock.MagicMock(channel_id="dead", date=future),
            mock.MagicMock(channel_id="live", date=future),
        ]
        live = mock.AsyncMock()

        def get_channel(cid):
            return None if cid == "dead" else live

        async def fetch_channel(cid):
            if cid == "dead":
                raise _not_found()
            return live

        self.Main.bot.get_channel = mock.MagicMock(side_effect=get_channel)
        self.Main.bot.fetch_channel = mock.AsyncMock(side_effect=fetch_channel)

        await self.Main.update_timer.coro(self.Main)

        live.edit.assert_awaited()
        self.Main.bot.logger.exception.assert_called()

    async def test_update_timer_survives_db_error(self) -> None:
        self.mock_Timer.get_all.side_effect = Exception("db down")

        await self.Main.update_timer.coro(self.Main)

        self.Main.bot.logger.exception.assert_called()

    def _edit_ctx(self):
        ctx = mock.AsyncMock()
        ctx.guild_id = "g1"
        ctx.bot.auto_roles = {"g1": {"123": {"channel_id": 1, "name": "n"}}}
        msg = mock.AsyncMock()
        msg.embeds = [mock.MagicMock()]
        channel = mock.AsyncMock()
        channel.fetch_message.return_value = msg
        ctx.guild.fetch_channel.return_value = channel
        # cache miss -> fall through to (awaited) fetch_emoji
        ctx.guild.get_emoji = mock.MagicMock(return_value=None)
        return ctx

    async def test_help_loads_config_once(self) -> None:
        import usagiBot.cogs.Main.index as main_index

        cmd = mock.MagicMock()
        cmd.name = "follow"
        cmd.description = "d"
        cmd.parent = None
        cmd.__original_kwargs__ = {"command_tag": "twitch_notify"}

        module = mock.MagicMock()
        module.qualified_name = "Twitch"
        module.cog_check.return_value = True
        module.walk_commands.return_value = [cmd]
        self.ctx.bot.cogs = {"Twitch": module}

        with mock.patch.object(
            main_index, "UsagiConfig", new_callable=mock.AsyncMock
        ) as mock_Config:
            mock_Config.get_all_by.return_value = [
                mock.MagicMock(command_tag="twitch_notify", generic_id=42)
            ]
            await self.Main.help_command.callback(self.Main, self.ctx, "Twitch")

        mock_Config.get_all_by.assert_awaited_once_with(guild_id="g1")
        mock_Config.get.assert_not_called()
        self.ctx.respond.assert_awaited()

    async def test_edit_role_unknown_role_responds(self) -> None:
        ctx = self._edit_ctx()
        self.mock_AutoRolesData.get_all_by.return_value = [
            mock.MagicMock(role_id=999, emoji_id=888, description="d")
        ]
        await self.Main.edit_role_reaction_role.callback(
            self.Main, ctx, "123", "555", mock.MagicMock(id=777)
        )
        ctx.send_followup.assert_awaited()
        self.mock_AutoRolesData.update.assert_not_called()

    async def test_edit_emoji_unknown_role_responds(self) -> None:
        ctx = self._edit_ctx()
        self.mock_AutoRolesData.get_all_by.return_value = [
            mock.MagicMock(role_id=999, emoji_id=888, description="d")
        ]
        await self.Main.edit_emoji_reaction_role.callback(
            self.Main, ctx, "123", "555", mock.MagicMock(id=777)
        )
        ctx.send_followup.assert_awaited()
        self.mock_AutoRolesData.update.assert_not_called()

    async def test_edit_description_unknown_role_responds(self) -> None:
        ctx = self._edit_ctx()
        self.mock_AutoRolesData.get_all_by.return_value = [
            mock.MagicMock(role_id=999, emoji_id=888, description="d")
        ]
        await self.Main.edit_description_reaction_role.callback(
            self.Main, ctx, "123", "555", "newdesc"
        )
        ctx.send_followup.assert_awaited()
        self.mock_AutoRolesData.update.assert_not_called()
