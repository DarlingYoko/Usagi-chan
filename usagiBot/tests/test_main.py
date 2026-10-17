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

    # --- timer add/remove ---------------------------------------------------

    async def test_add_timer_creates_when_absent(self) -> None:
        self.mock_Timer.get.return_value = None
        channel = mock.MagicMock(id="c1")
        await self.Main.add_timer.callback(
            self.Main, self.ctx, channel, "01.02.2026 03:04:05"
        )
        self.mock_Timer.create.assert_awaited_once()
        self.mock_Timer.update.assert_not_called()
        self.ctx.respond.assert_awaited()

    async def test_add_timer_updates_when_present(self) -> None:
        self.mock_Timer.get.return_value = mock.MagicMock(id="t1")
        channel = mock.MagicMock(id="c1")
        await self.Main.add_timer.callback(
            self.Main, self.ctx, channel, "01.02.2026 03:04:05"
        )
        self.mock_Timer.update.assert_awaited_once()
        self.mock_Timer.create.assert_not_called()

    async def test_remove_timer_missing_responds(self) -> None:
        self.mock_Timer.get.return_value = None
        await self.Main.remove_timer.callback(self.Main, self.ctx, "123")
        self.mock_Timer.delete.assert_not_called()
        self.ctx.respond.assert_awaited()

    async def test_remove_timer_deletes(self) -> None:
        self.mock_Timer.get.return_value = mock.MagicMock(id="t1")
        await self.Main.remove_timer.callback(self.Main, self.ctx, "123")
        self.mock_Timer.delete.assert_awaited_once_with(id="t1")

    # --- save_roles toggle --------------------------------------------------

    async def test_save_roles_enables_when_absent(self) -> None:
        import usagiBot.cogs.Main.index as main_index

        with mock.patch.object(
            main_index, "UsagiSaveRoles", new_callable=mock.AsyncMock
        ) as mock_SaveRoles:
            mock_SaveRoles.get.return_value = None
            await self.Main.save_roles_on_leave.callback(self.Main, self.ctx)
            mock_SaveRoles.create.assert_awaited_once_with(
                guild_id="g1", saving_roles=True
            )

    async def test_save_roles_disables_when_on(self) -> None:
        import usagiBot.cogs.Main.index as main_index

        with mock.patch.object(
            main_index, "UsagiSaveRoles", new_callable=mock.AsyncMock
        ) as mock_SaveRoles:
            mock_SaveRoles.get.return_value = mock.MagicMock(id="s1", saving_roles=True)
            await self.Main.save_roles_on_leave.callback(self.Main, self.ctx)
            mock_SaveRoles.update.assert_awaited_once_with(id="s1", saving_roles=False)

    async def test_save_roles_enables_when_off(self) -> None:
        import usagiBot.cogs.Main.index as main_index

        with mock.patch.object(
            main_index, "UsagiSaveRoles", new_callable=mock.AsyncMock
        ) as mock_SaveRoles:
            mock_SaveRoles.get.return_value = mock.MagicMock(id="s1", saving_roles=False)
            await self.Main.save_roles_on_leave.callback(self.Main, self.ctx)
            mock_SaveRoles.update.assert_awaited_once_with(id="s1", saving_roles=True)

    # --- auto-role create ---------------------------------------------------

    async def test_create_auto_role_message_writes_row_and_cache(self) -> None:
        self.ctx.bot.auto_roles = {}
        channel = mock.AsyncMock(id="chan1")
        channel.send.return_value = mock.MagicMock(id=999)

        await self.Main.create_auto_role_message.callback(
            self.Main, self.ctx, channel, "My roles"
        )

        self.mock_AutoRoles.create.assert_awaited_once_with(
            guild_id="g1", channel_id="chan1", message_id="999", name="My roles"
        )
        self.assertEqual(
            self.ctx.bot.auto_roles["g1"]["999"],
            {"name": "My roles", "channel_id": "chan1"},
        )

    # --- add/remove reaction role happy paths -------------------------------

    async def test_add_reaction_role_not_auto_role_responds(self) -> None:
        self.ctx.bot.auto_roles = {"g1": {}}
        await self.Main.add_reaction_role.callback(
            self.Main, self.ctx, "123", mock.MagicMock(), mock.MagicMock(), "d"
        )
        self.ctx.respond.assert_awaited()
        self.mock_AutoRolesData.create.assert_not_called()

    async def test_add_reaction_role_success(self) -> None:
        self.ctx.bot.auto_roles = {"g1": {"123": {"channel_id": 1, "name": "n"}}}
        msg = mock.AsyncMock()
        msg.embeds = [mock.MagicMock()]
        msg.reactions = []
        channel = mock.AsyncMock()
        channel.fetch_message.return_value = msg
        self.ctx.guild.fetch_channel.return_value = channel
        self.mock_AutoRolesData.get_all_by.return_value = []
        role = mock.MagicMock(id=1, mention="<@&1>")
        emoji = mock.MagicMock(id=2)

        await self.Main.add_reaction_role.callback(
            self.Main, self.ctx, "123", role, emoji, "desc"
        )

        msg.add_reaction.assert_awaited_once_with(emoji)
        self.mock_AutoRolesData.create.assert_awaited_once_with(
            message_id="123", role_id=1, emoji_id=2, description="desc"
        )
        self.ctx.respond.assert_awaited()

    async def test_remove_reaction_role_success(self) -> None:
        self.ctx.bot.auto_roles = {"g1": {"123": {"channel_id": 1, "name": "n"}}}
        msg = mock.AsyncMock()
        msg.embeds = [mock.MagicMock()]
        channel = mock.AsyncMock()
        channel.fetch_message.return_value = msg
        self.ctx.guild.fetch_channel.return_value = channel
        self.ctx.guild.get_emoji = mock.MagicMock(return_value=None)
        self.mock_AutoRolesData.get_all_by.return_value = [
            mock.MagicMock(role_id=1, emoji_id=2, description="gone"),
            mock.MagicMock(role_id=9, emoji_id=8, description="stay"),
        ]

        await self.Main.remove_reaction_role.callback(self.Main, self.ctx, "123", "1")

        msg.clear_reaction.assert_awaited_once()
        self.mock_AutoRolesData.delete.assert_awaited_once_with(
            message_id="123", role_id=1
        )
        self.ctx.respond.assert_awaited()

    # --- change_lang --------------------------------------------------------

    async def test_change_lang_creates_when_absent(self) -> None:
        import usagiBot.cogs.Main.index as main_index

        self.ctx.author.id = "u1"
        self.Main.bot.language = {}
        with mock.patch.object(
            main_index, "UsagiLanguage", new_callable=mock.AsyncMock
        ) as mock_Lang:
            mock_Lang.get.return_value = None
            await self.Main.change_lang.callback(self.Main, self.ctx, "ru")
            mock_Lang.create.assert_awaited_once_with(user_id="u1", lang="ru")
        self.assertEqual(self.Main.bot.language["u1"], "ru")

    async def test_change_lang_updates_when_present(self) -> None:
        import usagiBot.cogs.Main.index as main_index

        self.ctx.author.id = "u1"
        self.ctx.bot.language = {}
        with mock.patch.object(
            main_index, "UsagiLanguage", new_callable=mock.AsyncMock
        ) as mock_Lang:
            mock_Lang.get.return_value = mock.MagicMock(id="l1")
            await self.Main.change_lang.callback(self.Main, self.ctx, "en")
            mock_Lang.update.assert_awaited_once_with(id="l1", lang="en")

    # --- autocomplete helpers ----------------------------------------------

    async def test_get_auto_role_messages_lists_cache(self) -> None:
        import usagiBot.cogs.Main.index as main_index

        ctx = mock.MagicMock()
        ctx.bot.auto_roles = {"g1": {"123": {"name": "Roles", "channel_id": 1}}}
        ctx.interaction.guild_id = "g1"
        result = await main_index.get_auto_role_messages(ctx)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].value, "123")

    async def test_get_timers_resolves_channel_names(self) -> None:
        import usagiBot.cogs.Main.index as main_index

        self.mock_Timer.get_all_by.return_value = [mock.MagicMock(channel_id=5)]
        guild = mock.MagicMock()
        channel = mock.MagicMock()
        channel.name = "voice"
        guild.get_channel = mock.MagicMock(return_value=channel)
        ctx = mock.MagicMock()
        ctx.bot.get_guild = mock.MagicMock(return_value=guild)
        ctx.interaction.guild_id = "g1"
        result = await main_index.get_timers(ctx)
        self.assertEqual([c.name for c in result], ["voice"])

    async def test_get_roles_from_message_maps_roles(self) -> None:
        import usagiBot.cogs.Main.index as main_index

        self.mock_AutoRolesData.get_all_by.return_value = [
            mock.MagicMock(role_id=7)
        ]
        role = mock.MagicMock(id=7)
        role.name = "VIP"
        ctx = mock.MagicMock()
        ctx.options = {"message": "123"}
        ctx.interaction.guild.get_role = mock.MagicMock(return_value=role)
        result = await main_index.get_roles_from_message(ctx)
        self.assertEqual(result[0].value, "7")
