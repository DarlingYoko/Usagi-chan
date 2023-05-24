from discord.ext import commands

from usagiBot.cogs.AI.ai_utils import OpenAIHandler
from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.src.UsagiUtils import get_embed
from usagiBot.env import OPENAI_API_KEY


class OpenAICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_gpt = OpenAIHandler(OPENAI_API_KEY)

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @commands.slash_command()
    async def ask_gpt(self, ctx, *, question: str):
        await ctx.defer()

        response = await self.chat_gpt.generate_answer(question)
        embed = get_embed(description=response)

        await ctx.followup.send(embed=embed)

    @commands.slash_command()
    async def current_gpt_stats(self, ctx):
        cur_model = await self.chat_gpt.get_ai_model()

        embed = get_embed(title="GPT info")
        embed.add_field(name=f"Model - {cur_model}", value='', inline=False)

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(OpenAICog(bot))
