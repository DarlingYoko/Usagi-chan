import discord.ui
import pytz

from usagiBot.db.models import UsagiConfig
from usagiBot.cogs.Hoyolab.genshin_utils import *
from usagiBot.src.UsagiUtils import get_embed
from usagiBot.src.UsagiChecks import check_is_already_set_up, check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError

from discord.ext import commands, tasks
from discord import SlashCommandGroup
from pycord18n.extension import _


class SubsSelect(discord.ui.Select):
    def __init__(self, bot, subs_acc_select):
        super().__init__()
        self.bot = bot
        self.subs_acc_select = subs_acc_select

        super().__init__(
            placeholder="Select subscription",
            min_values=1,
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
                    label="ZZZ resin notify",
                    value="zzz_resin",
                ),
                discord.SelectOption(
                    label="ZZZ daily claim",
                    value="zzz_daily",
                ),
                discord.SelectOption(
                    label="Daily reward notify",
                    description="Notify you about to claim daily reward.",
                    value="daily_notify",
                ),
            ]
        )

    @discord.ui.select(
        placeholder="Select subscription",
        max_values=5,

    )
    async def callback(self, interaction):
        user = self.subs_acc_select.user
        data = self.subs_acc_select.data
        for sub in self.values:
            match sub:
                case "genshin_resin":
                    user.genshin_resin_sub = not user.genshin_resin_sub
                case "genshin_daily":
                    user.genshin_daily_sub = not user.genshin_daily_sub
                case "starrail_resin":
                    user.starrail_resin_sub = not user.starrail_resin_sub
                case "starrail_daily":
                    user.starrail_daily_sub = not user.starrail_daily_sub
                case "zzz_resin":
                    user.zzz_resin_sub = not user.zzz_resin_sub
                case "zzz_daily":
                    user.zzz_daily_sub = not user.zzz_daily_sub
                case "daily_notify":
                    user.daily_notify_sub = not user.daily_notify_sub
                case _:
                    pass

        fields = generate_all_subs_fields(user)
        embed = get_embed(
            title=_("Subscriptions"),
            author_name=data.get("nickname", "Hoyolab user"),
            author_icon_URL=data.get("icon", None),
            fields=fields,
        )
        await UsagiHoyolab.update(
            id=user.id,
            genshin_resin_sub=user.genshin_resin_sub,
            genshin_daily_sub=user.genshin_daily_sub,
            daily_notify_sub=user.daily_notify_sub,
            starrail_daily_sub=user.starrail_daily_sub,
            starrail_resin_sub=user.starrail_resin_sub,
            zzz_daily_sub=user.zzz_daily_sub,
            zzz_resin_sub=user.zzz_resin_sub,
        )
        await interaction.response.edit_message(embed=embed)


class SubsAccountSelect(discord.ui.Select):
    def __init__(self, bot, users_data, users):
        self.bot = bot
        self.users_data = users_data
        self.users = users
        self.user = users[0]
        self.data = users_data[0]
        options = []
        for data in users_data:
            options.append(
                discord.SelectOption(
                    label=data.get("nickname", "Hoyolab user"),
                )
            )

        super().__init__(
            placeholder="Choose account",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):

        data_id = 0
        for i in range(len(self.users_data)):
            if self.users_data[i]["nickname"] == self.values[0]:
                data_id = i
                break
        self.data = self.users_data[data_id]
        self.user = self.users[data_id]

        fields = generate_all_subs_fields(self.user)
        embed = get_embed(
            title=_("Subscriptions"),
            author_name=self.data.get("nickname", "Hoyolab user"),
            author_icon_URL=self.data.get("icon", None),
            fields=fields,
        )
        await interaction.response.edit_message(embed=embed)


class SubsView(discord.ui.View):
    def __init__(self, bot: discord.Bot, users_data, users):
        super().__init__()
        subs_acc_select = SubsAccountSelect(bot, users_data, users)
        self.add_item(subs_acc_select)
        self.add_item(SubsSelect(bot, subs_acc_select))


