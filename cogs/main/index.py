import discord
from discord.ext import commands

async def isAdmin(ctx):
    return ctx.author.id == 824521926416269312

class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'админ')
    @commands.check(isAdmin)
    async def admin(self, ctx):
        await ctx.send('Hey!')

    @admin.error
    async def admin_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('Nothing to see here comrade.')


    @commands.command(name = 'чек', description = 'Поиск юзера')
    async def joined(self, ctx, *, member: discord.Member):
        await ctx.send('{0} joined on {0.joined_at}'.format(member))

    @joined.error
    async def joined_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('I could not find that member...')




def setup(bot):
    bot.add_cog(Main(bot))
