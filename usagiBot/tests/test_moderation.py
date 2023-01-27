from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase


class TestModerationMethods(IsolatedAsyncioTestCase):

    @mock.patch("usagiBot.db.models.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine, mock_UsagiConfig) -> None:
        self.bot = mock.AsyncMock()
        self.ctx = mock.AsyncMock()
        self.ctx.guild.id = "test_guild_id"

        self.mock_UsagiConfig = mock_UsagiConfig
        # self.mock_UsagiConfig.create = mock.AsyncMock()
        # self.mock_UsagiConfig.get = mock.AsyncMock()
        # self.mock_UsagiConfig.update = mock.AsyncMock()

        from usagiBot.src import UsagiUtils
        UsagiUtils.check_arg_in_command_tags = mock.MagicMock(return_value=True)

        from usagiBot.cogs.Moderation.index import Moderation
        self.Moderation = Moderation(self.bot)

    async def test_set_up_command_create(self) -> None:
        # self.mock_UsagiConfig.get = mock.AsyncMock()
        self.mock_UsagiConfig.get.return_value = False

        test_command = "test_command"
        channel = mock.MagicMock()
        channel.id = "test_channel_id"
        await self.Moderation.add_config_for_command(self.ctx, test_command, channel)

        self.mock_UsagiConfig.create.assert_called_with(
            guild_id="test_guild_id",
            command_tag="test_command",
            generic_id="test_channel_id"
        )
        self.ctx.respond.assert_called_with(content="Successfully configured channel for command", ephemeral=True)

    async def test_set_up_command_update(self) -> None:
        config = mock.MagicMock()
        config.id = "test_id"
        # self.mock_UsagiConfig.get = mock.AsyncMock()
        self.mock_UsagiConfig.get.return_value = config

        test_command = "test_command"
        channel = mock.MagicMock()
        channel.id = "test_channel_id"
        await self.Moderation.add_config_for_command(self.ctx, test_command, channel)

        self.mock_UsagiConfig.update.assert_called_with(
            id="test_id",
            guild_id="test_guild_id",
            command_tag="test_command",
            generic_id="test_channel_id"
        )
        self.ctx.respond.assert_called_with(content="Successfully reconfigured channel for command", ephemeral=True)
