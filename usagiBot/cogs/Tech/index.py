from discord import SlashCommandGroup
from discord.ext import commands
from datetime import timedelta

from discord.ext.commands import ColorConverter

from usagiBot.src.UsagiChecks import check_cog_whitelist, check_correct_channel_command
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.cogs.Tech.tech_utils import *


class Tech(commands.Cog):
    def __init__(self, bot):
        pass

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @commands.message_command(name="Pin message")
    async def pin_message(self, ctx, message: discord.Message) -> None:
        await message.pin(reason=f"Pinned by {ctx.author.name}")
        await ctx.respond(f"Message was pinned", ephemeral=True)

    @commands.slash_command(name="sleep", description="Go to sleep for N hours")
    @discord.commands.option(
        name="hours",
        description="Insert sleep hours!",
        autocomplete=lambda x: range(2, 25, 2),
        required=True,
    )
    async def go_sleep(
            self,
            ctx,
            hours: int,
    ) -> None:
        if not (2 <= hours <= 24):
            await ctx.respond("You entered the wrong amount of time.", ephemeral=True)
            return
        duration = timedelta(hours=hours)
        await ctx.author.timeout_for(duration=duration, reason="Timeout for sleep")
        await ctx.respond(f"Good night, see you in {hours} hours.", ephemeral=True)

    unic_role = SlashCommandGroup(
        name="unic_role",
        description="Customize your own role on the server!",
        checks=[
            check_correct_channel_command().predicate
        ],
        command_tag="customize_role",
    )

    customize_role_modify = unic_role.create_subgroup(
        name="modify",
        description="Modify an already created role!",
    )

    @unic_role.command(name="create", description="Create your own role for yourself.")
    @discord.commands.option(
        name="name",
        description="Name for the new role",
        required=True,
    )
    @discord.commands.option(
        name="color",
        description="Color for the new role in hexadecimal",
        required=True,
    )
    async def create_new_unic_role(
            self,
            ctx,
            name: str,
            color: ColorConverter
    ) -> None:
        role = await ctx.guild.create_role(
            name=name,
            colour=color,
            hoist=True,
            mentionable=True,
            reason=f"New role by {ctx.author.name}, id = {ctx.author.id}"
        )
        await ctx.author.add_roles(role)
        await UsagiUnicRoles.create(
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            role_id=role.id,
        )
        await ctx.respond(f"Created a new role for you. :point_right::skin-tone-1: {role.mention}", ephemeral=True)

    @unic_role.command(name="delete", description="Delete your role.")
    @discord.commands.option(
        name="role",
        description="Pick a role to delete.",
        required=True,
        autocomplete=get_user_roles,
    )
    async def delete_unic_role(
            self,
            ctx,
            role,
    ) -> None:
        role = await get_user_role(ctx, role)
        if role:
            await UsagiUnicRoles.delete(
                guild_id=ctx.guild.id,
                user_id=ctx.author.id,
                role_id=role.id,
            )
            await ctx.author.remove_roles(role)
            await ctx.respond("Successfully removed your role", ephemeral=True)

    @customize_role_modify.command(name="name", description="Change name of your role.")
    @discord.commands.option(
        name="role",
        description="Pick a role to rename.",
        required=True,
        autocomplete=get_user_roles,
    )
    async def rename_unic_role(
            self,
            ctx,
            role,
            new_name: str
    ) -> None:
        role = await get_user_role(ctx, role)
        if role:
            await role.edit(name=new_name)
            await ctx.respond(
                f"Successfully renamed your role :point_right::skin-tone-1: {role.mention}",
                ephemeral=True
            )

    @customize_role_modify.command(name="color", description="Change color of your role.")
    @discord.commands.option(
        name="role",
        description="Pick a role to recolor.",
        required=True,
        autocomplete=get_user_roles,
    )
    async def recolor_unic_role(
            self,
            ctx,
            role,
            new_color: ColorConverter
    ) -> None:
        role = await get_user_role(ctx, role)
        if role:
            await role.edit(color=new_color)
            await ctx.respond(
                f"Successfully recolored your role :point_right::skin-tone-1: {role.mention}",
                ephemeral=True
            )


def setup(bot):
    bot.add_cog(Tech(bot))
