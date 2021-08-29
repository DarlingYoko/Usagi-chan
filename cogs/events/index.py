import discord
from discord.ext import commands
from bin.functions import get_config


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



def setup(bot):
    bot.add_cog(Events(bot))
