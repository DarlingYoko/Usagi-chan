from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase


class TestModerationMethods(IsolatedAsyncioTestCase):

    @classmethod
    @mock.patch("usagiBot.db.models.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch("usagiBot.db.models.UsagiCogs", new_callable=mock.AsyncMock)
    @mock.patch("usagiBot.db.models.UsagiModerRoles", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    def setUpClass(cls, mock_engine, mock_UsagiModerRoles, mock_UsagiCogs, mock_UsagiConfig) -> None:
        cls.ctx = mock.AsyncMock()
        cls.ctx.guild.id = "test_guild_id"
        cls.ctx.bot.cogs = ["Fun", "Tech", "Wordle"]
        cls.bot = mock.AsyncMock()

        cls.mock_UsagiConfig = mock_UsagiConfig
        cls.mock_UsagiCogs = mock_UsagiCogs
        cls.mock_UsagiModerRoles = mock_UsagiModerRoles

        from usagiBot.src import UsagiUtils
        cls.UsagiUtils = UsagiUtils
        cls.UsagiUtils.check_arg_in_command_tags = mock.MagicMock()

        from usagiBot.cogs.Moderation.index import Moderation
        cls.Moderation = Moderation(cls.bot)

        cls.test_command = "test_command"
        cls.channel = mock.MagicMock()
        cls.channel.id = "test_channel_id"

        cls.moder_role = mock.MagicMock()
        cls.moder_role.id = "test_moder_role_id"
        cls.moder_role.mention = "test_moder_role_mention"

    async def test_set_up_command_create(self) -> None:
        self.UsagiUtils.check_arg_in_command_tags.return_value = True
        self.mock_UsagiConfig.get = mock.AsyncMock()
        self.mock_UsagiConfig.get.return_value = False

        await self.Moderation.add_config_for_command(self.ctx, self.test_command, self.channel)

        self.mock_UsagiConfig.create.assert_called_with(
            guild_id="test_guild_id",
            command_tag="test_command",
            generic_id="test_channel_id"
        )
        self.ctx.respond.assert_called_with(content="Successfully configured channel for command.", ephemeral=True)

    async def test_set_up_command_update(self) -> None:
        self.UsagiUtils.check_arg_in_command_tags.return_value = True

        config = mock.MagicMock()
        config.id = "test_id"
        self.mock_UsagiConfig.get.return_value = config

        await self.Moderation.add_config_for_command(self.ctx, self.test_command, self.channel)

        self.mock_UsagiConfig.update.assert_called_with(
            id="test_id",
            guild_id="test_guild_id",
            command_tag="test_command",
            generic_id="test_channel_id"
        )
        self.ctx.respond.assert_called_with(content="Successfully reconfigured channel for command.", ephemeral=True)

    async def test_delete_config_for_command(self) -> None:
        self.UsagiUtils.check_arg_in_command_tags.return_value = True

        await self.Moderation.delete_config_for_command(self.ctx, self.test_command)
        self.mock_UsagiConfig.delete.assert_called_with(guild_id=self.ctx.guild.id, command_tag=self.test_command)
        self.ctx.respond.assert_called_with(content="Successfully deleted configure for command.", ephemeral=True)

    async def test_delete_config_for_command_not_in_tags(self) -> None:
        self.UsagiUtils.check_arg_in_command_tags.return_value = False

        await self.Moderation.delete_config_for_command(self.ctx, self.test_command)
        self.ctx.respond.assert_called_with(content="This argument does not exist for commands.", ephemeral=True)

    async def test_enable_module(self) -> None:
        self.ctx.bot.guild_cogs_settings = {}
        await self.Moderation.enable_module(self.ctx, "Fun")

        self.mock_UsagiCogs.create.assert_called_with(
            guild_id="test_guild_id",
            module_name="Fun",
            access=True,
        )
        self.ctx.respond.assert_called_with(content="The `Fun` module has been enabled.", ephemeral=True)
        self.assertEqual(self.ctx.bot.guild_cogs_settings, {"test_guild_id": {"Fun": True}})

    async def test_enable_module_isnt_available(self) -> None:
        self.ctx.bot.guild_cogs_settings = {}
        await self.Moderation.enable_module(self.ctx, "Moderation")

        self.ctx.respond.assert_called_with(content="This module isn't available.", ephemeral=True)

    async def test_enable_module_is_already_enabled(self) -> None:
        self.ctx.bot.guild_cogs_settings = {
            "test_guild_id": {"Fun": True}
        }
        await self.Moderation.enable_module(self.ctx, "Fun")

        self.ctx.respond.assert_called_with(content="This module already enabled.", ephemeral=True)

    async def test_disable_module(self) -> None:
        self.ctx.bot.guild_cogs_settings = {
            "test_guild_id": {"Fun": True}
        }
        await self.Moderation.disable_module(self.ctx, "Fun")

        self.mock_UsagiCogs.delete.assert_called_with(
            guild_id="test_guild_id",
            module_name="Fun",
        )
        self.ctx.respond.assert_called_with(content="The `Fun` module has been disabled.", ephemeral=True)
        self.assertEqual(self.ctx.bot.guild_cogs_settings, {})

    async def test_disable_module_isnt_available(self) -> None:
        self.ctx.bot.guild_cogs_settings = {}
        await self.Moderation.disable_module(self.ctx, "Moderation")

        self.ctx.respond.assert_called_with(content="This module isn't available.", ephemeral=True)

    async def test_disable_module_is_already_enabled(self) -> None:
        self.ctx.bot.guild_cogs_settings = {}
        await self.Moderation.disable_module(self.ctx, "Fun")

        self.ctx.respond.assert_called_with(content="This module isn't enabled.", ephemeral=True)

    async def test_add_new_moder_role(self) -> None:
        self.ctx.bot.moder_roles = {}

        await self.Moderation.add_new_moder_role(self.ctx, self.moder_role)

        self.mock_UsagiModerRoles.create.assert_called_with(
            guild_id="test_guild_id",
            moder_role_id="test_moder_role_id",
        )
        self.ctx.respond.assert_called_with(
            content="The `test_moder_role_mention` role has been added.",
            ephemeral=True
        )
        self.assertEqual(self.ctx.bot.moder_roles, {"test_guild_id": ["test_moder_role_id"]})

    async def test_add_new_moder_role_already_exist(self) -> None:
        self.ctx.bot.moder_roles = {"test_guild_id": ["test_moder_role_id"]}

        await self.Moderation.add_new_moder_role(self.ctx, self.moder_role)

        self.ctx.respond.assert_called_with(
            content="This role already added.",
            ephemeral=True
        )

    async def test_remove_moder_role(self) -> None:
        self.ctx.bot.moder_roles = {"test_guild_id": ["test_moder_role_id"]}

        await self.Moderation.remove_moder_role(self.ctx, self.moder_role)

        self.mock_UsagiModerRoles.delete.assert_called_with(
            guild_id="test_guild_id",
            moder_role_id="test_moder_role_id",
        )
        self.ctx.respond.assert_called_with(
            content="The `test_moder_role_mention` role has been removed.",
            ephemeral=True
        )
        self.assertEqual(self.ctx.bot.moder_roles, {})

    async def test_remove_moder_role_not_exist(self) -> None:
        self.ctx.bot.moder_roles = {}

        await self.Moderation.remove_moder_role(self.ctx, self.moder_role)

        self.ctx.respond.assert_called_with(
            content="This role isn't moderation.",
            ephemeral=True
        )

    async def test_show_moder_roles(self) -> None:
        self.ctx.bot.moder_roles = {"test_guild_id": ["test_moder_role_id"]}

        await self.Moderation.show_moder_roles(self.ctx)

        self.ctx.respond.assert_called_with(
            content="All moderation roles:\n" + "1. <@&test_moder_role_id>\n",
            ephemeral=True
        )

    async def test_show_moder_roles_no_roles(self) -> None:
        self.ctx.bot.moder_roles = {}

        await self.Moderation.show_moder_roles(self.ctx)

        self.ctx.respond.assert_called_with(
            content="This guild doesn't have any Moderation roles.",
            ephemeral=True
        )

