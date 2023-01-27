import discord
from discord.ext import commands
from datetime import timedelta

from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError


class Tech(commands.Cog):
    def __init__(self, bot):
        pass

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @commands.message_command(name="Pin message")
    async def get_message_id(self, ctx, message: discord.Message) -> None:
        await message.pin(reason=f"Pinned by {ctx.author}")
        await ctx.respond(f"Message was pinned", ephemeral=True)

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
    bot.add_cog(Tech(bot))
