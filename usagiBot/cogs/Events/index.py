import re

import discord
import platform
import os
from discord.ext import commands, tasks
from discord.ext.commands import BadColourArgument

from usagiBot.src.UsagiUtils import (
    error_notification_to_owner,
    load_all_command_tags,
    init_cogs_settings,
    init_moder_roles,
    get_embed,
    init_auto_roles,
    init_language,
)
from usagiBot.src.UsagiErrors import *
from usagiBot.db.models import (
    create_tables,
    UsagiConfig,
    UsagiSaveRoles,
    UsagiMemberRoles,
    UsagiAutoRolesData,
    UsagiBackup,
)


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.messages_dump = {}
        self.dump_data.start()

    @tasks.loop(minutes=30)
    async def dump_data(self):
        backup = await UsagiBackup.get_all()

        delete_ids = []
        insert_mappings = []
        last_user = await UsagiBackup.get_last_obj()
        last_id = last_user.id + 1
        for user in backup:
            exist_user = (
                self.bot.messages_dump.get(user.guild_id, {})
                .get(user.channel_id, {})
                .get(user.user_id, None)
            )

            if exist_user is not None:
                insert_mappings.append(
                    UsagiBackup(
                        id=last_id,
                        guild_id=user.guild_id,
                        channel_id=user.channel_id,
                        user_id=user.user_id,
                        messages=exist_user["messages"] + user.messages,
                        images=exist_user["images"] + user.images,
                        gifs=exist_user["gifs"] + user.gifs,
                        emojis=exist_user["emojis"] + user.emojis,
                        stickers=exist_user["stickers"] + user.stickers,
                    )
                )
                delete_ids.append(user.id)

                del self.bot.messages_dump[user.guild_id][user.channel_id][user.user_id]
                last_id += 1

        for guild in self.bot.messages_dump.keys():
            for channel in self.bot.messages_dump[guild].keys():
                for user in self.bot.messages_dump[guild][channel].keys():
                    user_data = self.bot.messages_dump[guild][channel][user]
                    insert_mappings.append(
                        UsagiBackup(
                            id=last_id,
                            guild_id=guild,
                            channel_id=channel,
                            user_id=user,
                            messages=user_data["messages"],
                            images=user_data["images"],
                            gifs=user_data["gifs"],
                            emojis=user_data["emojis"],
                            stickers=user_data["stickers"],
                        )
                    )
                    last_id += 1

        await UsagiBackup.delete_all(delete_ids)
        await UsagiBackup.insert_mappings(insert_mappings)

    # Define main events
    @commands.Cog.listener()
    async def on_ready(self):
        await create_tables()
        self.bot.command_tags = await load_all_command_tags(self.bot)
        self.bot.guild_cogs_settings = await init_cogs_settings()
        self.bot.moder_roles = await init_moder_roles()
        self.bot.auto_roles = await init_auto_roles()
        self.bot.language = await init_language()
        self.bot.logger.info("---------NEW SESSION----------")
        self.bot.logger.info(f"Logged in as {self.bot.user.name}")
        self.bot.logger.info(f"discord.py API version: {discord.__version__}")
        self.bot.logger.info(f"Python version: {platform.python_version()}")
        self.bot.logger.info(
            f"Running on: {platform.system()} {platform.release()} ({os.name})"
        )
        self.bot.logger.info(f"Loaded command tags.")
        self.bot.logger.info(f"Connected to database.")
        self.bot.logger.info(f"Settings loaded.")
        self.bot.logger.info(f"Moder roles loaded.")
        self.bot.logger.info("-------------------")
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game("/help | ver 2.0 | NEW RELEASE!!"))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        user_lang = self.bot.language.get(ctx.author.id, "en")
        if isinstance(error, commands.CommandNotFound):
            await ctx.reply(
                self.bot.i18n.get_text("This command doesn't exist", user_lang),
                delete_after=2 * 60,
            )
        elif isinstance(error, commands.CommandOnCooldown):
            retry_after = float(error.retry_after)
            await ctx.reply(
                self.bot.i18n.get_text("You can use this command in", user_lang).format(
                    retry_after=f"{retry_after:.0f}"
                ),
                delete_after=2 * 60,
            )
        elif isinstance(error, UsagiNotSetUpError):
            await ctx.reply(
                self.bot.i18n.get_text("This command was not configured", user_lang),
                delete_after=2 * 60,
            )
        elif isinstance(error, UsagiModuleDisabledError):
            await ctx.reply(
                self.bot.i18n.get_text("This command is disabled", user_lang),
                delete_after=2 * 60,
            )
        elif isinstance(error, UsagiCallFromNotModerError):
            await ctx.reply(
                self.bot.i18n.get_text("You don't have permissions to use this command", user_lang),
                delete_after=2 * 60,
            )
        elif isinstance(error, UsagiCallFromWrongChannelError):
            await ctx.reply(
                self.bot.i18n.get_text("This is the wrong channel", user_lang).format(channel_id=error.channel_id),
                delete_after=2 * 60,
            )
        elif isinstance(error, BadColourArgument):
            await ctx.reply(
                self.bot.i18n.get_text("Your color is in wrong format", user_lang),
                delete_after=2 * 60,
            )
        elif isinstance(error, discord.errors.CheckFailure):
            await ctx.reply(
                self.bot.i18n.get_text("Some requirements were not met", user_lang),
                delete_after=2 * 60,
            )
        elif isinstance(error, discord.errors.Forbidden):
            await ctx.reply(
                self.bot.i18n.get_text("Don't have permissions to do that", user_lang),
                delete_after=2 * 60,
            )
        else:
            await error_notification_to_owner(ctx, error, self.bot)
        if not isinstance(ctx.message.channel, discord.DMChannel):
            await ctx.message.delete(delay=2 * 60)

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        user_lang = self.bot.language.get(ctx.author.id, "en")
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond(
                self.bot.i18n.get_text("Some requirements were not met.", user_lang),
                ephemeral=True,
            )
        elif isinstance(error, UsagiNotSetUpError):
            await ctx.respond(
                self.bot.i18n.get_text("This command was not configured", user_lang),
                ephemeral=True,
            )
        elif isinstance(error, commands.CommandOnCooldown):
            retry_after = float(error.retry_after)
            await ctx.respond(
                self.bot.i18n.get_text("You can use this command in", user_lang).format(
                    retry_after=f"{retry_after:.0f}"
                ),
                ephemeral=True,
            )
        elif isinstance(error, UsagiModuleDisabledError):
            await ctx.respond(
                self.bot.i18n.get_text("This command is disabled", user_lang),
                ephemeral=True,
            )
        elif isinstance(error, UsagiCallFromNotModerError):
            await ctx.respond(
                self.bot.i18n.get_text(
                    "You don't have permissions to use this command", user_lang
                ),
                ephemeral=True,
            )
        elif isinstance(error, UsagiCallFromWrongChannelError):
            await ctx.respond(
                self.bot.i18n.get_text("This is the wrong channel", user_lang).format(
                    channel_id=error.channel_id
                ),
                ephemeral=True,
            )
        elif isinstance(error, BadColourArgument):
            await ctx.respond(
                self.bot.i18n.get_text("Your color is in wrong format.", user_lang),
                ephemeral=True,
            )
        else:
            await error_notification_to_owner(ctx, error, self.bot, app_command=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        saving = await UsagiSaveRoles.get(guild_id=guild.id)
        if saving is None or saving is False:
            return

        command_tag = "save_roles_on_leave"
        config = await UsagiConfig.get(guild_id=guild.id, command_tag=command_tag)
        if config is None:
            return

        saved_roles = await UsagiMemberRoles.get(guild_id=guild.id, user_id=member.id)
        if saved_roles is None:
            return

        roles_id = saved_roles.roles.split(",")
        if roles_id == [""]:
            return
        roles = map(lambda role_id: guild.get_role(int(role_id)), roles_id)
        await member.add_roles(*roles)

        channel = await guild.fetch_channel(config.generic_id)
        await channel.send(
            embed=get_embed(
                title="Returned all roles to", description=f"{member.mention}"
            )
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        saving = await UsagiSaveRoles.get(guild_id=member.guild.id)
        if saving is None or saving is False:
            return

        command_tag = "save_roles_on_leave"
        config = await UsagiConfig.get(
            guild_id=member.guild.id, command_tag=command_tag
        )
        if config is None:
            return

        user_roles = filter(lambda role: role.is_assignable(), member.roles)
        str_user_roles = ",".join(map(lambda role: str(role.id), user_roles))
        saved_roles = await UsagiMemberRoles.get(
            guild_id=member.guild.id, user_id=member.id
        )
        if saved_roles is None:
            await UsagiMemberRoles.create(
                guild_id=member.guild.id, user_id=member.id, roles=str_user_roles
            )
        else:
            await UsagiMemberRoles.update(id=saved_roles.id, roles=str_user_roles)

        channel = await member.guild.fetch_channel(config.generic_id)
        await channel.send(
            embed=get_embed(
                title="Saved all roles for", description=f"{member.mention}"
            )
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message_id = str(payload.message_id)
        user_id = payload.user_id
        emoji = payload.emoji
        guild_id = payload.guild_id
        channel_id = payload.channel_id

        ai_quesion = self.bot.ai_question.get(message_id, None)

        if user_id == self.bot.user.id:
            return

        if ai_quesion is not None:
            if user_id == ai_quesion and emoji == "❌":
                guild = await self.bot.fetch_guild(guild_id)
                channel = await guild.fetch_channel(channel_id)
                message = await channel.fetch_message(message_id)
                await message.delete(reason="Delete by Emoji")

        auto_roles = self.bot.auto_roles.get(guild_id, {})
        role_data = auto_roles.get(message_id, None)

        if role_data is None:
            return
        role = await UsagiAutoRolesData.get(message_id=message_id, emoji_id=emoji.id)
        if role is None:
            return

        guild = await self.bot.fetch_guild(guild_id)
        role = guild.get_role(role.role_id)
        user = await guild.fetch_member(user_id)
        try:
            await user.add_roles(role)
        except discord.errors.Forbidden:
            channel = await guild.fetch_channel(role_data["channel_id"])
            await channel.send(
                embed=get_embed(
                    title="Cannot give roles as my role has lower position.",
                    color=discord.Color.red(),
                )
            )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        message_id = str(payload.message_id)
        user_id = payload.user_id
        emoji = payload.emoji
        guild_id = payload.guild_id

        if user_id == self.bot.user.id:
            return
        auto_roles = self.bot.auto_roles.get(guild_id, {})
        role_data = auto_roles.get(message_id, None)

        if role_data is None:
            return
        role = await UsagiAutoRolesData.get(message_id=message_id, emoji_id=emoji.id)
        if role is None:
            return

        guild = await self.bot.fetch_guild(guild_id)
        role = guild.get_role(role.role_id)
        user = await guild.fetch_member(user_id)
        try:
            await user.remove_roles(role)
        except discord.errors.Forbidden:
            channel = await guild.fetch_channel(role_data["channel_id"])
            await channel.send(
                embed=get_embed(
                    title="Cannot remove roles as my role has lower position.",
                    color=discord.Color.red(),
                )
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.author.bot:
            return

        if isinstance(message.channel, discord.channel.DMChannel):
            return
        user_id = message.author.id
        channel_id = message.channel.id
        guild_id = message.guild.id

        guild = self.bot.messages_dump.setdefault(guild_id, {})
        channel = guild.setdefault(channel_id, {})
        member = channel.setdefault(
            user_id, {"messages": 0, "images": 0, "gifs": 0, "emojis": 0, "stickers": 0}
        )
        member["messages"] += 1

        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type in ["image/png", "image/jpeg", "image/jpg"]:
                    member["images"] += 1
                if attachment.content_type in ["image/gif"]:
                    member["gifs"] += 1

        if ".gif" in message.content:
            member["gifs"] += 1

        if re.search("<*:*:*>", message.content):
            member["emojis"] += 1

        if message.stickers:
            member["stickers"] += len(message.stickers)


def setup(bot):
    bot.add_cog(Events(bot))
