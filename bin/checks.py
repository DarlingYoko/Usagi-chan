import discord
from discord.ext import commands
from bin.functions import get_config

config = get_config('config')


def is_artifact_channel(ctx):
    return ctx.channel.id == int(config['channel']['artifact'])

def is_mp_channel(ctx):
    return ctx.channel.id == int(config['channel']['mp'])

def is_emoji_channel(ctx):
    return ctx.channel.id == int(config['channel']['emoji'])

def is_transformator_channel(ctx):
    return ctx.channel.id == int(config['channel']['transformator'])

def is_create_role_channel(ctx):
    return ctx.channel.id == int(config['channel']['create_role'])

async def is_user_in_voice(ctx):
    voice_channel = await ctx.bot.fetch_channel(config['channel']['mp_voice'])
    return ctx.author in voice_channel.members
