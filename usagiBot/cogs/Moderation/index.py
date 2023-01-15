import discord
from discord import Cog
from discord.ext import commands
from usagiBot.db.models import UsagiConfig
from usagiBot.src.UsagiUtils import check_arg_in_command_tags
from typing import Union, List, Mapping


def get_command_tags(ctx: discord.AutocompleteContext) -> List[discord.commands.options.OptionChoice]:
    """
    Returns a list of command tags.
    """
    return ctx.bot.command_tags


def get_bot_cogs(ctx: discord.AutocompleteContext) -> Mapping[str, Cog]:
    """
    Returns a list of command tags.
    """
    return ctx.bot.cogs


class Moderation(commands.Cog):
    def __init__(self, bot):
        pass

    @commands.slash_command(description="Set Up Command")
    @discord.commands.option(
        name="command",
        description="Pick a command!",
        autocomplete=get_command_tags,
        required=True,
    )
    async def set_up_command(
        self,
        ctx,
        command: str,
        channel: Union[discord.TextChannel, discord.VoiceChannel],
    ) -> None:

        if not check_arg_in_command_tags(command, ctx.bot.command_tags):
            await ctx.respond(
                "This argument does not exist for commands.", ephemeral=True
            )
            return

        command_config_exist = await UsagiConfig.get(guild_id=ctx.guild.id, command_tag=command)
        text_result = "Successfully configured channel for command"
        if command_config_exist:
            await UsagiConfig.update(
                id=command_config_exist.id,
                guild_id=ctx.guild.id,
                command_tag=command,
                generic_id=channel.id
            )
            text_result = "Successfully reconfigured channel for command"
        else:
            await UsagiConfig.create(
                guild_id=ctx.guild.id,
                command_tag=command,
                generic_id=channel.id
            )

        await ctx.respond(content=text_result, ephemeral=True)

    @commands.slash_command(
        name="delete_settings", description="Delete Settings For Command"
    )
    @discord.commands.option(
        name="command",
        description="Pick a command!",
        autocomplete=get_command_tags,
        required=True,
    )
    async def delete_config_for_command(
        self,
        ctx,
        command: str,
        # channel: Union[discord.TextChannel, discord.VoiceChannel]
    ) -> None:

        if not check_arg_in_command_tags(command, ctx.bot.command_tags):
            await ctx.respond(
                "This argument does not exist for commands.", ephemeral=True
            )
            return

        await UsagiConfig.delete(guild_id=ctx.guild.id, command_tag=command)

        await ctx.respond("Successfully deleted configure for command", ephemeral=True)

    @commands.slash_command(
        name="enable_module", description="Enable module in bot"
    )
    @discord.commands.option(
        name="module",
        description="Pick a module!",
        autocomplete=get_bot_cogs,
        required=True,
    )
    async def enable_module(
            self,
            ctx,
            module: str,
    ) -> None:
        pass

    @commands.slash_command(
        name="disable_module", description="Disable module in bot"
    )
    @discord.commands.option(
        name="module",
        description="Pick a module!",
        autocomplete=get_bot_cogs,
        required=True,
    )
    async def disable_module(
            self,
            ctx,
            module: str,
            # channel: Union[discord.TextChannel, discord.VoiceChannel]
    ) -> None:
        pass


def setup(bot):
    bot.add_cog(Moderation(bot))
