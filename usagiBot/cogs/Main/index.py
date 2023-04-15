import discord
from discord.ext import commands
from unittest.mock import MagicMock

from usagiBot.src.UsagiErrors import *
from usagiBot.db.models import UsagiConfig, UsagiSaveRoles
from usagiBot.src.UsagiUtils import get_embed


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
                    command_tag = command.__original_kwargs__.get("command_tag")
                    if command_tag:
                        config = await UsagiConfig.get(guild_id=ctx.guild.id, command_tag=command_tag)
                        if not config:
                            command_dict["set_up"] = False
                        else:
                            command_dict["channel_id"] = config.generic_id

                    command_type = types.get(type(command))
                    command_list = commands_dict.setdefault(command_type, [])
                    command_list.append(command_dict)

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

    @commands.slash_command(
        name="save_roles",
        description="Toggle saving roles on user leave guild",
        command_tag="save_roles_on_leave",
    )
    async def save_roles_on_leave(self, ctx) -> None:
        saving = await UsagiSaveRoles.get(guild_id=ctx.guild.id)
        if saving is None:
            await UsagiSaveRoles.create(guild_id=ctx.guild.id, saving_roles=True)
            return await ctx.respond(
                embed=get_embed(
                    title="Enabled saving roles on member leave.",
                    color=discord.Color.green()
                )
            )
        else:
            if saving.saving_roles:
                await UsagiSaveRoles.update(id=saving.id, saving_roles=False)
                return await ctx.respond(
                    embed=get_embed(
                        title="Disabled saving roles on member leave.",
                        color=discord.Color.green()
                    )
                )
            else:
                await UsagiSaveRoles.update(id=saving.id, saving_roles=True)
                return await ctx.respond(
                    embed=get_embed(
                        title="Enabled saving roles on member leave.",
                        color=discord.Color.green()
                    )
                )


def setup(bot):
    bot.add_cog(Main(bot))
