import discord
from discord.ext import commands

def is_channel(channel_id):
    async def predicate(ctx):
        return ctx.channel.id == channel_id
    return commands.check(predicate)


async def is_user_in_voice(ctx):
    voice_channel = await ctx.bot.fetch_channel(858053937008214022)
    return ctx.author in voice_channel.members
