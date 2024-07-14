import asyncio
from datetime import datetime
from typing import List
from random import randint

import discord
import pytz
import json

from discord import SlashCommandGroup
from discord.ext import commands, tasks
from pycord18n.extension import _

from usagiBot.db.models import UsagiBirthday, UsagiConfig, UsagiBirthdayTimer
from usagiBot.src.UsagiChecks import check_is_already_set_up, check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError


def get_days(ctx: discord.AutocompleteContext, ):
    return [str(x) for x in range(1, 32)]


async def get_birthdays(
        ctx: discord.AutocompleteContext,
) -> List[discord.OptionChoice]:
    """
    Returns a list of birthday user's names.
    """
    user_names = []
    users = await UsagiBirthday.get_all_by(guild_id=ctx.interaction.guild_id)
    guild = ctx.bot.get_guild(ctx.interaction.guild_id)
    for user_data in users:
        user = await guild.fetch_member(user_data.user_id)
        user_names.append(discord.OptionChoice(name=user.name, value=str(user.id)))

    return user_names


# Add/remove user to db
# Loop to check day
class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_birthday.start()
        self.update_birthday_timer.start()

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @tasks.loop(hours=1)
    async def check_birthday(self):
        timezone = pytz.timezone("Europe/Moscow")
        time = datetime.now(timezone)
        if time.hour == 12:
            with open('./usagiBot/files/birthdays/texts.json') as f:
                birthday_texts = json.load(f)
                birthday_texts_length = len(birthday_texts)
            now = datetime.now()
            cur_data = datetime(day=now.day, month=now.month, year=now.year)
            users_data = await UsagiBirthday.get_all_by(date=cur_data)
            for user_data in users_data:
                guild = await self.bot.fetch_guild(user_data.guild_id)
                guild_config = await UsagiConfig.get(guild_id=user_data.guild_id, command_tag="birthday")
                channel = await guild.fetch_channel(guild_config.generic_id)

                birthday_text = (birthday_texts[str(randint(1, birthday_texts_length))]
                                 .format(user_id=user_data.user_id))
                await channel.send(content=birthday_text)

    @check_birthday.before_loop
    async def before_check_resin_overflow(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Checking birthdays.")

    @tasks.loop(hours=1)
    async def update_birthday_timer(self):
        timers = await UsagiBirthdayTimer.get_all_by(enable=True)
        time_now = datetime.now()

        for timer in timers:
            guild = await self.bot.fetch_guild(timer.guild_id)
            channel = await guild.fetch_channel(timer.channel_id)
            users_data = await UsagiBirthday.get_all_by(guild_id=timer.guild_id)
            user_birthdays = sorted(users_data, key=lambda x: x.date)
            br_data = None
            for user_birthday in user_birthdays:
                if time_now < user_birthday.date:
                    br_data = user_birthday
                    break

            if br_data is None:
                return

            text = f"До др {br_data.name}"
            category_id = channel.category_id
            category = await guild.fetch_channel(category_id)
            if category.name != text:
                await category.edit(name=text, reason="Update birthday timer.")
            delta = br_data.date - time_now
            s = delta.seconds
            hours, remainder = divmod(s, 3600)
            minutes, seconds = divmod(remainder, 60)
            time = ""
            if delta.days:
                time += f"{delta.days} d."
            time += f" {hours} h. {minutes} m."
            await asyncio.sleep(10 * 60)
            await channel.edit(name=time, reason="Update birthday timer.")

    @update_birthday_timer.before_loop
    async def before_check_resin_overflow(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Update birthday timers.")

    birthday = SlashCommandGroup(
        name="birthday",
        name_localizations={"ru": "др"},
        description="Celebrate users birthday!",
        description_localizations={"ru": "Празднуйте день рождения ваших друзей!"},
        command_tag="birthday",
        checks=[
            check_is_already_set_up().predicate
        ],
    )

    @birthday.command(
        name="add",
        name_localizations={"ru": "добавить"},
        description="Add user's birthday.",
        description_localizations={"ru": "Добавить пользователя в список."},
    )
    @discord.commands.option(
        name="day",
        name_localizations={"ru": "день"},
        autocomplete=get_days,
    )
    @discord.commands.option(
        name="month",
        name_localizations={"ru": "месяц"},
        choices=map(lambda x: str(x), range(1, 13)),
    )
    @discord.commands.option(
        name="name",
        name_localizations={"ru": "имя"},
        required=False
    )
    async def birthday_add(self, ctx, user: discord.User, day: int, month: int, name: str = ""):
        if not (0 < day < 32):
            return await ctx.respond(
                "Day out of range, 1 - 31"
            )
        exist_user = await UsagiBirthday.get(guild_id=ctx.guild.id, user_id=user.id)
        if exist_user:
            return await ctx.respond(
                _("This user already added in birthday list"),
                ephemeral=True
            )
        now = datetime.now()
        cur_data = datetime(day=day, month=month, year=now.year)
        if now > cur_data:
            cur_data = datetime(day=day, month=month, year=now.year + 1)
        await UsagiBirthday.create(
            guild_id=ctx.guild.id, user_id=user.id, date=cur_data, name=name
        )
        await ctx.respond(_("Done"), ephemeral=True)

    @birthday.command(
        name="remove",
        name_localizations={"ru": "удалить"},
        description="Remove user's birthday.",
        description_localizations={"ru": "Убрать пользователя из списка."},
    )
    @discord.commands.option(
        name="user",
        name_localizations={"ru": "пользователь"},
        autocomplete=get_birthdays,
    )
    async def birthday_remove(self, ctx, user: str):
        user_id = int(user)
        exist_user = await UsagiBirthday.get(guild_id=ctx.guild.id, user_id=user_id)
        if not exist_user:
            return await ctx.respond(
                _("This user isn't in birthday list, add him firstly"),
                ephemeral=True
            )
        await UsagiBirthday.delete(guild_id=ctx.guild.id, user_id=user_id)
        await ctx.respond(_("Done"), ephemeral=True)

    @birthday.command(
        name="toggle_timer",
        name_localizations={"ru": "переключить_таймер"},
        description="Enable|Disable birthday timer.",
        description_localizations={"ru": "Включить|Выключить таймер дня рождения."},
    )
    async def toggle_timer(self, ctx):
        guild = await UsagiBirthdayTimer.get(guild_id=ctx.guild.id)
        answer = "There is no timer setted"
        if guild:
            await UsagiBirthdayTimer.update(id=guild.id, enable=not guild.enable)
            answer = "Disabled birthday timer" if guild.enable else "Enabled birthday timer"
        await ctx.respond(_(answer), ephemeral=True)

    @birthday.command(
        name="add_timer",
        name_localizations={"ru": "добавить_таймер"},
        description="Add birthday timer.",
        description_localizations={"ru": "Добавить таймер дня рождения."},
    )
    @discord.commands.option(
        name="channel",
        name_localizations={"ru": "канал"},
    )
    async def add_birthday_timer(self, ctx, channel: discord.VoiceChannel):
        guild = await UsagiBirthdayTimer.get(guild_id=ctx.guild.id)
        if guild:
            await UsagiBirthdayTimer.update(id=guild.id, channel=channel.id)
            answer = "Updated birthday timer"
        else:
            await UsagiBirthdayTimer.create(guild_id=ctx.guild.id, channel_id=channel.id, enable=True)
            answer = "Added birthday timer"
        await ctx.respond(_(answer), ephemeral=True)


def setup(bot):
    bot.add_cog(Birthday(bot))
