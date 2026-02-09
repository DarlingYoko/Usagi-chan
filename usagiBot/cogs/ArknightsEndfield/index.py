from datetime import datetime

import discord
import pytz
from discord import SlashCommandGroup

from discord.ext import commands, tasks

from usagiBot.cogs.ArknightsEndfield.schemas import UsagiGryphline
from usagiBot.cogs.Main.schemas import UsagiConfig
from usagiBot.cogs.ArknightsEndfield.arknights_utils import EndfieldClient, generate_endfield_profile
from usagiBot.src.UsagiChecks import check_is_already_set_up, check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError

from pycord18n.extension import _


class EndfieldProfileView(discord.ui.View):
    def __init__(self, bot: discord.Bot, author: discord.Member, endfield_data: list):
        super().__init__(EndfieldProfileSelect(bot, author, endfield_data))

class EndfieldProfileSelect(discord.ui.Select):
    def __init__(self, bot: discord.Bot, author: discord.Member, endfield_data: list):
        self.bot = bot
        self.author = author
        self.endfield_data = endfield_data

        options = []
        for data in self.endfield_data:
            options.append(
                discord.SelectOption(
                    label=data.nickname if data.nickname else "Endfield nickname",
                )
            )

        super().__init__(
            placeholder="Choose account",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.respond(
                content="You are not authorized to use this modal", ephemeral=True )
            return
        data = [d for d in self.endfield_data if d.nickname == self.values[0]][0]
        await interaction.response.edit_message(embed=generate_endfield_profile(data))

class LoginButton(discord.ui.View):
    def __init__(self, bot, user, *items):
        super().__init__(*items)
        self.bot = bot
        self.user = user

    @discord.ui.button(label="Login")
    async def button_callback(self, button, interaction):
        lang = self.bot.language.get(self.user.id, "en")
        title = self.bot.i18n.get_text("Login Gryphline account", lang)
        await interaction.response.send_modal(
            LoginModal(bot=self.bot, user=self.user, title=title)
        )

class LoginModal(discord.ui.Modal):
    def __init__(self, bot, user, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.bot = bot
        self.user = user

        self.add_item(discord.ui.InputText(label="token"))

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        token = self.children[0].value

        lang = self.bot.language.get(user_id, "en")

        client = EndfieldClient(
            account_token=token,
        )

        await client.start()
        try:
            ok = await client.ensure_auth()
            uid = client.uid
        finally:
            await client.close()

        if not ok:
            response = self.bot.i18n.get_text("Failed to auth Gryphline", lang)
            await interaction.response.edit_message(content=response, view=None)
            return

        # Create new Gryphline user
        await UsagiGryphline.create(
            guild_id=guild_id,
            user_id=user_id,
            uid=uid,
            token=token,
            endfield_sanity_sub=True,
            endfield_daily_sub=True
        )

        # Send if success
        response = self.bot.i18n.get_text("Success login Gryphline", lang)
        await interaction.response.edit_message(content=response, view=None)


class Endfield(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.claim_endfield_daily_reward.start()
        self.check_sanity_overflow.start()

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @tasks.loop(minutes=60)
    async def check_sanity_overflow(self):
        users = await UsagiGryphline.get_all_by_or(endfield_sanity_sub=True)

        for user in users:
            config = await UsagiConfig.get(
                guild_id=user.guild_id, command_tag="endfield"
            )
            if not config:
                continue
            try:
                channel = self.bot.get_channel(
                    config.generic_id
                ) or await self.bot.fetch_channel(config.generic_id)
            except discord.errors.Forbidden:
                self.bot.logger.error(f"Cant get access to {config.generic_id}")
                continue

            client = EndfieldClient(
                account_token=user.token
            )

            await client.start()

            try:
                if not await client.sign_in():
                    continue

                profile = await client.get_profile()

                if not profile.success:
                    continue

            finally:
                await client.close()

            if profile.data and profile.data.sanity.current < 340:
                if user.endfield_sanity_sub_notified:
                    await UsagiGryphline.update(
                        id=user.id, endfield_sanity_sub_notified=False
                    )

            lang = self.bot.language.get(user.user_id, "en")
            if (
                    profile.data
                    and user.endfield_sanity_sub
                    and not user.endfield_sanity_sub_notified
                    and profile.data.sanity.current >= 340
            ):
                notify_text = self.bot.i18n.get_text("sanity cap", lang).format(
                    user_id=user.user_id,
                    nickname=profile.data.nickname,
                    current_sanity=profile.data.sanity.current,
                )
                await channel.send(content=notify_text)
                await UsagiGryphline.update(id=user.id, endfield_sanity_sub_notified=True)

    @check_sanity_overflow.before_loop
    async def before_check_sanity_overflow(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Checking sanity.")

    @tasks.loop(hours=1)
    async def claim_endfield_daily_reward(self):
        moscow_tz = pytz.timezone("Europe/Moscow")
        time_in_moscow = datetime.now(moscow_tz)
        if time_in_moscow.hour != 19:
            return

        users = await UsagiGryphline.get_all_by_or(endfield_daily_sub=True)
        channels = []
        errors = []

        for user in users:
            config = await UsagiConfig.get(
                guild_id=user.guild_id, command_tag="endfield"
            )
            if not config:
                continue
            channel = await self.bot.fetch_channel(config.generic_id)

            client = EndfieldClient(
                account_token=user.token
            )

            await client.start()

            try:
                if not await client.sign_in():
                    errors.append((user.user_id, channel, _("Authorisation failed")))

                result = await client.get_attendance()
                if result.success and channel not in channels:
                    channels.append(channel)

                if not result.success:
                    errors.append((user.user_id, channel, _("Profile error").format(message=result.message)))

            finally:
                await client.close()

        for channel in channels:
            await channel.send(
                content=(
                    "Claimed daily rewards.\n"
                    "To follow use `/endfield settings` and click for daily rewards."
                )
            )

        for error in errors:
            await error[1].send(
                content=f"<@{error[0]}>, {error[2]}"
            )

    @claim_endfield_daily_reward.before_loop
    async def before_claim_endfield_daily_reward(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Checking Endfield daily reward.")

    endfield = SlashCommandGroup(
        name="endfield",
        name_localizations={"ru": "ендфилд"},
        description="Manage your Arknights Endfield account!",
        description_localizations={
            "ru": "Управление Аркнайтс Ендфилд аккаунтом!"
        },
        command_tag="endfield",
        checks=[check_is_already_set_up().predicate],
    )

    @endfield.command(
        name="profile",
        name_localizations={"ru": "профиль"},
        description="Check your profile!",
        description_localizations={
            "ru": "Проверка вашего профиля!"
        },
    )
    async def endfield_profile(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        users_data = await UsagiGryphline.get_all_by(guild_id=ctx.guild.id, user_id=ctx.author.id)
        if not users_data:
            ctx.respond(_("User not found"), ephemeral=True)
            return

        endfield_data = []
        for user_data in users_data:
            client = EndfieldClient(
                account_token=user_data.token
            )

            await client.start()

            try:
                if not await client.sign_in():
                    await ctx.respond(_("Authorisation failed"))
                    return

                profile = await client.get_profile()

                if not profile.success:
                    await ctx.respond(_("Profile error").format(message=profile.message))
                    return

                endfield_data.append(profile.data)
            finally:
                await client.close()

        endfield_view = None
        if len(endfield_data) > 1:
            endfield_view = EndfieldProfileView(self.bot, ctx.author, endfield_data)

        await ctx.respond(
            embed=generate_endfield_profile(endfield_data[0]),
            view=endfield_view
        )

    @endfield.command(
        name="login",
        name_localizations={"ru": "логин"},
        description="Login for manage account",
        description_localizations={
            "ru": "Логин для управления аккаунтом"
        },
    )
    async def endfield_login(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            _("Please login Gryphline"),
            view=LoginButton(self.bot, ctx.user),
            ephemeral=True,
        )

    @endfield.command(
        name="settings",
        name_localizations={"ru": "настройки"},
        description="Settings for daily reward and notifications!",
        description_localizations={
            "ru": "Настройка ежедневных отметок и уведомлений!"
        },
    )
    @discord.commands.option(
        name="option",
        name_localizations={"ru": "опция"},
        description="Option to change",
        description_localizations={"ru": "Опция для настройки"},
        choices=["Daily reward", "Notification"],
        required=True,
    )
    @discord.commands.option(
        name="uid",
        name_localizations={"ru": "уид"},
        description="UID to change",
        description_localizations={"ru": "Уид для настройки"},
        required=True,
    )
    async def endfield_settings(self, ctx: discord.ApplicationContext, option: str, uid: int):
        check_account = await UsagiGryphline.get(guild_id=ctx.guild.id, user_id=ctx.author.id, uid=uid)
        if not check_account:
            ctx.respond(_("User not found"), ephemeral=True)
            return

        result = None
        match option:
            case "Daily reward":
                check_account.endfield_daily_sub = not check_account.endfield_daily_sub
                result = _("ON") if check_account.endfield_daily_sub else _("OFF")
            case "Notification":
                check_account.endfield_sanity_sub = not check_account.endfield_sanity_sub
                result = _("ON") if check_account.endfield_sanity_sub else _("OFF")
            case _:
                pass

        await UsagiGryphline.update(
            id=check_account.id,
            endfield_daily_sub=check_account.endfield_daily_sub,
            endfield_sanity_sub=check_account.endfield_sanity_sub
        )
        await ctx.respond(
            _("Updated Endfield account").format(uid=uid, option=option, result=result),
            ephemeral=True
        )



    @endfield.command(
        name="delete",
        name_localizations={"ru": "удалить"},
        description="Delete account by uid",
        description_localizations={
            "ru": "Удалить аккаунт по уиду"
        },
    )
    @discord.commands.option(
        name="uid",
        name_localizations={"ru": "уид"},
        description="UID to delete",
        description_localizations={"ru": "Уид для удаления"},
        required=True,
    )
    async def endfield_delete(self, ctx: discord.ApplicationContext, uid: int):
        check_account = await UsagiGryphline.get(guild_id=ctx.guild.id, user_id=ctx.author.id, uid=uid)
        if not check_account:
            ctx.respond(_("User not found"), ephemeral=True)
            return

        await UsagiGryphline.delete(guild_id=ctx.guild.id, user_id=ctx.author.id, uid=uid)
        await ctx.respond(_("Deleted Gryphline account").format(uid=uid), ephemeral=True)


def setup(bot):
    bot.add_cog(Endfield(bot))
