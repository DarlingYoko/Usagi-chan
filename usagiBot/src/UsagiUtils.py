from datetime import datetime
from typing import List, Dict

import discord
from discord.ext.commands._types import Error

from usagiBot.env import (
    BOT_OWNER,
    QbittorrentHOST,
    QbittorrentUSERNAME,
    QbittorrentPASSWORD,
)
from usagiBot.db.models import UsagiCogs, UsagiModerRoles, UsagiAutoRoles, UsagiLanguage

import qbittorrentapi
from PIL import Image, ImageDraw, ImageFont
import io


class UsagiEmbed(discord.Embed):
    def __eq__(self, other):
        if isinstance(self, other.__class__):
            if len(self._fields) != len(other._fields):
                return False
            for i in range(len(self._fields)):
                if (
                    self._fields[i].name != other._fields[i].name
                    and self._fields[i].value != other._fields[i].value
                    and self._fields[i].inline != other._fields[i].inline
                ):
                    return False

            result = self.title == other.title and self.description == other.description
            return result
        return False


class Editor:
    def __init__(self, source, mode="RGBA", color=(0, 0, 0, 0)):
        if isinstance(source, (tuple, list)):
            # Create blank canvas (width, height)
            self.image = Image.new(mode, source, color)
        elif isinstance(source, Image.Image):
            self.image = source.convert("RGBA")
        else:
            # Load from file path
            self.image = Image.open(source).convert("RGBA")
        self.draw = ImageDraw.Draw(self.image)

    def paste(self, image, position=(0, 0)):
        # if image is another Editor instance — take its image
        if isinstance(image, Editor):
            image = image.image

        # if image is path
        if isinstance(image, str):
            image = Image.open(image).convert("RGBA")

        if not isinstance(image, Image.Image):
            raise TypeError(f"paste() expected PIL.Image or Editor, got {type(image)}")

        # Ensure RGBA
        image = image.convert("RGBA")

        # Use only alpha channel as mask
        alpha = image.split()[-1]  # take A-channel
        self.image.paste(image, position, alpha)

        return self

    def text(self, position, text, font, color="white"):
        # Convert hex color if needed
        if isinstance(color, str):
            if color.startswith("#"):
                hex_color = color[1:]
                # support short form #fff
                if len(hex_color) == 3:
                    hex_color = "".join([c * 2 for c in hex_color])
                color = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4)) + (255,)
        self.draw.text(position, text, font=font, fill=color)
        return self

    @property
    def image_bytes(self) -> io.BytesIO:
        """Return image bytes

        Returns
        -------
        BytesIO
            Bytes from the image of Editor
        """
        _bytes = io.BytesIO()
        self.image.save(_bytes, "png")

        _bytes.seek(0)
        return _bytes

    def save(self, path):
        self.image.save(path)

    def show(self):
        self.image.show()
        return self

    def get_image(self):
        return self.image

    @staticmethod
    def font(path, size):
        return ImageFont.truetype(path, size)


async def error_notification_to_owner(
    ctx: discord.ext.commands.Context,
    error: Error,
    bot: discord.Bot,
    app_command: bool = False,
):
    """
    Send error log to bot owner
    :param ctx: Discord Context
    :param error: Error
    :bot: Bot object
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
        + f"> **Error type** - {type(error)}\n"
    )

    if not app_command:
        error_message += (
            f"> **Message** - {ctx.message.id}\n"
            + f"> **Args** - {ctx.args}\n"
            + f"> **Kwargs** - {ctx.kwargs}\n"
        )
    await owner.send(error_message)
    bot.logger.error(error)


async def load_all_command_tags(
    bot: discord.ext.commands.Bot,
) -> List[discord.commands.options.OptionChoice]:
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

    return command_tags


def check_arg_in_command_tags(
    arg: str, tags: List[discord.commands.options.OptionChoice]
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
        cogs_settings.setdefault(item.guild_id, {})[item.module_name] = item.access
    return cogs_settings


async def init_moder_roles() -> Dict:
    """
    Init and load moders from db
    :return: Dict of moders
    """
    moder_roles = {}
    copy_from_db = await UsagiModerRoles.get_all()
    for item in copy_from_db:
        moder_roles.setdefault(item.guild_id, []).append(item.moder_role_id)
    return moder_roles


async def init_auto_roles() -> Dict:
    payload = {}
    auto_roles = await UsagiAutoRoles.get_all()
    for role in auto_roles:
        guild_payload = payload.setdefault(role.guild_id, {})
        guild_payload.setdefault(
            role.message_id, {"name": role.name, "channel_id": role.channel_id}
        )
    return payload


async def init_language() -> Dict:
    langs = await UsagiLanguage.get_all()
    return {lang.user_id: lang.lang for lang in langs}


async def init_qbt_client(logger) -> qbittorrentapi.Client:
    conn_info = dict(
        host=QbittorrentHOST,
        username=QbittorrentUSERNAME,
        password=QbittorrentPASSWORD,
    )

    qbt_client = qbittorrentapi.Client(**conn_info)

    try:
        qbt_client.auth_log_in()
        logger.info("Logged in Qbittorrent")
    except qbittorrentapi.LoginFailed as e:
        logger.error(e)

    return qbt_client


def get_embed(
    embed: discord.Embed = None,
    title: str = "",
    description: str = "",
    color: discord.Colour = 0xF08080,
    url_image: str = None,
    thumbnail: str = None,
    footer: List[str] = None,
    author_name: str = None,
    author_icon_URL: str = None,
    fields: List[discord.EmbedField] = None,
    timestamp: datetime.timestamp = None,
):
    if not embed:
        embed = UsagiEmbed()

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

    embed.timestamp = timestamp if timestamp is not None else datetime.utcnow()

    if fields:
        embed.clear_fields()
        for field in fields:
            embed.add_field(name=field.name, value=field.value, inline=field.inline)

    return embed
