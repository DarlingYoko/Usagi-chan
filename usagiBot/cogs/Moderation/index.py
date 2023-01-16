import discord
from discord.ext import commands
from usagiBot.db.models import UsagiConfig, UsagiCogs, UsagiModerRoles
from usagiBot.src.UsagiUtils import check_arg_in_command_tags
from usagiBot.src.UsagiChecks import check_member_is_moder
from typing import Union, List


def get_command_tags(ctx: discord.AutocompleteContext) -> List[discord.commands.options.OptionChoice]:
    """
    Returns a list of command tags.
    """
    return ctx.bot.command_tags


def get_bot_cogs(ctx: discord.AutocompleteContext) -> List:
    """
    Returns a list of command tags.
    """
    no_access_cogs = ["Events", "Moderation"]
    cogs = []
    for name in ctx.bot.cogs:
        if name not in no_access_cogs:
            cogs.append(name)
    return cogs


class Moderation(commands.Cog):
    def __init__(self, bot):
        pass

    def cog_check(self, ctx):
        return check_member_is_moder(ctx)

    @commands.slash_command(name="set_up_command", description="Set up dettings for command")
    @discord.commands.option(
        name="command",
        description="Pick a command!",
        autocomplete=get_command_tags,
        required=True,
    )
    async def add_config_for_command(
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
        name="delete_settings", description="Delete settings for command"
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
        guild_id = ctx.guild.id
        guild_cogs_settings = ctx.bot.guild_cogs_settings

        if module not in get_bot_cogs(ctx):
            await ctx.respond(
                "This module is't available.", ephemeral=True
            )
            return

        if (
            guild_id in guild_cogs_settings and
            module in guild_cogs_settings[guild_id]
        ):
            await ctx.respond(
                "This module already enabled.", ephemeral=True
            )
            return

        await UsagiCogs.create(
            guild_id=guild_id,
            module_name=module,
            access=True,
        )
        if guild_id in guild_cogs_settings:
            guild_cogs_settings[guild_id][module] = True
        else:
            guild_cogs_settings[guild_id] = {module: True}

        await ctx.respond(
            f"The `{module}` module has been enabled.", ephemeral=True
        )
        return

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
    ) -> None:
        guild_id = ctx.guild.id
        guild_cogs_settings = ctx.bot.guild_cogs_settings

        if module not in get_bot_cogs(ctx):
            await ctx.respond(
                "This module is't available.", ephemeral=True
            )
            return

        if (
            guild_id not in guild_cogs_settings or
            (guild_id in guild_cogs_settings and module not in guild_cogs_settings[guild_id])
        ):
            await ctx.respond(
                "This module isn't enabled.", ephemeral=True
            )
            return

        await UsagiCogs.delete(
            guild_id=guild_id,
            module_name=module,
        )

        del guild_cogs_settings[guild_id][module]
        if len(guild_cogs_settings) == 0:
            del guild_cogs_settings[guild_id]

        await ctx.respond(
            f"The `{module}` module has been disabled.", ephemeral=True
        )
        return

    @commands.slash_command(name="add_moder_role", description="Add new moder role for guild")
    @discord.commands.option(
        name="member_role",
        description="Pick a Role!",
        required=True,
    )
    async def add_new_moder_role(
            self,
            ctx,
            member_role: Union[discord.Role],
    ) -> None:
        guild_id = ctx.guild.id
        moder_roles = ctx.bot.moder_roles
        if (
            guild_id in moder_roles and
            member_role.id in moder_roles[guild_id]
        ):
            await ctx.respond("This role already added.", ephemeral=True)
            return

        await UsagiModerRoles.create(
            guild_id=guild_id,
            moder_role_id=member_role.id,
        )
        if guild_id in moder_roles:
            moder_roles[guild_id].append(member_role.id)
        else:
            moder_roles[guild_id] = [member_role.id]

        await ctx.respond(
            f"The `{member_role}` role has been added.", ephemeral=True
        )
        return

    @commands.slash_command(name="remove_moder_role", description="Remove moder role from guild")
    @discord.commands.option(
        name="member_role",
        description="Pick a Role!",
        required=True,
    )
    async def remove_moder_role(
            self,
            ctx,
            member_role: Union[discord.Role],
    ) -> None:
        guild_id = ctx.guild.id
        moder_roles = ctx.bot.moder_roles

        if (
            guild_id not in moder_roles or
            (guild_id in moder_roles and member_role.id not in moder_roles[guild_id])
        ):
            await ctx.respond("This role isn't moderation.", ephemeral=True)
            return

        await UsagiModerRoles.delete(
            guild_id=guild_id,
            moder_role_id=member_role.id,
        )

        moder_roles[guild_id].remove(member_role.id)
        if len(moder_roles[guild_id]) == 0:
            del moder_roles[guild_id]

        await ctx.respond(
            f"The `{member_role}` role has been removed.", ephemeral=True
        )
        return

    @commands.slash_command(name="show_moder_roles", description="Show all moder roles from that guild")
    async def remove_moder_role(
            self,
            ctx,
    ) -> None:
        guild_id = ctx.guild.id
        moder_roles = ctx.bot.moder_roles
        if guild_id not in moder_roles:
            await ctx.respond("This guild doesn't have any Moderation roles", ephemeral=True)
            return

        result_text = "All moderation roles:\n"
        counter = 1
        for role_id in moder_roles[guild_id]:
            result_text += f"{counter}. <@&{role_id}>\n"
            counter += 1

        await ctx.respond(result_text, ephemeral=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
