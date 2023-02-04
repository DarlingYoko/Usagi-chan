import importlib
import os
from unittest import IsolatedAsyncioTestCase
from unittest import mock

import discord
from sqlalchemy.ext import asyncio

from usagiBot.src.UsagiErrors import *

os.environ["BOT_OWNER"] = "11111"
os.environ["BOT_ID"] = "1234567890"


class TestCheckMethods(IsolatedAsyncioTestCase):

    @mock.patch("usagiBot.db.models.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine, mock_UsagiConfig) -> None:
        self.mock_UsagiConfig = mock_UsagiConfig

        import usagiBot.src.UsagiChecks as UsagiChecks
        importlib.reload(UsagiChecks)
        self.UsagiChecks = UsagiChecks

        self.bot = mock.MagicMock()

        self.ctx = mock.AsyncMock()
        self.ctx.author.name = "test_author"
        self.ctx.guild.id = "test_guild_id"
        self.ctx.channel.id = "test_channel_id"

        self.message = mock.AsyncMock()

    async def test_check_is_already_set_up(self) -> None:
        command = mock.MagicMock()
        command.__original_kwargs__ = {"command_tag": "test_command_tag"}
        command.parent = None
        self.ctx.command = command
        self.mock_UsagiConfig.get.return_value = "test_config_return"
        try:
            respone = await self.UsagiChecks.check_is_already_set_up().predicate(self.ctx)
        except UsagiNotSetUpError:
            self.fail("check_is_already_set_up() raised UsagiNotSetUpError unexpectedly!")

        self.mock_UsagiConfig.get.assert_called_with(guild_id="test_guild_id", command_tag="test_command_tag")
        self.assertEqual(respone, "test_config_return")

    async def test_check_is_already_set_up_no_command_tag(self) -> None:
        command = mock.MagicMock()
        command.__original_kwargs__ = {}
        command.parent = None
        self.ctx.command = command

        with self.assertRaises(UsagiNotSetUpError):
            await self.UsagiChecks.check_is_already_set_up().predicate(self.ctx)

    async def test_check_is_already_set_up_no_config_return(self) -> None:
        command = mock.MagicMock()
        command.__original_kwargs__ = {"command_tag": "test_command_tag"}
        command.parent = None
        self.mock_UsagiConfig.get.return_value = None
        self.ctx.command = command

        with self.assertRaises(UsagiNotSetUpError):
            await self.UsagiChecks.check_is_already_set_up().predicate(self.ctx)

        self.mock_UsagiConfig.get.assert_called_with(guild_id="test_guild_id", command_tag="test_command_tag")

    async def test_check_correct_channel_command(self) -> None:
        command = mock.MagicMock()
        command.__original_kwargs__ = {"command_tag": "test_command_tag"}
        command.parent = None
        self.ctx.command = command
        self.mock_UsagiConfig.get.return_value = mock.MagicMock(generic_id="test_channel_id")
        try:
            respone = await self.UsagiChecks.check_correct_channel_command().predicate(self.ctx)
        except UsagiNotSetUpError:
            self.fail("check_correct_channel_command() raised UsagiNotSetUpError unexpectedly!")
        except UsagiCallFromWrongChannelError:
            self.fail("check_correct_channel_command() raised UsagiCallFromWrongChannelError unexpectedly!")

        self.mock_UsagiConfig.get.assert_called_with(guild_id="test_guild_id", command_tag="test_command_tag")
        self.assertTrue(respone)

    async def test_check_correct_channel_command_wrong_channel(self) -> None:
        command = mock.MagicMock()
        command.__original_kwargs__ = {"command_tag": "test_command_tag"}
        command.parent = None
        self.ctx.command = command
        self.mock_UsagiConfig.get.return_value = mock.MagicMock(generic_id="test_channel_id_2")

        with self.assertRaises(UsagiCallFromWrongChannelError):
            await self.UsagiChecks.check_correct_channel_command().predicate(self.ctx)

        self.mock_UsagiConfig.get.assert_called_with(guild_id="test_guild_id", command_tag="test_command_tag")

    async def test_check_cog_whitelist(self) -> None:
        self.ctx.bot.guild_cogs_settings = {
            "test_guild_id": {"test_cog_name": True}
        }
        cog = mock.MagicMock(qualified_name="test_cog_name")
        respone = self.UsagiChecks.check_cog_whitelist(cog, self.ctx)

        self.assertTrue(respone)

    async def test_check_cog_whitelist_from_DMC(self) -> None:
        self.ctx.message.channel = mock.MagicMock(spec=discord.DMChannel)
        cog = mock.MagicMock(qualified_name="test_cog_name")
        respone = self.UsagiChecks.check_cog_whitelist(cog, self.ctx)

        self.assertTrue(respone)

    async def test_check_cog_whitelist_not_in(self) -> None:
        self.ctx.bot.guild_cogs_settings = {
            "test_guild_id": {}
        }
        cog = mock.MagicMock()
        respone = self.UsagiChecks.check_cog_whitelist(cog, self.ctx)

        self.assertFalse(respone)

    async def test_check_member_is_moder_have_moder_role(self) -> None:
        self.ctx.author.id = "test_author_id"
        self.ctx.author.guild_permissions.administrator = False
        self.ctx.bot.moder_roles = {"test_guild_id": [1, 2, 3, 4]}
        self.ctx.author.roles = [mock.MagicMock(id=2), mock.MagicMock(id=5), mock.MagicMock(id=456)]

        try:
            respone = self.UsagiChecks.check_member_is_moder(self.ctx)
        except UsagiCallFromNotModerError:
            self.fail("check_member_is_moder() raised UsagiCallFromNotModerError unexpectedly!")

        self.assertTrue(respone)

    async def test_check_member_is_moder_admin(self) -> None:
        self.ctx.author.id = "test_author_id"
        self.ctx.author.guild_permissions.administrator = True
        self.ctx.bot.moder_roles = {}
        self.ctx.author.roles = []
        try:
            respone = self.UsagiChecks.check_member_is_moder(self.ctx)
        except UsagiCallFromNotModerError:
            self.fail("check_member_is_moder() raised UsagiCallFromNotModerError unexpectedly!")

        self.assertTrue(respone)

    async def test_check_member_is_moder_me(self) -> None:
        self.ctx.author.id = 290166276796448768
        self.ctx.author.guild_permissions.administrator = False
        self.ctx.bot.moder_roles = {}
        self.ctx.author.roles = []
        try:
            respone = self.UsagiChecks.check_member_is_moder(self.ctx)
        except UsagiCallFromNotModerError:
            self.fail("check_member_is_moder() raised UsagiCallFromNotModerError unexpectedly!")

        self.assertTrue(respone)

    async def test_check_member_is_moder_failed(self) -> None:
        self.ctx.author.id = "test_author_id"
        self.ctx.author.guild_permissions.administrator = False
        self.ctx.bot.moder_roles = {}
        self.ctx.author.roles = []

        with self.assertRaises(UsagiCallFromNotModerError):
            self.UsagiChecks.check_member_is_moder(self.ctx)

