import discord
import platform
import os
from discord.ext import commands
from usagiBot.src.UsagiUtils import error_notification_to_owner, load_all_command_tags
from usagiBot.src.UsagiErrors import UsagiNotSetUpError


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Define main events
    @commands.Cog.listener()
    async def on_ready(self):
        await load_all_command_tags(self.bot)
        self.bot.logger.info("---------NEW SESSION----------")
        self.bot.logger.info(f"Logged in as {self.bot.user.name}")
        self.bot.logger.info(f"discord.py API version: {discord.__version__}")
        self.bot.logger.info(f"Python version: {platform.python_version()}")
        self.bot.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        self.bot.logger.info(f"Loaded command tags: {self.bot.command_tags}")
        self.bot.logger.info(f"Connected to database ")
        self.bot.logger.info("-------------------")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.reply("Такой команды не существует.", delete_after=2 * 60)
        elif isinstance(error, commands.CommandOnCooldown):
            retry_after = float(error.retry_after)
            await ctx.reply(
                f"Эту команду ты сможешь использовать через {retry_after:.0f}s",
                delete_after=2 * 60,
            )
        elif isinstance(error, UsagiNotSetUpError):
            await ctx.reply(
                "This command was not configured. Contact the server administration.",
                delete_after=2 * 60,
            )
        elif isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Some requirements were not met.", delete_after=2 * 60)
        else:
            await error_notification_to_owner(ctx, error)

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Some requirements were not met.", ephemeral=True)
        elif isinstance(error, UsagiNotSetUpError):
            await ctx.respond(
                "This command was not configured. Contact the server administration.",
                ephemeral=True,
            )
        elif isinstance(error, commands.CommandOnCooldown):
            retry_after = float(error.retry_after)
            await ctx.respond(
                f"Эту команду ты сможешь использовать через {retry_after:.0f}s",
                ephemeral=True,
            )
        else:
            await error_notification_to_owner(ctx, error, app_command=True)


def setup(bot):
    bot.add_cog(Events(bot))