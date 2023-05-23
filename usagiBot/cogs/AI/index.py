from discord.ext import commands
from discord import Embed
from usagiBot.cogs.AI.ai_utils import OpenAIHandler
from usagiBot.env import OPENAI_API_KEY
from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError


class OpenAICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_gpt = OpenAIHandler(OPENAI_API_KEY)
        self.ai_channel = "channel_id"

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @commands.slash_command()
    async def ask_gpt(self, ctx, *, question: str):
        await ctx.defer()

        response = await self.chat_gpt.generate_answer(question)
        embed = Embed(title="", color=0xd71919, description=response)

        await ctx.followup.send(embed=embed)

    @commands.slash_command()
    async def current_gpt_stats(self, ctx):
        cur_model = await self.chat_gpt.get_ai_model()

        embed = Embed(title="GPT info", color=0xd71919)
        embed.add_field(name=f"Model - {cur_model}", value='', inline=False)

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(OpenAICog(bot))
