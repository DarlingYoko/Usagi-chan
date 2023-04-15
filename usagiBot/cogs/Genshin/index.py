import pytz

from usagiBot.db.models import UsagiConfig
from usagiBot.src.UsagiChecks import check_cog_whitelist, is_owner
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.src.UsagiUtils import get_embed
from usagiBot.cogs.Genshin.genshin_utils import *

from discord.ext import commands, tasks
from discord import SlashCommandGroup

instruction = """
1. Go to <https://hoyolab.com>.
2. Login to your account.
3. Press F12 to open Inspect Mode (ie. Developer Tools) or Ctrl+Shift+I.
4. Go to Console.
5. Run command `document.cookie`.
6. Copy output.
"""


class GenshinModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="Cookie"))

    async def callback(self, interaction: discord.Interaction):
        genshin_api = GenshinAPI()
        auth_result = await genshin_api.new_user_auth(
            guild_id=interaction.guild_id,
            user_id=interaction.user.id,
            cookies=self.children[0].value,
        )
        text = "Unsuccessfully auth! Wrong cookies"
        if auth_result:
            text = "Successfully auth"
        await interaction.response.send_message(content=text, ephemeral=True)


class GenshinAuth(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(
        label="Enter",
        style=discord.ButtonStyle.primary,
    )
    async def guess_button(self, button, interaction):
        await interaction.response.send_modal(GenshinModal(title="Genshin auth"))


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

            notify_text = f"<@{user.user_id}>, you have already {data.current_resin} resin! <a:dinkDonk:865127621112102953>"
            await channel.send(content=notify_text)
            await UsagiGenshin.update(id=user.id, resin_sub_notified=True)

    @check_resin_overflow.before_loop
    async def before_twitch_auth_loop(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Checking resin.")

    @tasks.loop(hours=1)
    async def claim_daily_reward(self):
        moscow_tz = pytz.timezone("Europe/Moscow")
        time_in_moscow = datetime.now(moscow_tz)
        if time_in_moscow.hour != 18:
            return
        users = await UsagiGenshin.get_all_by(daily_sub=True)
        channels = []

        for user in users:
            config = await UsagiConfig.get(
                guild_id=user.guild_id, command_tag="genshin"
            )
            if not config:
                continue
            channel = await self.bot.fetch_channel(config.generic_id)

            genshin_api = GenshinAPI()
            respone = await genshin_api.claim_daily_reward(
                guild_id=user.guild_id, user_id=user.user_id
            )
            if respone:
                channels.append(channel)
        for channel in channels:
            await channel.send(
                content="Claimed daily rewards. To follow use `/genshin sub reward_claim `"
            )

    @claim_daily_reward.before_loop
    async def before_twitch_auth_loop(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info(f"Checking daily reward.")

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    genshin = SlashCommandGroup(
        name="genshin",
        description="Follow your resin in Genshin Impact!",
        command_tag="genshin",
    )

    genshin_subscriptions = genshin.create_subgroup(
        name="sub",
        description="Manage your subscriptions to genshin commands",
    )

    genshin_unsubscriptions = genshin.create_subgroup(
        name="unsub",
        description="Manage your subscriptions to genshin commands",
    )

    @genshin.command(name="auth", description="Necessary auth for using commands.")
    async def follow_streamer(
        self,
        ctx,
    ) -> None:
        await ctx.respond(instruction, view=GenshinAuth(), ephemeral=True)

    @genshin.command(name="resin", description="Resin brief.")
    @discord.commands.option(
        name="user_id",
        description="Check someone else.",
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
                content="You are not logged in. Pls go `/genshin auth`", ephemeral=True
            )
            return

        fields = generate_resin_fields(data)

        embed = get_embed(
            title=f"Resin",
            author_name=ctx.user.display_name,
            author_icon_URL=ctx.user.avatar,
            fields=fields,
        )
        await ctx.send_followup(content="", embed=embed)

    @genshin.command(name="notes", description="Shows all info.")
    async def check_notes(self, ctx) -> None:
        await ctx.defer(ephemeral=True)
        user = await UsagiGenshin.get(guild_id=ctx.guild.id, user_id=ctx.user.id)
        if user is None:
            await ctx.respond(
                content="You are not logged in. Pls go `/genshin auth`", ephemeral=True
            )
            return

        fields = generate_notes_fields(user)

        embed = get_embed(
            title=f"Notes",
            author_name=ctx.user.display_name,
            author_icon_URL=ctx.user.avatar,
            fields=fields,
        )
        await ctx.send_followup(content="", embed=embed)

    @genshin.command(name="code", description="Activate genshin promo code.")
    @discord.commands.option(
        name="code",
        description="Code to activate",
        required=True,
    )
    async def redeem_code(self, ctx, code: str) -> None:
        await ctx.defer(ephemeral=True)
        genshin_api = GenshinAPI()
        cookies_response = await genshin_api.set_cookies(
            guild_id=ctx.guild.id, user_id=ctx.user.id
        )
        if cookies_response is False:
            await ctx.respond(
                content="You are not logged in. Pls go `/genshin auth`", ephemeral=True
            )
            return
        redeem_response = await genshin_api.redeem_code(code)
        await ctx.send_followup(content=redeem_response)

    @genshin_subscriptions.command(
        name="reward_claim", description="Subscription to claim daily rewards."
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
            content="Successfully subscribed you to auto claiming daily rewards."
        )

    @genshin_unsubscriptions.command(
        name="reward_claim", description="Unsubscription from claim daily rewards."
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
            content="Successfully unsubscribed you from auto claiming daily rewards."
        )

    @genshin_subscriptions.command(
        name="resin_overflow",
        description="Subscription to notification of resin overflow.",
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
            content="Successfully subscribed you to notification of resin overflow."
        )

    @genshin_unsubscriptions.command(
        name="resin_overflow",
        description="Unsubscription from notification of resin overflow.",
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
            content="Successfully unsubscribed you from notification of resin overflow."
        )

    @genshin_subscriptions.command(
        name="auto_code_sub",
        description="Subscription to auto redeem codes.",
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
            content="Successfully subscribed you to auto redeeming codes."
        )

    @genshin_unsubscriptions.command(
        name="auto_code_sub",
        description="Unsubscription from auto redeem codes.",
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
            content="Successfully unsubscribed you from auto redeeming codes."
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


def setup(bot):
    bot.add_cog(Genshin(bot))