class LoginButton(discord.ui.View):
    def __init__(self, bot, user, *items):
        super().__init__(*items)
        self.bot = bot
        self.user = user

    @discord.ui.button(label="Login")
    async def button_callback(self, button, interaction):
        lang = self.bot.language.get(self.user.id, "en")
        title = self.bot.i18n.get_text("Login Hoyolab account", lang)
        await interaction.response.send_modal(
            LoginModal(bot=self.bot, user=self.user, title=title)
        )


class LoginModal(discord.ui.Modal):
    def __init__(self, bot, user, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.bot = bot
        self.user = user

        self.add_item(discord.ui.InputText(label="ltuid_v2"))
        self.add_item(discord.ui.InputText(label="ltmid_v2"))
        self.add_item(discord.ui.InputText(label="ltoken_v2"))
        self.add_item(discord.ui.InputText(label="cookie_token_v2"))

    async def callback(self, interaction: discord.Interaction):

        guild_id = interaction.guild_id
        user_id = interaction.user.id
        ltuid_v2 = self.children[0].value
        ltmid_v2 = self.children[1].value
        ltoken_v2 = self.children[2].value
        cookie_token_v2 = self.children[3].value

        lang = self.bot.language.get(user_id, "en")

        hoyolab_api = HoyolabAPI()
        cookies = {
            "ltuid_v2": ltuid_v2,
            "ltmid_v2": ltmid_v2,
            "account_id_v2": ltuid_v2,
            "ltoken_v2": ltoken_v2,
            "cookie_token_v2": cookie_token_v2,
        }
        result = await hoyolab_api.check_cookies(cookies)
        if not result:
            response = self.bot.i18n.get_text("Failed to auth", lang)
            await interaction.response.edit_message(content=response, view=None)
            return
        # Create new Hoyolab user
        await UsagiHoyolab.create(
            guild_id=guild_id,
            user_id=user_id,
            ltuid_v2=ltuid_v2,
            ltmid_v2=ltmid_v2,
            account_id_v2=ltuid_v2,
            ltoken_v2=ltoken_v2,
            cookie_token_v2=cookie_token_v2,
        )

        # Send if success

        response = self.bot.i18n.get_text("Success login", lang)
        await interaction.response.edit_message(content=response, view=None)


class HoyolabAccountSelect(discord.ui.Select):
    def __init__(self, bot, users_data):
        self.bot = bot
        self.users_data = users_data
        options = []
        for data in users_data:
            options.append(
                discord.SelectOption(
                    label=data.get("nickname", "Hoyolab user"),
                )
            )

        super().__init__(
            placeholder="Choose account",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        data = [d for d in self.users_data if d["nickname"] == self.values[0]][0]
        fields = generate_fields(data)
        embed = get_embed(
            title=_("Resin"),
            author_name=data.get("nickname", "Hoyolab user"),
            author_icon_URL=data.get("icon", None),
            fields=fields,
        )
        await interaction.response.edit_message(embed=embed)


class HoyolabAccountView(discord.ui.View):
    def __init__(self, bot: discord.Bot, users_data):
        super().__init__(HoyolabAccountSelect(bot, users_data))


class HoyolabAccountDeleteSelect(discord.ui.Select):
    def __init__(self, users_data, users):
        self.users_data = users_data
        self.users = users
        options = []
        for data in users_data:
            options.append(
                discord.SelectOption(
                    label=data.get("nickname", "Hoyolab user"),
                )
            )

        super().__init__(
            placeholder="Choose account",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        data_id = 0
        for i in range(len(self.users_data)):
            if self.users_data[i]["nickname"] == self.values[0]:
                data_id = i
                break
        await UsagiHoyolab.delete(id=self.users[data_id].id)
        self.users_data.pop(data_id)
        self.users.pop(data_id)
        if not self.users_data:
            await interaction.response.edit_message(view=None, content="Done")
            return
        await interaction.response.edit_message(view=HoyolabAccountDeleteView(self.users_data, self.users))


class HoyolabAccountDeleteView(discord.ui.View):
    def __init__(self, users_data, users):
        super().__init__(HoyolabAccountDeleteSelect(users_data, users))


class Hoyolab(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.check_resin_overflow.start()
        self.claim_daily_reward.start()
        self.daily_reward_claim_notify.start()

    @tasks.loop(minutes=30)
    async def check_resin_overflow(self):
        users = await UsagiHoyolab.get_all_by_or(
            genshin_resin_sub=True,
            starrail_resin_sub=True,
            zzz_resin_sub=True
        )

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

            hoyolab_api = HoyolabAPI()
            data = await hoyolab_api.get_user_data(db_id=user.id)
            genshin_data = data.get("genshin", None)
            starrail_data = data.get("starrail", None)
            zzz_data = data.get("zzz", None)

            if genshin_data and genshin_data.current_resin < 180:
                if user.genshin_resin_sub_notified:
                    await UsagiHoyolab.update(id=user.id, genshin_resin_sub_notified=False)

            if starrail_data and starrail_data.current_stamina < 220:
                if user.starrail_resin_sub_notified:
                    await UsagiHoyolab.update(id=user.id, starrail_resin_sub_notified=False)

            if zzz_data and zzz_data.battery_charge.current < 220:
                if user.zzz_resin_sub_notified:
                    await UsagiHoyolab.update(id=user.id, zzz_resin_sub_notified=False)

            lang = self.bot.language.get(user.user_id, "en")
            if (
                    genshin_data and
                    user.genshin_resin_sub and
                    not user.genshin_resin_sub_notified and
                    genshin_data.current_resin >= 180
            ):
                notify_text = self.bot.i18n.get_text("resin cap", lang).format(
                    user_id=user.user_id,
                    nickname=data["nickname"],
                    current_resin=genshin_data.current_resin
                )
                await channel.send(content=notify_text)
                await UsagiHoyolab.update(id=user.id, genshin_resin_sub_notified=True)
            if (
                    starrail_data and
                    user.starrail_resin_sub and not
                    user.starrail_resin_sub_notified and
                    starrail_data.current_stamina >= 220
            ):
                notify_text = self.bot.i18n.get_text("stamina cap", lang).format(
                    user_id=user.user_id,
                    nickname=data["nickname"],
                    current_stamina=starrail_data.current_stamina
                )
                await channel.send(content=notify_text)
                await UsagiHoyolab.update(id=user.id, starrail_resin_sub_notified=True)

            if (
                    zzz_data and
                    user.zzz_resin_sub and not
                    user.zzz_resin_sub_notified and
                    zzz_data.battery_charge.current >= 220
            ):
                notify_text = self.bot.i18n.get_text("energy cap", lang).format(
                    user_id=user.user_id,
                    nickname=data["nickname"],
                    current_energy=zzz_data.battery_charge.current
                )
                await channel.send(content=notify_text)
                await UsagiHoyolab.update(id=user.id, zzz_resin_sub_notified=True)

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

        users = await UsagiHoyolab.get_all_by(daily_notify_sub=True)
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
            links = "\nGenshin - https://bit.ly/genshin_daily\nHonkai - https://bit.ly/honkai_daily\nZZZ - https://bit.ly/zzz_daily"
            text = "Don't forget to claim your daily reward! <:UsagiLove:1084226975113158666> \n" \
                   + users_text \
                   + links
            await channel.send(text)

    @daily_reward_claim_notify.before_loop
    async def before_daily_reward_claim_notify(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("daily_reward_claim_notify")

    @tasks.loop(hours=1)
    async def claim_daily_reward(self):
        moscow_tz = pytz.timezone("Europe/Moscow")
        time_in_moscow = datetime.now(moscow_tz)
        if time_in_moscow.hour != 19:
            return
        users = await UsagiHoyolab.get_all_by_or(
            genshin_daily_sub=True,
            starrail_daily_sub=True,
            zzz_daily_sub=True)
        channels = []
        out_date_cookies = []

        for user in users:
            config = await UsagiConfig.get(
                guild_id=user.guild_id, command_tag="genshin"
            )
            if not config:
                continue
            channel = await self.bot.fetch_channel(config.generic_id)

            hoyolab_api = HoyolabAPI()
            respone = None
            if user.genshin_daily_sub:
                respone = await hoyolab_api.claim_daily_reward(
                    db_id=user.id,
                    game=genshin.Game.GENSHIN
                )
            if user.starrail_daily_sub:
                respone = await hoyolab_api.claim_daily_reward(
                    db_id=user.id,
                    game=genshin.Game.STARRAIL
                )
            if user.zzz_daily_sub:
                respone = await hoyolab_api.claim_daily_reward(
                    db_id=user.id,
                    game=genshin.Game.ZZZ
                )
            if respone == "InvalidCookies":
                out_date_cookies.append((user.user_id, channel))
                respone = None
            if respone and channel not in channels:
                channels.append(channel)
        for channel in channels:
            await channel.send(
                content=("Claimed daily rewards.\n"
                         "To follow use `/hoyolab sub genshin_reward_claim/honkai_reward_claim `")
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
        link_1 = (
            "<https://docs.google.com/spreadsheets/d/1l9HPu2cAzTckdXtr7u-7D8NSKzZNUqOuvbmxERFZ_6w/edit#gid=955728278>")
        link_2 = (
            "<https://docs.google.com/spreadsheets/d/e/2PACX-1vRIWjzFwAZZoBvKw2oiNaVpppI9atoV0wxuOjulKRJECrg_BN404d7LoKlHp8RMX8hegDr4b8jlHjYy/pubhtml>")
        link_3 = (
            "<https://docs.google.com/spreadsheets/u/0/d/1nGCs3jx1nVysEdH-2CliKEMj7KIwhILUMXTkQKDQoJA/htmlview#gid=0>")
        answer = _("links to primogems")
        text = "\n".join([answer, link_1, link_2, link_3])
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
        checks=[
            check_is_already_set_up().predicate
        ],
    )

    @hoyolab.command(
        name="login",
        name_localizations={"ru": "логин"},
        description="Necessary login Hoyolab account for using commands.",
        description_localizations={"ru": "Обязательная авторизация для использования хоёлаб команд."},
    )
    async def login(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            _("Please login hoyolab"),
            view=LoginButton(self.bot, ctx.user),
            ephemeral=True
        )

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
                    content=_("Wrong discord ID"),
                    ephemeral=True
                )
                return
        users = await UsagiHoyolab.get_all_by(guild_id=ctx.guild.id, user_id=user_id)
        if not users:
            await ctx.respond(
                content=_("You are not logged in"), ephemeral=True
            )
            return
        users_data = []
        for user in users:
            hoyolab_api = HoyolabAPI()
            data = await hoyolab_api.get_user_data(db_id=user.id)
            users_data.append(data)

        if not users_data:
            await ctx.respond(
                content=_("Your cookie out of date"),
                ephemeral=True
            )
            return

        fields = generate_fields(users_data[0])
        embed = get_embed(
            title=_("Resin"),
            author_name=users_data[0].get("nickname", "Hoyolab user"),
            author_icon_URL=users_data[0].get("icon", None),
            fields=fields,
        )
        await ctx.send_followup(content="", embed=embed, view=HoyolabAccountView(self.bot, users_data))

        if users_data[0]["geetest_error"] is not None:
            await ctx.respond(
                content=_("geetest error").format(geetest_error=users_data[0]["geetest_error"]),
                ephemeral=True
            )

    @hoyolab.command(
        name="notes",
        name_localizations={"ru": "заметки"},
        description="Shows all info.",
        description_localizations={"ru": "Вся информация о вашем аккаунте."},
    )
    async def check_notes(self, ctx) -> None:
        await ctx.defer()

        fields = generate_notes_fields()

        embed = get_embed(
            title=_("Notes"),
            author_name=ctx.user.display_name,
            author_icon_URL=ctx.user.avatar,
            fields=fields,
        )
        await ctx.send_followup(content="", embed=embed)

    # @hoyolab.command(
    #     name="redeem_code",
    #     name_localizations={"ru": "код"},
    #     description="Activate genshin promo code.",
    #     description_localizations={"ru": "Активировать код."},
    # )
    # @discord.commands.option(
    #     name="code",
    #     name_localizations={"ru": "код"},
    #     description="Code to activate",
    #     description_localizations={"ru": "Код для активации."},
    # )
    # @discord.commands.option(
    #     name="game",
    #     name_localizations={"ru": "игра"},
    #     description="For which game code",
    #     description_localizations={"ru": "Для какой игры этот код."},
    #     choices=["Genshin", "Star Rail"],
    # )
    # async def redeem_code(self, ctx, code: str, game: str) -> None:
    #     await ctx.defer(ephemeral=True)
    #
    #     hoyolab_api = GenshinAPI()
    #     cookies_response = await hoyolab_api.set_cookies(
    #         guild_id=ctx.guild.id,
    #         user_id=ctx.user.id,
    #         redemtion_check=True
    #     )
    #     if cookies_response is False:
    #         await ctx.send_followup(
    #             content=_("You are not logged in"), ephemeral=True
    #         )
    #         return
    #     elif cookies_response == "Error cookie_token_v2":
    #         await ctx.send_followup(
    #             content=_("Need to provide cookie_token_v2"), ephemeral=True
    #         )
    #         return
    #     redeem_response = await hoyolab_api.redeem_code(code, game)
    #     await ctx.send_followup(content=redeem_response)

    @hoyolab.command(
        name="subscription",
        name_localizations={"ru": "подписки"},
        description="Activate genshin promo code.",
        description_localizations={"ru": "Активировать код."},
    )
    async def subscriptions(self, ctx) -> None:
        await ctx.defer(ephemeral=True)

        users = await UsagiHoyolab.get_all_by(guild_id=ctx.guild.id, user_id=ctx.user.id)
        if not users:
            await ctx.respond(
                content=_("You are not logged in"), ephemeral=True
            )
            return
        users_data = []
        for user in users:
            hoyolab_api = HoyolabAPI()
            data = await hoyolab_api.get_user_data(db_id=user.id)
            users_data.append({
                "nickname": data["nickname"],
                "icon": data["icon"]
            })

        if not users_data:
            await ctx.respond(
                content=_("Your cookie out of date"),
                ephemeral=True
            )
            return

        fields = generate_all_subs_fields(users[0])

        embed = get_embed(
            title=_("Subscriptions"),
            author_name=users_data[0].get("nickname", "Hoyolab user"),
            author_icon_URL=users_data[0].get("icon", None),
            fields=fields,
        )
        await ctx.respond(embed=embed, view=SubsView(self.bot, users_data, users))

    @hoyolab.command(
        name="delete",
        name_localizations={"ru": "удалить"},
        description="Delete accounts from Hoyolab.",
        description_localizations={"ru": "Удалить аккаунты Хоёлаба."},
    )
    async def delete_hoyolab_account(self, ctx) -> None:
        await ctx.defer(ephemeral=True)

        users = await UsagiHoyolab.get_all_by(guild_id=ctx.guild.id, user_id=ctx.user.id)
        if not users:
            await ctx.respond(
                content=_("You are not logged in"), ephemeral=True
            )
            return
        users_data = []
        for user in users:
            hoyolab_api = HoyolabAPI()
            data = await hoyolab_api.get_user_data(db_id=user.id)
            users_data.append({
                "nickname": data["nickname"],
                "icon": data["icon"]
            })

        if not users_data:
            await ctx.respond(
                content=_("Your cookie out of date"),
                ephemeral=True
            )
            return

        await ctx.respond(content="", view=HoyolabAccountDeleteView(users_data, users))

    # @commands.command()
    # @is_owner()
    # async def redeem_code_all(self, ctx, *, codes: str) -> None:
    #     users = await UsagiHoyolab.get_all_by(code_sub=True)
    #     response_codes = {}
    #     for user in users:
    #         hoyolab_api = GenshinAPI()
    #         await hoyolab_api.set_cookies(guild_id=user.guild_id, user_id=user.user_id)
    #         for code in codes.split(","):
    #             response = await hoyolab_api.redeem_code(code.strip())
    #             user_codes = response_codes.setdefault(user.user_id, {})
    #             user_codes.setdefault(code, response)
    #
    #     await ctx.reply(response_codes)


def setup(bot):
    bot.add_cog(Hoyolab(bot))
