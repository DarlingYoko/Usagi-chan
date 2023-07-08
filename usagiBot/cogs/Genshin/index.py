import pytz

from usagiBot.db.models import UsagiConfig
from usagiBot.src.UsagiChecks import check_cog_whitelist, is_owner
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.src.UsagiUtils import get_embed
from usagiBot.cogs.Genshin.genshin_utils import *

from discord.ext import commands, tasks
from discord import SlashCommandGroup
from pycord18n.extension import _


class GenshinModal(discord.ui.Modal):
    def __init__(self, bot, lang, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.lang = lang
        label = self.bot.i18n.get_text("Cookie", lang)
        self.add_item(discord.ui.InputText(label=label))

    async def callback(self, interaction: discord.Interaction):
        genshin_api = GenshinAPI()
        cookies = self.children[0].value.replace("'", "")
        auth_result = await genshin_api.new_user_auth(
            guild_id=interaction.guild_id,
            user_id=interaction.user.id,
            cookies=cookies,
        )
        text = self.bot.i18n.get_text("Wrong cookies", self.lang)
        if auth_result:
            text = self.bot.i18n.get_text("Successfully auth", self.lang)
        await interaction.response.send_message(content=text, ephemeral=True)


class SelectSubsView(discord.ui.View):
    def __init__(self, bot, user, *items):
        super().__init__(*items)
        self.bot = bot
        self.user = user

    @discord.ui.select(
        placeholder="Select subscription",
        max_values=5,
        options=[
            discord.SelectOption(
                label="Genshin resin notify",
                value="genshin_resin",
            ),
            discord.SelectOption(
                label="Genshin daily claim",
                value="genshin_daily",
            ),
            discord.SelectOption(
                label="StarRail resin notify",
                value="starrail_resin",
            ),
            discord.SelectOption(
                label="StarRail daily claim",
                value="starrail_daily",
            ),
            discord.SelectOption(
                label="Daily reward notify",
                description="Notify you about to claim daily reward.",
                value="daily_notify",
            ),
        ]
    )
    async def select_callback(self, select, interaction):
        for sub in select.values:
            match sub:
                case "genshin_resin":
                    self.user.genshin_resin_sub = not self.user.genshin_resin_sub
                case "genshin_daily":
                    self.user.genshin_daily_sub = not self.user.genshin_daily_sub
                case "starrail_resin":
                    self.user.starrail_resin_sub = not self.user.starrail_resin_sub
                case "starrail_daily":
                    self.user.starrail_daily_sub = not self.user.starrail_daily_sub
                case "daily_notify":
                    self.user.daily_notify_sub = not self.user.daily_notify_sub
                case _:
                    pass

        fields = generate_all_subs_fields(self.user)

        embed = get_embed(
            title=_("Subscriptions"),
            author_name=interaction.user.display_name,
            author_icon_URL=interaction.user.avatar,
            fields=fields,
        )
        await UsagiGenshin.update(
            id=self.user.id,
            genshin_resin_sub=self.user.genshin_resin_sub,
            genshin_daily_sub=self.user.genshin_daily_sub,
            daily_notify_sub=self.user.daily_notify_sub,
            starrail_daily_sub=self.user.starrail_daily_sub,
            starrail_resin_sub=self.user.starrail_resin_sub,
        )
        await interaction.response.edit_message(embed=embed)


class GenshinAuth(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(
        label="Enter cookie",
        style=discord.ButtonStyle.primary,
    )
    async def guess_button(self, button, interaction):
        lang = self.bot.language.get(interaction.user.id, "en")
        title = self.bot.i18n.get_text("Genshin auth", lang)
        await interaction.response.send_modal(GenshinModal(title=title, bot=self.bot, lang=lang))


class Genshin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_resin_overflow.start()
        self.claim_daily_reward.start()
        self.daily_reward_claim_notify.start()

    @tasks.loop(minutes=30)
    async def check_resin_overflow(self):
        users = await UsagiGenshin.get_all_by_or(genshin_resin_sub=True, starrail_resin_sub=True)

        for user in users:
            config = await UsagiConfig.get(
                guild_id=user.guild_id, command_tag="genshin"
            )
            if not config:
                continue
            try:
                channel = await self.bot.fetch_channel(config.generic_id)
            except discord.errors.Forbidden:
                print(f"Cant get access to {config.generic_id}")
                continue

            genshin_api = GenshinAPI()
            data = await genshin_api.get_user_data(
                guild_id=user.guild_id, user_id=user.user_id
            )
            genshin_data = data.get("genshin", None)
            starrail_data = data.get("starrail", None)

            if genshin_data is None and starrail_data is None:
                continue
            if genshin_data and genshin_data.current_resin < 150:
                if user.genshin_resin_sub_notified:
                    await UsagiGenshin.update(id=user.id, genshin_resin_sub_notified=False)

            if starrail_data and starrail_data.current_stamina < 170:
                if user.starrail_resin_sub_notified:
                    await UsagiGenshin.update(id=user.id, starrail_resin_sub_notified=False)

            lang = self.bot.language.get(user.user_id, "en")
            if user.genshin_resin_sub and not user.genshin_resin_sub_notified and genshin_data.current_resin >= 150:
                notify_text = self.bot.i18n.get_text("resin cap", lang).format(
                    user_id=user.user_id,
                    current_resin=genshin_data.current_resin
                )
                await channel.send(content=notify_text)
                await UsagiGenshin.update(id=user.id, genshin_resin_sub_notified=True)
            if user.starrail_resin_sub and not user.starrail_resin_sub_notified and starrail_data.current_stamina >= 170:
                notify_text = self.bot.i18n.get_text("stamina cap", lang).format(
                    user_id=user.user_id,
                    current_stamina=starrail_data.current_stamina
                )
                await channel.send(content=notify_text)
                await UsagiGenshin.update(id=user.id, starrail_resin_sub_notified=True)

    @check_resin_overflow.before_loop
    async def before_check_resin_overflow(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Checking resin.")

    @tasks.loop(hours=1)
    async def daily_reward_claim_notify(self):
        moscow_tz = pytz.timezone("Europe/Moscow")
        time_in_moscow = datetime.now(moscow_tz)
        if time_in_moscow.hour != 19:
            return

        users = await UsagiGenshin.get_all_by(daily_notify_sub=True)
        notify_channels = {}

        for user in users:
            config = await UsagiConfig.get(
                guild_id=user.guild_id, command_tag="genshin"
            )
            if not config:
                continue
            channel = await self.bot.fetch_channel(config.generic_id)
            notify_channel = notify_channels.setdefault(channel.id, {"channel": channel, "users": []})
            notify_channel["users"].append(user.user_id)

        for data in notify_channels.values():
            users = data["users"]
            channel = data["channel"]

            users_text = ", ".join(map(lambda user_id: f"<@{user_id}>", users))
            links = "\nGenshin - https://bit.ly/genshin_daily\nHonkai - https://bit.ly/honkai_daily"
            text = "Don't forget to claim your daily reward! <:UsagiLove:1084226975113158666> \n" \
                   + users_text \
                   + links
            await channel.send(text)

    @daily_reward_claim_notify.before_loop
    async def before_daily_reward_claim_notify(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("daily_reward_claim_notify")

    @tasks.loop(minutes=30)
    async def claim_daily_reward(self):
        moscow_tz = pytz.timezone("Europe/Moscow")
        time_in_moscow = datetime.now(moscow_tz)
        if time_in_moscow.hour != 19:
            return
        users = await UsagiGenshin.get_all_by_or(genshin_daily_sub=True, starrail_daily_sub=True)
        channels = []
        out_date_cookies = []

        for user in users:
            config = await UsagiConfig.get(
                guild_id=user.guild_id, command_tag="genshin"
            )
            if not config:
                continue
            channel = await self.bot.fetch_channel(config.generic_id)

            genshin_api = GenshinAPI()
            respone = None
            if user.genshin_daily_sub:
                respone = await genshin_api.claim_daily_reward(
                    guild_id=user.guild_id,
                    user_id=user.user_id,
                    game=genshin.Game.GENSHIN
                )
            if user.starrail_daily_sub:
                respone = await genshin_api.claim_daily_reward(
                    guild_id=user.guild_id,
                    user_id=user.user_id,
                    game=genshin.Game.STARRAIL
                )
            if respone == "InvalidCookies":
                out_date_cookies.append((user.user_id, channel))
                respone = None
            if respone and channel not in channels:
                channels.append(channel)
        for channel in channels:
            await channel.send(
                content=("Claimed daily rewards.\n"
                         "To follow use `/hoyolab sub genshin_reward_claim/honkai_reward_claim `"
                         "Or you can do it by yourself\n"
                         "Genshin - https://bit.ly/genshin_daily\n"
                         "Honkai - https://bit.ly/honkai_daily")
            )

        for out_cookie in out_date_cookies:
            await out_cookie[1].send(
                content=f"<@{out_cookie[0]}>, " + _("Your cookie out of date")
            )

    @claim_daily_reward.before_loop
    async def before_claim_daily_reward(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info(f"Checking daily reward.")

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @commands.command(name="primogems", aliases=["примогемы"])
    async def primogems_link(self, ctx):
        link_1 = ("<https://docs.google.com/spreadsheets/d/1DPJOtHTLB_y-"
                  "MTcUheSBrMPFvV_EtBlcYA6Xy1F0R_c/edit?pli=1#gid=284498967>")
        link_2 = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vToBPh4yTn4VioU"
                  "uqSvnPiwLoG0rJodFe9_gz6qOKUy3z8dCWtXel5Aqa07qSTZG8qhu7Fwgx7AfxzU/pubhtml#>")
        answer = _("links to primogems")
        text = "\n".join([answer, link_1, link_2])
        return await ctx.reply(text)

    @commands.command(name="forum", aliases=["форум"])
    async def forum_link(self, ctx):
        return await ctx.reply(_("forum link"))

    @commands.command(name="map", aliases=["карта"])
    async def map_link(self, ctx):
        return await ctx.reply(_("links to maps"))

    @commands.command(name="ambr", aliases=["эмбер"])
    async def ambr_link(self, ctx):
        return await ctx.reply("<https://ambr.top/ru/archive/avatar>")

    @commands.command(name="hh", aliases=["хх"])
    async def hh_link(self, ctx):
        return await ctx.reply(_("hh links"))

    @commands.command(name="paimon", aliases=["паймон", "pompom", "понпон", "помпом"])
    async def paimon_link(self, ctx):
        return await ctx.reply(_("paimon links"))

    hoyolab = SlashCommandGroup(
        name="hoyolab",
        name_localizations={"ru": "хоелаб"},
        description="Follow your resin in Hoyolab!",
        description_localizations={"ru": "Отслеживайте свою смолу и получайте дейли отметки в Хоёлабе!"},
        command_tag="genshin",
    )

    @hoyolab.command(
        name="auth",
        name_localizations={"ru": "авторизоваться"},
        description="Necessary auth for using commands.",
        description_localizations={"ru": "Обязательная авторизация для использования геншин команд."},
    )
    async def follow_streamer(
        self,
        ctx,
    ) -> None:
        await ctx.respond(_("instruction"), view=GenshinAuth(self.bot), ephemeral=True)

    @hoyolab.command(
        name="resin",
        name_localizations={"ru": "смола"},
        description="Resin and stamina brief.",
        description_localizations={"ru": "Краткая сводка по смоле и топливе"},
    )
    @discord.commands.option(
        name="user_id",
        name_localizations={"ru": "айди"},
        description="Check someone else.",
        description_localizations={"ru": "Проверерить кого-то другого."},
        required=False,
    )
    async def check_resin_count(self, ctx, user_id=None) -> None:
        await ctx.defer(ephemeral=True)
        if user_id is None:
            user_id = ctx.user.id
        else:
            try:
                user_id = int(user_id)
            except ValueError:
                await ctx.respond(
                    content=_("Wrong discord ID"), ephemeral=True
                )
                return

        genshin_api = GenshinAPI()
        data = await genshin_api.get_user_data(guild_id=ctx.guild.id, user_id=user_id)
        if data is False:
            await ctx.respond(
                content=_("You are not logged in"), ephemeral=True
            )
            return

        if data is {}:
            await ctx.respond(
                content=_("Your cookie out of date"), ephemeral=True
            )
            return

        fields = generate_fields(data)

        embed = get_embed(
            title=_("Resin"),
            author_name=ctx.user.display_name,
            author_icon_URL=ctx.user.avatar,
            fields=fields,
        )
        await ctx.send_followup(content="", embed=embed)

    @hoyolab.command(
        name="notes",
        name_localizations={"ru": "заметки"},
        description="Shows all info.",
        description_localizations={"ru": "Вся информация о вашем аккаунте."},
    )
    async def check_notes(self, ctx) -> None:
        await ctx.defer(ephemeral=True)
        user = await UsagiGenshin.get(guild_id=ctx.guild.id, user_id=ctx.user.id)
        if user is None:
            await ctx.respond(
                content=_("You are not logged in"), ephemeral=True
            )
            return

        fields = generate_notes_fields(user)

        embed = get_embed(
            title=_("Notes"),
            author_name=ctx.user.display_name,
            author_icon_URL=ctx.user.avatar,
            fields=fields,
        )
        await ctx.send_followup(content="", embed=embed)

    @hoyolab.command(
        name="code",
        name_localizations={"ru": "код"},
        description="Activate genshin promo code.",
        description_localizations={"ru": "Активировать код."},
    )
    @discord.commands.option(
        name="code",
        name_localizations={"ru": "код"},
        description="Code to activate",
        description_localizations={"ru": "Код для активации."},
    )
    async def redeem_code(self, ctx, code: str) -> None:
        await ctx.defer(ephemeral=True)

        genshin_api = GenshinAPI()
        cookies_response = await genshin_api.set_cookies(
            guild_id=ctx.guild.id, user_id=ctx.user.id
        )
        if cookies_response is False:
            await ctx.send_followup(
                content=_("You are not logged in"), ephemeral=True
            )
            return
        if cookies_response is None:
            await ctx.send_followup(
                content=_("Your cookie out of date"), ephemeral=True
            )
            return
        redeem_response = await genshin_api.redeem_code(code)
        if redeem_response is None:
            redeem_response = _("Your cookie out of date")
        await ctx.send_followup(content=redeem_response)

    @hoyolab.command(
        name="subscription",
        name_localizations={"ru": "подписки"},
        description="Activate genshin promo code.",
        description_localizations={"ru": "Активировать код."},
    )
    async def redeem_code(self, ctx) -> None:
        await ctx.defer(ephemeral=True)
        user = await UsagiGenshin.get(guild_id=ctx.guild.id, user_id=ctx.user.id)
        if user is None:
            await ctx.respond(
                content=_("You are not logged in"), ephemeral=True
            )
            return

        fields = generate_all_subs_fields(user)

        embed = get_embed(
            title=_("Subscriptions"),
            author_name=ctx.user.display_name,
            author_icon_URL=ctx.user.avatar,
            fields=fields,
        )
        await ctx.respond(view=SelectSubsView(self.bot, user), embed=embed)

    @commands.command()
    @is_owner()
    async def redeem_code_all(self, ctx, *, codes: str) -> None:
        users = await UsagiGenshin.get_all_by(code_sub=True)
        response_codes = {}
        for user in users:
            genshin_api = GenshinAPI()
            await genshin_api.set_cookies(guild_id=user.guild_id, user_id=user.user_id)
            for code in codes.split(","):
                response = await genshin_api.redeem_code(code.strip())
                user_codes = response_codes.setdefault(user.user_id, {})
                user_codes.setdefault(code, response)

        await ctx.reply(response_codes)


def setup(bot):
    bot.add_cog(Genshin(bot))
