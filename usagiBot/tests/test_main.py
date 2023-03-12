from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase


class TestMainMethods(IsolatedAsyncioTestCase):

    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Main.index import Main
        self.Main = Main

        self.bot = mock.AsyncMock()
        self.ctx = mock.AsyncMock()
        self.ctx.author.name = "test_author"

        self.message = mock.AsyncMock()

    async def test_help_command(self) -> None:
        main_cog = mock.MagicMock()
        main_cog.qualified_name = "Main"
        command_1 = mock.MagicMock(__original_kwargs__={})
        command_1.name = "main_command_1"
        command_2 = mock.MagicMock(__original_kwargs__={})
        command_2.name = "main_command_2"
        main_cog.get_commands.return_value = [command_1, command_2]

        fun_cog = mock.MagicMock()
        fun_cog.qualified_name = "Fun"
        command_3 = mock.MagicMock(__original_kwargs__={})
        command_3.name = "fun_command_3"
        command_4 = mock.MagicMock(__original_kwargs__={})
        command_4.name = "fun_command_4"
        fun_cog.get_commands.return_value = [command_3, command_4]
        self.ctx.bot.cogs = {
            "Main": main_cog,
            "Fun": fun_cog,
        }
        await self.Main.help_command(self.ctx)

        self.ctx.respond.assert_called_with(content="**Main**\n\t*None*\n> \t\tmain_command_1 \n> \t\tmain_command_2 \n\n\n**Fun**\n\t*None*\n> \t\tfun_command_3 \n> \t\tfun_command_4 \n\n\n", ephemeral=True)
