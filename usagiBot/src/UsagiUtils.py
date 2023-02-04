from datetime import datetime
from typing import List, Dict

import discord
from discord.ext.commands._types import Error

from usagiBot.env import BOT_OWNER
from usagiBot.db.models import UsagiCogs, UsagiModerRoles


async def error_notification_to_owner(ctx: discord.ext.commands.Context, error: Error, app_command: bool = False):
    """
    Send error log to bot owner
    :param ctx: Discord Context
    :param error: Error
    :param app_command: Is command application
    :return:
    """
    owner = await ctx.bot.fetch_user(BOT_OWNER)
    error_message = (
            "**NEW ERROR OCCURRED**\n"
            + f"> **Command** - {ctx.command.name}\n"
            + f"> **User** - {ctx.author.mention}\n"
            + f"> **Channel** - {ctx.channel.id}\n"
            + f"> **Error** - {error.message}\n"
            + f"> **Error type** - {type(error)}\n"
    )

    if not app_command:
        error_message += (
                f"> **Message** - {ctx.message.id}\n"
                + f"> **Args** - {ctx.args}\n"
                + f"> **Kwargs** - {ctx.kwargs}\n"
        )
    await owner.send(error_message)


async def load_all_command_tags(bot: discord.ext.commands.Bot) -> None:
    """
    Loads all command tags into bot
    :param bot:
    :return:
    """
    command_tags = []
    for cog_name, cog in bot.cogs.items():
        for command in cog.get_commands():
            command_tag = command.__original_kwargs__.get("command_tag")
            if command_tag:
                choice = discord.OptionChoice(
                    name=command.name,
                    value=command_tag,
                )
                command_tags.append(choice)

    bot.command_tags = command_tags


def check_arg_in_command_tags(
        arg: str,
        tags: List[discord.commands.options.OptionChoice]
) -> bool:
    """
    Check that command there is in command tags
    :param arg: command name
    :param tags: all command tags
    :return: bool
    """
    return bool(list(filter(lambda tag: arg == tag.value, tags)))


async def init_cogs_settings() -> Dict:
    """
    Init and load cogs settings from db
    :return: dict of settings
    """
    cogs_settings = {}
    copy_from_db = await UsagiCogs.get_all()
    for item in copy_from_db:
        guild_id = item.guild_id
        module_name = item.module_name
        access = item.access
        if guild_id in cogs_settings.keys():
            cogs_settings[guild_id][module_name] = access
        else:
            cogs_settings[guild_id] = {module_name: access}

    return cogs_settings


async def init_moder_roles() -> Dict:
    """
    Init and load moders from db
    :return: Dict of moders
    """
    moder_roles = {}
    copy_from_db = await UsagiModerRoles.get_all()
    for item in copy_from_db:
        guild_id = item.guild_id
        moder_role_id = item.moder_role_id
        if guild_id in moder_roles.keys():
            moder_roles[guild_id].append(moder_role_id)
        else:
            moder_roles[guild_id] = [moder_role_id]

    return moder_roles


def get_embed(
    embed=None,
    title="",
    description="",
    color=0xf08080,
    url_image=None,
    thumbnail=None,
    footer=None,
    author_name=None,
    author_icon_URL=None,
    fields=None,
    timestamp=datetime.utcnow(),
):
    if not embed:
        embed = discord.Embed()

    embed.color = color

    if title:
        embed.title = title

    if description:
        embed.description = description

    if url_image:
        embed.set_image(url=url_image)

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if footer:
        embed.set_footer(text=footer[0], icon_url=footer[1])

    if author_name:
        embed.set_author(name=author_name)

    if author_icon_URL:
        embed.set_author(name=embed.author.name, icon_url=author_icon_URL)

    if title:
        embed.title = title

    if timestamp:
        embed.timestamp = timestamp

    if fields:
        embed.clear_fields()
        for field in fields:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

    return embed
