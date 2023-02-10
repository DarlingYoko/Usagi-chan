import discord
import platform
import os
from discord.ext import commands
from discord.ext.commands import BadColourArgument

from usagiBot.src.UsagiUtils import (
    error_notification_to_owner,
    load_all_command_tags,
    init_cogs_settings,
    init_moder_roles
)
from usagiBot.src.UsagiErrors import *
from usagiBot.db.models import create_tables


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Define main events
    @commands.Cog.listener()
    async def on_ready(self):
        await create_tables()
        await load_all_command_tags(self.bot)
        self.bot.guild_cogs_settings = await init_cogs_settings()
        self.bot.moder_roles = await init_moder_roles()
        self.bot.logger.info("---------NEW SESSION----------")
        self.bot.logger.info(f"Logged in as {self.bot.user.name}")
        self.bot.logger.info(f"discord.py API version: {discord.__version__}")
        self.bot.logger.info(f"Python version: {platform.python_version()}")
        self.bot.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        self.bot.logger.info(f"Loaded command tags: {self.bot.command_tags}")
        self.bot.logger.info(f"Connected to database.")
        self.bot.logger.info(f"Settings loaded.")
        self.bot.logger.info(f"Moder roles loaded.")
        self.bot.logger.info("-------------------")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.reply("This command doesn't exist.", delete_after=2 * 60)
        elif isinstance(error, commands.CommandOnCooldown):
            retry_after = float(error.retry_after)
            await ctx.reply(
                f"You can use this command in {retry_after:.0f}s",
                delete_after=2 * 60,
            )
        elif isinstance(error, UsagiNotSetUpError):
            await ctx.reply(
                "This command was not configured. Contact the server administration.",
                delete_after=2 * 60,
            )
        elif isinstance(error, UsagiModuleDisabledError):
            await ctx.reply(
                "This command is disabled. Contact the server administration.",
                delete_after=2 * 60,
            )
        elif isinstance(error, UsagiCallFromNotModerError):
            await ctx.reply(
                "You don't have permissions to use this command.",
                delete_after=2 * 60,
            )
        elif isinstance(error, UsagiCallFromWrongChannelError):
            await ctx.reply(
                f"This is the wrong channel to send this command\nTry this one: <#{error.channel_id}>",
                delete_after=2 * 60,
            )
        elif isinstance(error, BadColourArgument):
            await ctx.reply(
                "Your color is in wrong format!",
                delete_after=2 * 60,
            )
        elif isinstance(error, discord.errors.CheckFailure):
            await ctx.reply("Some requirements were not met.", delete_after=2 * 60)
        else:
            await error_notification_to_owner(ctx, error)
        if not isinstance(ctx.message.channel, discord.DMChannel):
            await ctx.message.delete(delay=2*60)

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
                f"You can use this command in {retry_after:.0f}s",
                ephemeral=True,
            )
        elif isinstance(error, UsagiModuleDisabledError):
            await ctx.respond(
                "This command is disabled. Contact the server administration.",
                ephemeral=True,
            )
        elif isinstance(error, UsagiCallFromNotModerError):
            await ctx.respond(
                "You don't have permissions to use this command.",
                ephemeral=True,
            )
        elif isinstance(error, UsagiCallFromWrongChannelError):
            await ctx.respond(
                f"This is the wrong channel to send this command\nTry this one: <#{error.channel_id}>",
                ephemeral=True,
            )
        elif isinstance(error, BadColourArgument):
            await ctx.respond(
                "Your color is in wrong format!",
                ephemeral=True,
            )
        else:
            await error_notification_to_owner(ctx, error, app_command=True)


def setup(bot):
    bot.add_cog(Events(bot))
