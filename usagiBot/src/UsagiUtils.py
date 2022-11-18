from typing import List

import discord
from discord.ext.commands._types import Error

from usagiBot.env import BOT_OWNER
from usagiBot.db.models import UsagiConfig


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
            + f"> **Error** - {error}\n"
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


async def check_command_tag_in_db(ctx: discord.ext.commands.Context, command_tag: str) -> bool:
    """
    Check for the presence of the command tag in the database
    :param ctx: discord Context
    :param command_tag: Command name tag
    :return: Bool
    """
    config = await UsagiConfig.get(guild_id=ctx.guild.id, command_tag=command_tag)
    if config:
        return True

    return False


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
    for tag in tags:
        if arg == tag.value:
            return True
    return False
