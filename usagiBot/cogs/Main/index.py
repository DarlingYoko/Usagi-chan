import discord
from discord.ext import commands
from unittest.mock import MagicMock

from usagiBot.src.UsagiErrors import *
from usagiBot.db.models import UsagiConfig


class Main(commands.Cog):
    def __init__(self, bot):
        pass

    @commands.slash_command(name="help", description="Show help for commands")
    async def help_command(
            self,
            ctx,
    ) -> None:
        types = {
            discord.ext.commands.core.Command: "Default commands",
            discord.commands.core.SlashCommand: "Slash commands",
            discord.commands.core.MessageCommand: "Message commands",
            discord.commands.core.UserCommand: "User commands",
            discord.commands.SlashCommandGroup: "Slash command group"
        }
        skip_cogs = ["events"]
        skip_commands = ["help"]
        answer = ""

        for cog_name, cog in ctx.bot.cogs.items():
            if cog_name in skip_cogs:
                continue
            if cog:
                try:
                    cog.cog_check(ctx)
                except UsagiModuleDisabledError:
                    continue
                answer += f"**{cog.qualified_name}**\n"
                commands_dict = {}
                for command in cog.get_commands():
                    if command.name in skip_commands:
                        continue
                    command_dict = {
                        "name": command.name,
                        "set_up": True,
                        "channel_id": None,
                    }
                    for check in command.checks:
                        try:
                            mock_ctx = MagicMock()
                            mock_ctx.command = command
                            mock_ctx.guild.id = ctx.guild.id
                            response = await check(mock_ctx)

                            if isinstance(response, UsagiConfig):
                                command_dict["channel_id"] = response.generic_id

                        except discord.errors.CheckFailure:
                            pass
                        except UsagiNotSetUpError:
                            command_dict["set_up"] = False
                        except UsagiCallFromWrongChannelError as e:
                            command_dict["channel_id"] = e.channel_id

                    command_type = types.get(type(command))
                    if command_type in commands_dict.keys():
                        commands_dict[command_type].append(command_dict)
                    else:
                        commands_dict[command_type] = [command_dict]
                for item, value in commands_dict.items():
                    answer += f"\t*{item}*\n"
                    for command in value:
                        answer += f"> \t\t{command['name']} "
                        if not command["set_up"]:
                            answer += "**-> command isn't configured**"
                        if command["channel_id"]:
                            answer += f"**-> <#{command['channel_id']}>**"
                        answer += "\n"
                    answer += "\n"
                answer += "\n"
        await ctx.respond(content=answer, ephemeral=True)


def setup(bot):
    bot.add_cog(Main(bot))
