import configparser, os, sys
import discord
from datetime import datetime
from discord.ext import commands



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


class UserConverter(commands.Converter):
    async def convert(self, ctx, argument):
        member = discord.utils.find(lambda m: m.display_name.lower().startswith(argument.lower()), ctx.guild.members)
        if not member:
            raise commands.BadArgument
        return member


def get_embed(embed = None, title = '', description = '', color = 0xf08080, urlImage = None, thumbnail = None, footer = None, authorName = None, authorIconURL = None, fields = None):
    if not embed:
        embed = discord.Embed()

    embed.color = color

    if title:
        embed.title = title

    if description:
        embed.description = description

    if urlImage:
        embed.set_image(url = urlImage)

    if thumbnail:
        embed.set_thumbnail(url = thumbnail)

    if footer:
        embed.set_footer(text = footer[0], icon_url = footer[1])

    if authorName:
        embed.set_author(name = authorName)

    if authorIconURL:
        embed.set_author(name = embed.author.name, icon_url = authorIconURL)

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
