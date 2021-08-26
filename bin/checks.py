import discord
from discord.ext import commands
from bin.functions import get_config


config = get_config()

def is_channel(channel_id):
    async def predicate(ctx):
        return ctx.channel.id == channel_id
    return commands.check(predicate)


async def is_user_in_voice(ctx):
    voice_channel = await ctx.bot.fetch_channel(config['channel'].getint('mp_voice'))
    return ctx.author in voice_channel.members
