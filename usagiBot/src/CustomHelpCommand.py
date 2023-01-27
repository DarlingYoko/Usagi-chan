import discord

from discord.ext import commands


class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        ctx = self.context
        await ctx.reply("Please use **/help** command to see help instructions.", delete_after=60)
        if not isinstance(ctx.message.channel, discord.DMChannel):
            await ctx.message.delete(delay=60)
