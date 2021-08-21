import discord
from discord.ext import commands

async def isAdmin(ctx):
    return ctx.author.id == 824521926416269312

class Artifacts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.get_cog('Database')


    @commands.command(name = 'пинг', description = 'Проверка пинга', aliases = ['ping'])
    async def ping(self, ctx):
        await ctx.send(f'Pong! {round(ctx.bot.latency * 1000)} ms')

    @commands.command()
    async def test(self, ctx):
        data = self.db.get_value('users_arts', 'artifacts', 'user_id', ctx.author.id)
        await ctx.send(f'Test command! {data}')


    @commands.Cog.listener()
    async def on_ready(self):
        self.db = self.bot.get_cog('Database')



def setup(bot):
    bot.add_cog(Artifacts(bot))
