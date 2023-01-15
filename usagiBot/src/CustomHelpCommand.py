from discord.ext import commands
from usagiBot.src.UsagiErrors import UsagiNotSetUpError, UsagiModuleDisabled
import discord
from unittest.mock import MagicMock


class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        ctx = self.context
        types = {
            discord.ext.commands.core.Command: "Default commands",
            discord.commands.core.SlashCommand: "Slash commands",
            discord.commands.core.MessageCommand: "Message commands",
            discord.commands.core.UserCommand: "User commands"
        }
        answer = ""
        for cog in mapping:
            if cog:
                try:
                    cog.cog_check(ctx)
                except UsagiModuleDisabled:
                    continue
                answer += f"**{cog.qualified_name}**\n"
                commands_dict = {}
                for command in cog.get_commands():
                    command_dict = {
                        "name": command.name,
                        "set_up": True
                    }
                    for check in command.checks:
                        try:
                            mock_ctx = MagicMock()
                            mock_ctx.command = command
                            mock_ctx.guild.id = ctx.guild.id
                            await check(mock_ctx)
                        except discord.errors.CheckFailure:
                            pass
                        except UsagiNotSetUpError:
                            command_dict["set_up"] = False

                    if types[type(command)] in commands_dict.keys():
                        commands_dict[types[type(command)]].append(command_dict)
                    else:
                        commands_dict[types[type(command)]] = [command_dict]
                for item, value in commands_dict.items():
                    answer += f"\t*{item}*\n"
                    for command in value:
                        answer += f"> \t\t{command['name']} "
                        if not command["set_up"]:
                            answer += "**-> command isn't configured**"
                        answer += "\n"
                    answer += "\n"
                answer += "\n"

        await ctx.reply(answer)
