from typing import Callable

from discord.ext import commands
from discord.ext.commands.core import T

from usagiBot.src.UsagiUtils import check_command_tag_in_db
from usagiBot.src.UsagiErrors import UsagiNotSetUpError, UsagiCallFromNotModer


def check_is_already_set_up():
    async def predicate(ctx):
        command_tag = ctx.command.__original_kwargs__.get("command_tag")
        if not command_tag:
            raise UsagiNotSetUpError()

        checker = await check_command_tag_in_db(ctx, command_tag)
        if checker:
            return True
        else:
            raise UsagiNotSetUpError()

    return commands.check(predicate)


def check_cog_whitelist(cog, ctx) -> bool:
    guild_cogs_settings = ctx.bot.guild_cogs_settings
    guild_id = ctx.guild.id
    cog_name = cog.qualified_name

    if guild_id in guild_cogs_settings and cog_name in guild_cogs_settings[guild_id]:
        return guild_cogs_settings[guild_id][cog_name]

    return False


def check_member_is_moder() -> Callable[[T], T]:
    async def predicate(ctx):
        moder_roles = ctx.bot.moder_roles
        guild_id = ctx.guild.id
        member_roles = ctx.author.roles

        if guild_id in moder_roles:
            for role_id in moder_roles[guild_id]:
                for member_role in member_roles:
                    if role_id == member_role.id:
                        return True

        if ctx.author.id == 290166276796448768:
            return True

        raise UsagiCallFromNotModer()

    return commands.check(predicate)
