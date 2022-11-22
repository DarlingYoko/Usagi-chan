from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase


class TestModerationMethods(IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.bot = mock.AsyncMock()

        self.ctx = mock.AsyncMock()
        self.ctx.guild.id = "test_guild_id"

    @mock.patch("usagiBot.db.models.UsagiConfig")
    @mock.patch.object(asyncio, "create_async_engine")
    async def test_set_up_command(self, mock_engine, mock_UsagiConfig) -> None:
        from usagiBot.src import UsagiUtils
        UsagiUtils.check_arg_in_command_tags = mock.MagicMock(return_value=True)
        mock_UsagiConfig.create = mock.AsyncMock()
        from usagiBot.cogs.Moderation.index import Moderation
        self.Moderation = Moderation(self.bot)
        test_command = "test_command"
        channel = mock.MagicMock
        channel.id = "test_channel_id"
        await self.Moderation.set_up_command(self.ctx, test_command, channel)

        mock_UsagiConfig.create.assert_called_with(
            guild_id="test_guild_id",
            command_tag="test_command",
            generic_id="test_channel_id"
        )
        self.ctx.respond.assert_called_with("Successfully configured", ephemeral=True)