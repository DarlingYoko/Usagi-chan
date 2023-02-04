from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase
from discord.ext import commands


class TestEventsMethods(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        self.ctx = mock.AsyncMock()
        self.bot = mock.AsyncMock()

        from usagiBot.cogs.Events.index import Events

        self.ctx.author.name = "Yoko"
        self.Events = Events(self.bot)

    async def test_command_not_found(self) -> None:
        await self.Events.on_command_error(self.ctx, commands.CommandNotFound())
        self.ctx.reply.assert_called_with("This command doesn't exist.", delete_after=120)

    async def test_command_on_cooldown(self) -> None:
        error = commands.CommandOnCooldown(
            cooldown=commands.Cooldown(rate=1, per=60.0),
            retry_after=60.0,
            type=commands.BucketType.user
        )
        await self.Events.on_command_error(self.ctx, error)
        self.ctx.reply.assert_called_with("You can use this command in 60s", delete_after=120)

    async def test_on_command_error(self) -> None:
        user = mock.AsyncMock()
        self.ctx.bot.fetch_user.return_value = user
        self.ctx.command.name = "test_command_name"
        self.ctx.author.mention = "test_author_mention"
        self.ctx.message.id = "test_message"
        self.ctx.channel.id = "test_channel"
        self.ctx.args = "test_args"
        self.ctx.kwargs = "test_kwargs"

        self.error = mock.MagicMock()
        self.error.message = "test_error_message"

        test_error_message = "**NEW ERROR OCCURRED**\n" + \
                             f"> **Command** - test_command_name\n" + \
                             f"> **User** - test_author_mention\n" + \
                             f"> **Channel** - test_channel\n" + \
                             f"> **Error** - test_error_message\n" + \
                             f"> **Error type** - {type(self.error)}\n" + \
                             f"> **Message** - test_message\n" + \
                             f"> **Args** - test_args\n" + \
                             f"> **Kwargs** - test_kwargs\n"
        await self.Events.on_command_error(self.ctx, self.error)
        user.send.assert_called_with(test_error_message)
