import asyncio
import logging
import textwrap

import aiohttp
import discord

from usagiBot.src.UsagiUtils import get_embed, Editor
from usagiBot.env import (
    TWITCH_TOKEN,
    REFRESH_TOKEN,
    CLIENT_ID,
    CLIENT_SECRET,
)

from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.type import (
    AuthScope,
    InvalidRefreshTokenException,
    InvalidTokenException,
)

from PIL import Image, ImageFont, ImageOps
from discord import File
from io import BytesIO

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)

# Parsed once — gen_pic runs for every stream notification
FONT_BOLD = ImageFont.truetype(font="./usagiBot/files/fonts/Inter-Bold.ttf", size=30)
FONT_BOLD_BIG = ImageFont.truetype(font="./usagiBot/files/fonts/Inter-Bold.ttf", size=40)
FONT_REGULAR = ImageFont.truetype(font="./usagiBot/files/fonts/Inter-Regular.ttf", size=38)


async def twitch_auth() -> Twitch:
    """
    Create new object to Twitch API.

    Stream lookups only need app auth, so a revoked/expired user token pair
    degrades to app auth instead of leaving the notifier without a client.
    :return: new Twitch
    """
    twitch = Twitch(CLIENT_ID, CLIENT_SECRET)
    target_scope = [
        AuthScope.CHANNEL_READ_REDEMPTIONS,
        AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
    ]
    try:
        await twitch.set_user_authentication(TWITCH_TOKEN, target_scope, REFRESH_TOKEN)
    except (InvalidRefreshTokenException, InvalidTokenException, TypeError):
        logger.warning(
            "Twitch user token is invalid or revoked; regenerate TWITCH_TOKEN and "
            "REFRESH_TOKEN. Falling back to app auth (stream notifications still work)."
        )
        twitch = await Twitch(CLIENT_ID, CLIENT_SECRET)
    return twitch


async def get_streamer_icon(twitch, streamer) -> str:
    """
    Return streamer icon URL by streamer name
    :return: icon URL
    """
    user = await first(twitch.get_users(logins=[streamer]))
    if not user:
        return "https://static-cdn.jtvnw.net/user-default-pictures-uv/75305d54-c7cc-40d1-bb9c-91fbe85943c7-profile_image-300x300.png"
    return user.profile_image_url


async def get_notify_src(stream, icon_url) -> tuple[discord.Embed, File]:
    """
    Generate notify embed and image
    :param stream:  stream obj
    :param icon_url:  streamer icon url
    :return: embed
    """
    link = f"<https://www.twitch.tv/{stream.user_login}>"
    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        async with session.get(icon_url) as response:
            response.raise_for_status()
            icon_bytes = await response.read()
    image = await asyncio.to_thread(gen_pic, stream, icon_bytes)
    embed = get_embed(
        description=f"### [{stream.user_name}]({link}) start stream!",
        url_image=f"attachment://{stream.user_login}_image.png",
    )
    return embed, image


def gen_pic(stream, icon_bytes: bytes) -> File:
    game = stream.game_name
    stream_title = stream.title
    viewer_count = str(stream.viewer_count)

    blank = Image.open("./usagiBot/files/photo/stream.png")
    mask = Image.open("./usagiBot/files/photo/mask2.png").convert("L")
    image = Image.open(BytesIO(icon_bytes))

    background = Editor(Image.new("RGBA", (1050, 1050), (0, 0, 0, 0)))

    font_bold = FONT_BOLD
    font_bold_big = FONT_BOLD_BIG
    font_regular = FONT_REGULAR

    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)

    background.paste(blank, (0, 0))
    background.paste(output.resize((160, 160)), (42, 10))

    background.text((245, 15), stream.user_name, font=font_bold_big, color="white")

    lines = textwrap.wrap(stream_title, width=40)
    y_text = 80
    for line in lines:
        bbox = font_bold.getbbox(line)
        width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        background.text((245, y_text), line, font=font_bold, color="white")
        y_text += height

    background.text((245, y_text + 20), game, font=font_regular, color="#bf94ff")
    background.text((90, 205), viewer_count, font=font_bold_big, color="#ff8280")

    new_background = Image.open(background.image_bytes)
    crop = 300 if y_text + 80 > 260 else 260
    new_background = new_background.crop((0, 0, 1050, crop))

    _bytes = BytesIO()
    new_background.save(_bytes, "png")
    _bytes.seek(0)

    file = File(fp=_bytes, filename=f"{stream.user_login}_image.png")

    return file
