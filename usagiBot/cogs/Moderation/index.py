import discord
from discord.ext import commands
from usagiBot.db.models import UsagiConfig
from usagiBot.src.UsagiUtils import check_arg_in_command_tags
from typing import Union


def get_command_tags(ctx: discord.AutocompleteContext):
    """Returns a list of colors that begin with the characters entered so far."""
    return ctx.bot.command_tags


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

        await UsagiConfig.create(
            guild_id=ctx.guild.id, command_tag=command, generic_id=channel.id
        )

        await ctx.respond("Successfully configured", ephemeral=True)

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

        await UsagiConfig.delete(guild_id=733631069542416384, command_tag=command)

        await ctx.respond("Successfully configured", ephemeral=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
