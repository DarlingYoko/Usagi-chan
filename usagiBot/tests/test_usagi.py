from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase
from discord.ext import commands


class TestUsagiMethods(IsolatedAsyncioTestCase):

    @mock.patch("usagiBot.db.models.UsagiConfig")
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine, mock_UsagiConfig) -> None:
        self.ctx = mock.AsyncMock()
        self.ctx.author.name = "Yoko"

    async def test_command_not_found(self) -> None:
        from usagiBot.usagi import on_command_error
        await on_command_error(self.ctx, commands.CommandNotFound())
        self.ctx.reply.assert_called_with("Такой команды не существует.")

    async def test_command_on_cooldown(self) -> None:
        from usagiBot.usagi import on_command_error
        error = commands.CommandOnCooldown(
            cooldown=commands.Cooldown(rate=1, per=60.0),
            retry_after=60.0,
            type=commands.BucketType.user
        )
        await on_command_error(self.ctx, error)
        self.ctx.reply.assert_called_with("Эту команду ты сможешь использовать через 60s")

    async def test_on_command_error(self) -> None:
        from usagiBot.usagi import on_command_error
        user = mock.AsyncMock()
        self.ctx.bot.fetch_user.return_value = user
        self.ctx.command.name = "test_command_name"
        self.ctx.author.mention = "test_author_mention"
        self.ctx.message.id = "test_message"
        self.ctx.channel.id = "test_channel"
        self.ctx.args = "test_args"
        self.ctx.kwargs = "test_kwargs"

        test_error_message = "**NEW ERROR OCCURRED**\n" + \
                             f"> **Command** - test_command_name\n" + \
                             f"> **User** - test_author_mention\n" + \
                             f"> **Message** - test_message\n" + \
                             f"> **Channel** - test_channel\n" + \
                             f"> **Args** - test_args\n" + \
                             f"> **Kwargs** - test_kwargs\n" + \
                             f"> **Error** - test_error\n"

        await on_command_error(self.ctx, "test_error")
        user.send.assert_called_with(test_error_message)
