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

    @tasks.loop(minutes=30)
    async def check_resin_overflow(self):
        users = await UsagiGenshin.get_all_by(resin_sub=True)

        for user in users:
            config = await UsagiConfig.get(
                guild_id=user.guild_id, command_tag="genshin"
            )
            if not config:
                continue
            channel = await self.bot.fetch_channel(config.generic_id)

            genshin_api = GenshinAPI()
            data = await genshin_api.get_user_data(
                guild_id=user.guild_id, user_id=user.user_id
            )
            if data.current_resin < 150:
                if user.resin_sub_notified:
                    await UsagiGenshin.update(id=user.id, resin_sub_notified=False)
                continue

            if user.resin_sub_notified:
                continue

            lang = self.bot.language.get(user.user_id, "en")
            notify_text = self.bot.i18n.get_text("resin cap", lang).format(
                user_id=user.user_id,
                current_resin=data.current_resin
            )
            await channel.send(content=notify_text)
            await UsagiGenshin.update(id=user.id, resin_sub_notified=True)

    @check_resin_overflow.before_loop
    async def before_check_resin_overflow(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Checking resin.")

    @tasks.loop(hours=1)
    async def claim_daily_reward(self):
        moscow_tz = pytz.timezone("Europe/Moscow")
        time_in_moscow = datetime.now(moscow_tz)
        if time_in_moscow.hour != 18:
            return
        users = await UsagiGenshin.get_all_by_or(daily_sub=True, honkai_daily_sub=True)
        channels = []

        for user in users:
            config = await UsagiConfig.get(
                guild_id=user.guild_id, command_tag="genshin"
            )
            if not config:
                continue
            channel = await self.bot.fetch_channel(config.generic_id)

            genshin_api = GenshinAPI()
            respone = None
            if user.daily_sub:
                respone = await genshin_api.claim_daily_reward(
                    guild_id=user.guild_id,
                    user_id=user.user_id,
                    game=genshin.Game.GENSHIN
                )
            if user.honkai_daily_sub:
                respone = await genshin_api.claim_daily_reward(
                    guild_id=user.guild_id,
                    user_id=user.user_id,
                    game=genshin.Game.STARRAIL
                )
            if respone and channel not in channels:
                channels.append(channel)
        for channel in channels:
            await channel.send(
                content=("Claimed daily rewards.\n"
                         "To follow use `/hoyolab sub genshin_reward_claim/honkai_reward_claim `"
                         "Or you can do it by yourself"
                         "Genshin - https://bit.ly/genshin_daily\n"
                         "Honkai - https://bit.ly/honkai_daily")
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

    genshin = SlashCommandGroup(
        name="hoyolab",
        name_localizations={"ru": "хоелаб"},
        description="Follow your resin in Hoyolab!",
        description_localizations={"ru": "Отслеживайте свою смолу и получайте дейли отметки в Хоёлабе!"},
        command_tag="genshin",
    )

    genshin_subscriptions = genshin.create_subgroup(
        name="sub",
        name_localizations={"ru": "подписаться"},
        description="Manage your subscriptions to genshin commands",
        description_localizations={"ru": "Настройка ваших подписок на геншин команды"},
    )

    genshin_unsubscriptions = genshin.create_subgroup(
        name="unsub",
        name_localizations={"ru": "отписаться"},
        description="Manage your subscriptions to genshin commands",
        description_localizations={"ru": "Настройка ваших подписок на геншин команды"},
    )

    @genshin.command(
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

    @genshin.command(
        name="resin",
        name_localizations={"ru": "смола"},
        description="Resin brief.",
        description_localizations={"ru": "Краткая сводка по смоле"},
    )
    @discord.commands.option(
        name="user_id",
        name_localizations={"ru": "айди"},
        description="Check someone else.",
        description_localizations={"ru": "Проверерить кого-то другого."},
        required=False,
    )
    async def check_resin_count(self, ctx, user_id: int = None) -> None:
        await ctx.defer(ephemeral=True)
        if user_id is None:
            user_id = ctx.user.id

        genshin_api = GenshinAPI()
        data = await genshin_api.get_user_data(guild_id=ctx.guild.id, user_id=user_id)
        if not data:
            await ctx.respond(
                content=_("You are not logged in"), ephemeral=True
            )
            return

        fields = generate_resin_fields(data)

        embed = get_embed(
            title=_("Resin"),
            author_name=ctx.user.display_name,
            author_icon_URL=ctx.user.avatar,
            fields=fields,
        )
        await ctx.send_followup(content="", embed=embed)

    @genshin.command(
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

    @genshin.command(
        name="code",
        name_localizations={"ru": "код"},
        description="Activate genshin promo code.",
        description_localizations={"ru":"Активировать код."},
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
            await ctx.respond(
                content=_("You are not logged in"), ephemeral=True
            )
            return
        redeem_response = await genshin_api.redeem_code(code)
        await ctx.send_followup(content=redeem_response)

    @genshin_subscriptions.command(
        name="genshin_reward_claim",
        name_localizations={"ru": "геншин_сбор_дейли"},
        description="Subscription to claim daily rewards for Genshin Impact.",
        description_localizations={"ru": "Подписка на сбор дейли отметок для Геншин Импакта."},
    )
    async def reward_claim_sub(
        self,
        ctx,
    ) -> None:
        user = await check_genshin_login(ctx)
        if user is None:
            return

        await UsagiGenshin.update(id=user.id, daily_sub=True)
        await ctx.send_followup(
            content=_("Successfully subscribed you to auto claiming daily rewards")
        )

    @genshin_unsubscriptions.command(
        name="genshin_reward_claim",
        name_localizations={"ru": "геншин_сбор_дейли"},
        description="Unsubscription from claim daily rewards from Genshin Impact.",
        description_localizations={"ru": "Отписка от сбора дейли отметок для Геншин Импакта."},
    )
    async def reward_claim_unsub(
        self,
        ctx,
    ) -> None:
        user = await check_genshin_login(ctx)
        if user is None:
            return

        await UsagiGenshin.update(id=user.id, daily_sub=False)
        await ctx.send_followup(
            content=_("Successfully unsubscribed you from auto claiming daily rewards")
        )

    @genshin_subscriptions.command(
        name="resin_overflow",
        name_localizations={"ru": "кап_смолы"},
        description="Subscription to notification of resin overflow.",
        description_localizations={"ru": "Подписка на уведомление капа смолы."},
    )
    async def resin_overflow_sub(
        self,
        ctx,
    ) -> None:
        user = await check_genshin_login(ctx)
        if user is None:
            return

        await UsagiGenshin.update(id=user.id, resin_sub=True)
        await ctx.send_followup(
            content=_("Successfully subscribed you to notification of resin overflow")
        )

    @genshin_unsubscriptions.command(
        name="resin_overflow",
        name_localizations={"ru": "кап_смолы"},
        description="Unsubscription from notification of resin overflow.",
        description_localizations={"ru": "Отписка от уведомлений капа смолы."},
    )
    async def resin_overflow_unsub(
        self,
        ctx,
    ) -> None:
        user = await check_genshin_login(ctx)
        if user is None:
            return

        await UsagiGenshin.update(id=user.id, resin_sub=False)
        await ctx.send_followup(
            content=_("Successfully unsubscribed you from notification of resin overflow")
        )

    @genshin_subscriptions.command(
        name="auto_code",
        name_localizations={"ru": "авто_коды"},
        description="Subscription to auto redeem codes.",
        description_localizations={"ru": "Подписка на авто ввод кодов."},
    )
    async def auto_code_sub(
        self,
        ctx,
    ) -> None:
        user = await check_genshin_login(ctx)
        if user is None:
            return

        await UsagiGenshin.update(id=user.id, code_sub=True)
        await ctx.send_followup(
            content=_("Successfully subscribed you to auto redeeming codes")
        )

    @genshin_unsubscriptions.command(
        name="auto_code",
        name_localizations={"ru": "авто_коды"},
        description="Unsubscription from auto redeem codes.",
        description_localizations={"ru": "Отписка от авто ввода кодов."},
    )
    async def auto_code_unsub(
        self,
        ctx,
    ) -> None:
        user = await check_genshin_login(ctx)
        if user is None:
            return

        await UsagiGenshin.update(id=user.id, code_sub=False)
        await ctx.send_followup(
            content=_("Successfully unsubscribed you from auto redeeming codes.")
        )

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

    @genshin_subscriptions.command(
        name="honkai_reward_claim",
        name_localizations={"ru": "хонкай_сбор_дейли"},
        description="Subscription to auto redeem daily rewards on Honkai Star Rail.",
        description_localizations={"ru": "Подписка на авто отметки для Хонкай Стар рейл."},
    )
    async def auto_honkai_daily_sub(
            self,
            ctx,
    ) -> None:
        user = await check_genshin_login(ctx)
        if user is None:
            return

        await UsagiGenshin.update(id=user.id, honkai_daily_sub=True)
        await ctx.send_followup(
            content=_("Successfully subscribed you to auto claiming daily rewards")
        )

    @genshin_unsubscriptions.command(
        name="honkai_reward_claim",
        name_localizations={"ru": "хонкай_сбор_дейли"},
        description="Unsubscription from claim daily rewards on Honkai Star Rail.",
        description_localizations={"ru": "Отписка от сбора дейли отметок на Хонкай Стар рейл."},
    )
    async def reward_claim_unsub(
            self,
            ctx,
    ) -> None:
        user = await check_genshin_login(ctx)
        if user is None:
            return

        await UsagiGenshin.update(id=user.id, honkai_daily_sub=False)
        await ctx.send_followup(
            content=_("Successfully unsubscribed you from auto claiming daily rewards")
        )


def setup(bot):
    bot.add_cog(Genshin(bot))
