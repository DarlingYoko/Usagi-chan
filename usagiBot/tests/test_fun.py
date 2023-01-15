from usagiBot.cogs.Fun import fun_utils
from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase


class TestFunMethods(IsolatedAsyncioTestCase):

    @mock.patch("usagiBot.db.models.UsagiConfig")
    @mock.patch.object(asyncio, "create_async_engine")
    @mock.patch.object(fun_utils, "get_exchange_rate_data")
    def setUp(self, mock_get_exchange_rate_data, mock_engine, mock_UsagiConfig) -> None:
        self.bot = mock.AsyncMock()

        from usagiBot.cogs.Fun.index import Fun
        self.Fun = Fun(self.bot)

        mock_get_exchange_rate_data.return_value = {
            "USDRUB": {"value": "60", "change": "-0.1"},
            "USDUAH": {"value": "30", "change": "-1"},
            "USDBYN": {"value": "2", "change": "2"},
        }

        self.ctx = mock.AsyncMock()
        self.message = mock.AsyncMock()
        self.channel = mock.AsyncMock()
        config = mock.MagicMock
        mock_UsagiConfig.get_command_tag = mock.AsyncMock()

        self.ctx.author.name = "Yoko"

        self.message.id = "test_message_id"
        self.message.author.mention = "test_author_mention"
        self.message.content = "test_content"
        self.message.attachments = []
        self.message.embeds = []

        config.generic_id = 54321
        mock_UsagiConfig.get_command_tag.return_value = config

    async def test_ping(self) -> None:
        self.ctx.bot.latency = 1
        await self.Fun.ping_to_usagi(self.Fun, self.ctx)
        self.ctx.reply.assert_called_with("Pong! 1000 ms")

    async def test_get_message_id(self) -> None:
        await self.Fun.get_message_id(self.Fun, self.ctx, self.message)
        self.ctx.respond.assert_called_with("Message ID: `test_message_id`")

    async def test_add_based_message_successful(self) -> None:
        self.ctx.guild.id = 12345
        self.ctx.command.__original_kwargs__ = {"command_tag": "based_message_channel"}
        self.ctx.bot.fetch_channel.return_value = self.channel

        await self.Fun.add_based_message(self.Fun, self.ctx, self.message)

        self.ctx.bot.fetch_channel.assert_called_with(54321)
        self.ctx.respond.assert_called_with("Добавила базу <:BASEDHM:897821614312394793>")
        self.channel.send.assert_called_with(
            content="База от test_author_mention\ntest_content",
            files=[],
            embeds=[],
        )

    async def test_get_exchange_rate(self) -> None:

        await self.Fun.get_exchange_rate(self.Fun, self.ctx)

        return_message = (
            "```autohotkey\n"
            "Сводка курса на данный момент:\n"
            "1. USDRUB 60 (-0.1)\n"
            "2. USDUAH 30 (-1)\n"
            "3. USDBYN 2 (2)\n"
            "```"
        )
        self.ctx.reply.assert_called_with(return_message)

    @mock.patch("random.randint")
    async def test_get_user_iq(self, mock_randint) -> None:
        mock_randint.return_value = 69
        await self.Fun.get_user_iq(self.Fun, self.ctx)

        return_message = "Твой iq = 69\n+ секс"
        self.ctx.reply.assert_called_with(return_message)
