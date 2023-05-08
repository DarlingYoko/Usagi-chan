import asyncio
from datetime import datetime, timedelta
from string import Template

import discord
import genshin

from usagiBot.db.models import UsagiGenshin
from pycord18n.extension import _

blue_text = Template("""```ansi\n[2;31m[2;34m$count[0m[2;31m[0m```""")
red_text = Template("""```ansi\n[2;31m$count[0m```""")


class GenshinAPI:
    def __init__(self):
        self.client = genshin.Client(game=genshin.Game.GENSHIN)

    async def set_cookies(self, guild_id, user_id) -> bool:
        user = await UsagiGenshin.get(guild_id=guild_id, user_id=user_id)
        if user is None:
            return False
        self.client.set_cookies(user.cookies)
        return True

    async def new_user_auth(self, guild_id, user_id, cookies):
        self.client.set_cookies(cookies)
        try:
            await self.client.get_genshin_user(701700971)
        except genshin.InvalidCookies:
            return False
        user = await UsagiGenshin.get(guild_id=guild_id, user_id=user_id)
        if user is None:
            await UsagiGenshin.create(
                guild_id=guild_id,
                user_id=user_id,
                cookies=cookies,
                resin_sub=False,
                resin_sub_notified=False,
                daily_sub=False,
                code_sub=False,
            )
        else:
            await UsagiGenshin.update(
                id=user.id,
                cookies=cookies,
            )
        return True

    async def get_user_data(self, guild_id, user_id):
        cookies_result = await self.set_cookies(guild_id=guild_id, user_id=user_id)
        if not cookies_result:
            return False
        data = await self.client.get_genshin_notes()
        return data

    async def redeem_code(self, code):
        try:
            await self.client.redeem_code(code)
        except genshin.RedemptionCooldown:
            await asyncio.sleep(5)
            await self.redeem_code(code)
        except genshin.RedemptionException as e:
            return e.msg

        return _("Successfully redeemed")

    async def claim_daily_reward(self, guild_id, user_id):
        cookies_result = await self.set_cookies(guild_id=guild_id, user_id=user_id)
        if not cookies_result:
            return False
        try:
            await self.client.claim_daily_reward(reward=False)
            return True
        except genshin.AlreadyClaimed:
            return False


def generate_resin_fields(data) -> list[discord.EmbedField]:
    resin_timer = int(
        (datetime.now() + data.remaining_resin_recovery_time).timestamp()
    )
    realm_timer = int(
        (datetime.now() + data.remaining_realm_currency_recovery_time).timestamp()
    )

    resin_text = red_text if data.current_resin >= 150 else blue_text
    realm_text = (
        red_text
        if data.current_realm_currency / data.max_realm_currency >= 0.8
        else blue_text
    )

    resin_count = resin_text.substitute({"count": data.current_resin})
    realm_count = realm_text.substitute({"count": data.current_realm_currency})

    daily_withdrawn = (
        "<:greenTick:874767321007276143>"
        if data.claimed_commission_reward
        else "<:redThick:874767320915005471>"
    )

    fields = [
        discord.EmbedField(
            name=_("Resin count"),
            value=_("resin_cap").format(
                resin_count=resin_count, resin_timer=resin_timer
            ),
            inline=True,
        ),
        discord.EmbedField(
            name=_("Realm currency"),
            value=_("realm_cap").format(
                realm_count=realm_count,
                max_realm_currency=data.max_realm_currency,
                realm_timer=realm_timer,
            ),
            inline=True,
        ),
        discord.EmbedField(
            name=_("Dailies"),
            value=_("Completed").format(
                completed_commissions=data.completed_commissions,
                daily_withdrawn=daily_withdrawn,
            ),
            inline=True,
        ),
    ]
    return fields


def generate_notes_fields(user) -> list[discord.EmbedField]:
    today = datetime.today()

    # Calculate the Abyss reset date
    if today.day < 16:
        abyss_reset_date = datetime(year=today.year, month=today.month, day=16)
    else:
        abyss_reset_date = (today.replace(day=1) + timedelta(days=32)).replace(
            day=1
        )
    abyss_reset_date = int(abyss_reset_date.timestamp())

    # Calculate the New patch date
    patch_date = datetime(year=2023, month=3, day=1, hour=3)
    while patch_date < today:
        patch_date += timedelta(weeks=6)
    patch_date = int(patch_date.timestamp())

    # Calculate the New presentation date
    presentation_date = datetime(year=2023, month=2, day=17, hour=12)
    while presentation_date < today:
        presentation_date += timedelta(weeks=6)
    presentation_date = int(presentation_date.timestamp())

    resin_notify = (
        "<:greenTick:874767321007276143>"
        if user.resin_sub
        else "<:redThick:874767320915005471>"
    )
    daily_reward = (
        "<:greenTick:874767321007276143>"
        if user.daily_sub
        else "<:redThick:874767320915005471>"
    )
    auto_redeem_code = (
        "<:greenTick:874767321007276143>"
        if user.code_sub
        else "<:redThick:874767320915005471>"
    )

    fields = [
        discord.EmbedField(
            name="_ _",
            value=_("resin_notify").format(
                resin_notify=resin_notify
            ),
            inline=True,
        ),
        discord.EmbedField(
            name="_ _",
            value=_("daily_reward").format(
                daily_reward=daily_reward
            ),
            inline=True,
        ),
        discord.EmbedField(
            name="_ _",
            value=_("Auto redeeming").format(
                auto_redeem_code=auto_redeem_code
            ),
            inline=True,
        ),
        discord.EmbedField(
            name=_("Abyss reset"),
            value=f"<t:{abyss_reset_date}:R>",
            inline=True,
        ),
        discord.EmbedField(
            name=_("Presentation"),
            value=f"<t:{presentation_date}:R>",
            inline=True,
        ),
        discord.EmbedField(
            name=_("New patch"),
            value=f"<t:{patch_date}:R>",
            inline=True,
        ),
    ]
    return fields


async def check_genshin_login(ctx):
    await ctx.defer(ephemeral=True)
    user = await UsagiGenshin.get(guild_id=ctx.guild.id, user_id=ctx.user.id)
    if user is None:
        await ctx.send_followup(content=_("You are not logged in"), ephemeral=True)
        return None
    return user
