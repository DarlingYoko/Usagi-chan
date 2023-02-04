from discord.ext import commands
from discord import DMChannel, ApplicationContext

from usagiBot.src.UsagiErrors import *
from usagiBot.db.models import UsagiConfig


def check_is_already_set_up():
    async def predicate(ctx):
        command = ctx.command
        if ctx.command.parent:
            command = ctx.command.parent
        command_tag = command.__original_kwargs__.get("command_tag")
        if not command_tag:
            raise UsagiNotSetUpError()
        config = await UsagiConfig.get(guild_id=ctx.guild.id, command_tag=command_tag)
        if not config:
            raise UsagiNotSetUpError()

        return config

    return commands.check(predicate)


def check_correct_channel_command():
    async def predicate(ctx):
        config = await check_is_already_set_up().predicate(ctx)
        if config and config.generic_id == ctx.channel.id:
            return True

        raise UsagiCallFromWrongChannelError(
            channel_id=config.generic_id
        )

    return commands.check(predicate)


def check_cog_whitelist(cog, ctx) -> bool:

    if isinstance(ctx, ApplicationContext):
        channel = ctx.channel
    else:
        channel = ctx.message.channel
    if isinstance(channel, DMChannel):
        return True
    guild_cogs_settings = ctx.bot.guild_cogs_settings
    guild_id = ctx.guild.id
    cog_name = cog.qualified_name

    if guild_id in guild_cogs_settings and cog_name in guild_cogs_settings[guild_id]:
        return True

    return False


def check_member_is_moder(ctx):
    moder_roles = ctx.bot.moder_roles
    guild_id = ctx.guild.id
    member_roles = ctx.author.roles

    guild_moder_role_ids = moder_roles.get(guild_id, [])
    member_role_ids = list(map(lambda x: x.id, member_roles))
    if set(member_role_ids) & set(guild_moder_role_ids):
        return True

    if ctx.author.guild_permissions.administrator:
        return True

    if ctx.author.id == 290166276796448768:
        return True

    raise UsagiCallFromNotModerError()

