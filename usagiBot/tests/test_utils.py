import os

import discord
from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase
import importlib


os.environ["BOT_OWNER"] = "11111"
os.environ["BOT_ID"] = "1234567890"


class TestUtilsMethods(IsolatedAsyncioTestCase):

    @mock.patch("usagiBot.db.models.UsagiModerRoles", new_callable=mock.AsyncMock)
    @mock.patch("usagiBot.db.models.UsagiCogs", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine, mock_UsagiCogs, mock_UsagiModerRoles) -> None:
        mock_UsagiCogs.get_all.return_value = [
            mock.MagicMock(guild_id="test_guild_id_1", module_name="test_module_id_1", access=True),
            mock.MagicMock(guild_id="test_guild_id_1", module_name="test_module_id_2", access=False),
            mock.MagicMock(guild_id="test_guild_id_2", module_name="test_module_id_3", access=True),
        ]

        mock_UsagiModerRoles.get_all.return_value = [
            mock.MagicMock(guild_id="test_guild_id_1", moder_role_id="test_role_id_1"),
            mock.MagicMock(guild_id="test_guild_id_1", moder_role_id="test_role_id_2"),
            mock.MagicMock(guild_id="test_guild_id_2", moder_role_id="test_role_id_3"),
        ]

        import usagiBot.src.UsagiUtils as UsagiUtils
        importlib.reload(UsagiUtils)
        self.Usagi_Utils = UsagiUtils

        self.bot = mock.MagicMock()

        self.ctx = mock.AsyncMock()
        self.ctx.author.name = "test_author"

        self.message = mock.AsyncMock()

        self.error = mock.MagicMock()
        self.error.__str__.return_value = 'test_error_message'
        self.user = mock.AsyncMock()
        self.ctx.command.name = "test_command_name"
        self.ctx.author.mention = "test_author_mention"
        self.ctx.channel.id = "test_channel_id"
        self.ctx.message.id = "test_message_id"
        self.ctx.args = "test_args"
        self.ctx.kwargs = "test_kwargs"

        self.ctx.bot.fetch_user.return_value = self.user

    async def test_error_notification_to_owner(self) -> None:
        await self.Usagi_Utils.error_notification_to_owner(ctx=self.ctx, error=self.error)
        self.user.send.assert_called_with(f"**NEW ERROR OCCURRED**\n> **Command** - test_command_name\n> **User** - test_author_mention\n> **Channel** - test_channel_id\n> **Error** - test_error_message\n> **Error type** - {type(self.error)}\n> **Message** - test_message_id\n> **Args** - test_args\n> **Kwargs** - test_kwargs\n")

    async def test_error_notification_to_owner_app_command(self) -> None:
        await self.Usagi_Utils.error_notification_to_owner(ctx=self.ctx, error=self.error, app_command=True)
        self.user.send.assert_called_with(f"**NEW ERROR OCCURRED**\n> **Command** - test_command_name\n> **User** - test_author_mention\n> **Channel** - test_channel_id\n> **Error** - test_error_message\n> **Error type** - {type(self.error)}\n")

    async def test_load_all_command_tags(self) -> None:
        main_cog = mock.MagicMock()
        main_cog.qualified_name = "Main"
        command_1 = mock.MagicMock()
        command_1.name = "main_command_1"
        command_1.__original_kwargs__ = {"command_tag": "command_tag_command_1"}
        command_2 = mock.MagicMock()
        command_2.name = "main_command_2"
        command_2.__original_kwargs__ = {"command_tag": "command_tag_command_2"}
        main_cog.get_commands.return_value = [command_1, command_2]
        self.bot.cogs.items.return_value = [("Main", main_cog)]

        await self.Usagi_Utils.load_all_command_tags(self.bot)
        self.assertEqual(self.bot.command_tags[0].name, "main_command_1")
        self.assertEqual(self.bot.command_tags[0].value, "command_tag_command_1")
        self.assertEqual(self.bot.command_tags[1].name, "main_command_2")
        self.assertEqual(self.bot.command_tags[1].value, "command_tag_command_2")

    async def test_check_arg_in_command_tags(self) -> None:
        tags = [
            discord.OptionChoice(
                name="main_command_1",
                value="command_tag_command_1",
            ),
            discord.OptionChoice(
                name="main_command_2",
                value="command_tag_command_2",
            )
        ]
        response = self.Usagi_Utils.check_arg_in_command_tags("command_tag_command_1", tags)
        self.assertTrue(response)

    async def test_check_arg_in_command_tags_false(self) -> None:
        response = self.Usagi_Utils.check_arg_in_command_tags("asdasdasd", [])
        self.assertFalse(response)

    async def test_init_cogs_settings(self) -> None:
        response = await self.Usagi_Utils.init_cogs_settings()
        self.assertEqual(response, {
            "test_guild_id_1": {
                "test_module_id_1": True,
                "test_module_id_2": False
            },
            "test_guild_id_2": {
                "test_module_id_3": True,
            }
        })

    async def test_init_moder_roles(self) -> None:
        response = await self.Usagi_Utils.init_moder_roles()
        self.assertEqual(response, {
            "test_guild_id_1": [
                "test_role_id_1",
                "test_role_id_2",
            ],
            "test_guild_id_2": [
                "test_role_id_3",
            ]
        })
