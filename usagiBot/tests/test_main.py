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

        from usagiBot.src.UsagiUtils import get_embed
        self.get_embed = get_embed

        self.message = mock.AsyncMock()

    async def test_help_command(self) -> None:
        main_cog = mock.MagicMock()
        main_cog.qualified_name = "Main"
        command_1 = mock.MagicMock(__original_kwargs__={})
        command_1.name = "main_command_1"
        command_1.parent = None
        command_1.description = "description_1"
        command_2 = mock.MagicMock(__original_kwargs__={})
        command_2.name = "main_command_2"
        command_2.parent = None
        command_2.description = "description_2"
        main_cog.get_commands.return_value = [command_1, command_2]

        fun_cog = mock.MagicMock()
        self.ctx.bot.cogs = {
            "Main": main_cog,
            "Fun": fun_cog,
        }
        await self.Main.help_command(self.ctx, "Main")
        embed = self.get_embed(
            title="**Main**"
        )
        embed.add_field(name="_ _\n**None**", value="_ _")
        embed.add_field(name="main_command_1", value="Configured - No needed\ndescription_1")
        embed.add_field(name="main_command_2", value="Configured - No needed\ndescription_2")
        self.ctx.respond.assert_called_with(embed=embed, ephemeral=True)


