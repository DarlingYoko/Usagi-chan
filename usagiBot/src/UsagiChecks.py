from typing import Any, Optional

from discord.ext import commands
from discord import DMChannel, ApplicationContext

from usagiBot.src.UsagiErrors import *
from usagiBot.cogs.Main.schemas import UsagiConfig
from usagiBot.env import BOT_OWNER

# A role with any of these is a staff role: binding it to a public reaction
# is a privilege grant, so only administrators may do it.
ELEVATED_PERMISSIONS = (
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "manage_webhooks",
    "manage_messages",
    "manage_nicknames",
    "manage_emojis",
    "manage_events",
    "manage_threads",
    "kick_members",
    "ban_members",
    "moderate_members",
    "mention_everyone",
)


def require_guild(ctx: Any) -> bool:
    """Guild-only commands: answer DMs with NoPrivateMessage instead of crashing on ctx.guild."""
    if ctx.guild is None:
        raise commands.NoPrivateMessage()
    return True


def guild_cog_check(cog: Any, ctx: Any) -> bool:
    """cog_check for toggleable cogs whose commands all need a guild."""
    require_guild(ctx)
    if check_cog_whitelist(cog, ctx):
        return True
    raise UsagiModuleDisabledError()


def check_is_already_set_up():
    async def predicate(ctx):
        require_guild(ctx)
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

        raise UsagiCallFromWrongChannelError(channel_id=config.generic_id)

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


def _is_guild_or_bot_owner(ctx: Any) -> bool:
    return ctx.author.id in (ctx.guild.owner_id, BOT_OWNER)


def check_member_is_moder(ctx):
    require_guild(ctx)
    moder_roles = ctx.bot.moder_roles
    guild_id = ctx.guild.id
    member_roles = ctx.author.roles

    guild_moder_role_ids = moder_roles.get(guild_id, [])
    member_role_ids = list(map(lambda x: x.id, member_roles))
    if set(member_role_ids) & set(guild_moder_role_ids):
        return True

    if ctx.author.guild_permissions.administrator:
        return True

    if ctx.author.id == BOT_OWNER:
        return True

    raise UsagiCallFromNotModerError()


def check_member_is_admin(ctx: Any) -> bool:
    """Server administrators, the server owner or the bot owner — not bot-configured moderators."""
    require_guild(ctx)
    if ctx.author.guild_permissions.administrator or _is_guild_or_bot_owner(ctx):
        return True
    raise UsagiCallFromNotAdminError()


def check_member_can_pin(ctx: Any) -> bool:
    """Pinning through the bot needs Manage Messages or a bot moderator role."""
    require_guild(ctx)
    if ctx.author.guild_permissions.manage_messages:
        return True
    return check_member_is_moder(ctx)


def role_grant_error(member: Any, role: Any) -> Optional[str]:
    """
    Why `member` may not hand out `role` through the bot (an i18n key),
    or None when it is allowed. The bot assigns with its own permissions,
    so without this a moderator could give themselves any role below the bot.
    """
    if role.is_default() or role.managed:
        return "This role can't be given out"
    if not role.is_assignable():
        return "This role is above my highest role"
    if member.id in (member.guild.owner_id, BOT_OWNER):
        return None
    if role.position >= member.top_role.position:
        return "You can only give out roles below your highest role"
    elevated = any(getattr(role.permissions, name) for name in ELEVATED_PERMISSIONS)
    if elevated and not member.guild_permissions.administrator:
        return "Only administrators can give out roles with moderation permissions"
    return None


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == BOT_OWNER

    return commands.check(predicate)
