import textwrap

import discord
import requests

from usagiBot.src.UsagiUtils import get_embed
from usagiBot.env import (
    TWITCH_TOKEN,
    REFRESH_TOKEN,
    CLIENT_ID,
    CLIENT_SECRET,
)
from twitchAPI.twitch import Twitch
from twitchAPI.types import AuthScope
from easy_pil import Editor
from PIL import Image, ImageFont, ImageOps
from discord import File
from twitchAPI.helper import first


async def twitch_auth() -> Twitch:
    """
    Create new object to Twitch API
    :return: new Twitch
    """
    twitch = Twitch(CLIENT_ID, CLIENT_SECRET)
    target_scope = [
        AuthScope.CHANNEL_READ_REDEMPTIONS,
        AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
    ]
    await twitch.set_user_authentication(TWITCH_TOKEN, target_scope, REFRESH_TOKEN)
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


def get_notify_src(stream, icon_url) -> tuple[discord.Embed, File]:
    """
    Generate notify embed and image
    :param stream:  stream obj
    :param icon_url:  streamer icon url
    :return: embed
    """
    link = f"<https://www.twitch.tv/{stream.user_login}>"
    text = f"**{stream.user_name}** start stream!"
    image = gen_pic(stream, icon_url)
    embed = get_embed(
        title=text,
        description=f"[twitch.tv/{stream.user_login}]({link})",
        url_image=f"attachment://{stream.user_login}_image.png",
    )
    return embed, image


def gen_pic(stream, icon_url):
    game = stream.game_name
    stream_title = stream.title
    viewer_count = str(stream.viewer_count)

    blank = Image.open("./usagiBot/files/photo/stream.png")
    mask = Image.open("./usagiBot/files/photo/mask2.png").convert("L")
    image = Image.open(requests.get(icon_url, stream=True).raw)

    background = Editor(Image.new("RGBA", (1050, 260), (0, 0, 0, 0)))

    font_bold = ImageFont.truetype(
        font="./usagiBot/files/fonts/Inter-Bold.ttf", size=30
    )
    font_bold_big = ImageFont.truetype(
        font="./usagiBot/files/fonts/Inter-Bold.ttf", size=40
    )
    font_regular = ImageFont.truetype(
        font="./usagiBot/files/fonts/Inter-Regular.ttf", size=38
    )

    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)

    background.paste(blank, (0, 0))
    background.paste(output.resize((160, 160)), (42, 10))

    background.text((245, 15), stream.user_name, font=font_bold_big, color="white")

    lines = textwrap.wrap(stream_title, width=60)
    y_text = 80
    for line in lines:
        width, height = font_bold.getsize(line)
        background.text((245, y_text), line, font=font_bold, color="white")
        y_text += height

    background.text((245, y_text + 20), game, font=font_regular, color="#bf94ff")
    background.text((90, 205), viewer_count, font=font_bold_big, color="#ff8280")

    file = File(fp=background.image_bytes, filename=f"{stream.user_login}_image.png")

    return file
