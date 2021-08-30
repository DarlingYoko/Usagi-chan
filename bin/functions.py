import configparser, os, sys
import discord
from datetime import datetime
from discord.ext import commands
from discord_components import Button, Select, ButtonStyle, SelectOption


def get_config():
    config = configparser.ConfigParser()

    for filename in os.listdir('./test_config'):
        if filename.endswith('.ini'):
            config.read(f'./test_config/{filename}', encoding = 'UTF8')
    return config


def print_error():
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print('New error:\ntype - {0}, line - {1}, error - {2}, file - {3}\n'.format(exc_type, exc_tb.tb_lineno, exc_obj, fname))


def get_embed(embed = None, title = '', description = '', color = 0xf08080, url_image = None, thumbnail = None, footer = None, author_name = None, author_icon_URL = None, fields = None):
    if not embed:
        embed = discord.Embed()

    embed.color = color

    if title:
        embed.title = title

    if description:
        embed.description = description

    if url_image:
        embed.set_image(url = url_image)

    if thumbnail:
        embed.set_thumbnail(url = thumbnail)

    if footer:
        embed.set_footer(text = footer[0], icon_url = footer[1])

    if author_name:
        embed.set_author(name = author_name)

    if author_icon_URL:
        embed.set_author(name = embed.author.name, icon_url = author_icon_URL)

    if title:
        embed.title = title

    if fields:
        embed.clear_fields()
        for field in fields:
            embed.add_field(name = field['name'], value = field['value'], inline=field['inline'])


    return embed



def check_str_in_list(str, list):
    for line in list:
        if line in str:
            return 1
    return 0


def get_query_btns(ctx, page):
    emojiStart = ctx.bot.get_emoji(873921151896805487)
    emojiPrevious = ctx.bot.get_emoji(873921151372513312)
    emojiNext = ctx.bot.get_emoji(873921151716438016)
    emojiEnd = ctx.bot.get_emoji(873921151280234537)
    btnStart = Button(style=ButtonStyle.gray, emoji = emojiStart, id = 'start')
    btnPrevious = Button(style=ButtonStyle.gray, emoji = emojiPrevious, id = 'previuos')
    btnNext = Button(style=ButtonStyle.gray, emoji = emojiNext, id = 'next')
    btnEnd = Button(style=ButtonStyle.gray, emoji = emojiEnd, id = 'end')
    page = Button(style=ButtonStyle.gray, label = page, id = 'page', disabled = True)
    components=[[btnStart, btnPrevious, page, btnNext, btnEnd,]]
    return components
