import discord
from discord.ext import commands
from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabled
from datetime import timedelta


class Main(commands.Cog):
    def __init__(self, bot):
        pass

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabled()

    @commands.slash_command(name="sleep", description="Go to sleep for N hours")
    @discord.commands.option(
        name="hours",
        description="Insert sleep hours!",
        autocomplete=lambda x: range(2, 25, 2),
        required=True,
    )
    async def go_sleep(
            self,
            ctx,
            hours: int,
    ) -> None:
        duration = timedelta(hours=hours)
        await ctx.author.timeout_for(duration=duration, reason="Timeout for sleep")
        await ctx.respond(f"Good night, see you in {hours} hours.", ephemeral=True)


def setup(bot):
    bot.add_cog(Main(bot))