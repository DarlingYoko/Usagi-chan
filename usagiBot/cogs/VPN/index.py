from typing import List

import discord
from discord import SlashCommandGroup, ButtonStyle
from discord.ext import commands, tasks
from pycord18n.extension import _

from usagiBot.cogs.VPN.schemas import UsagiVpnUsers, UsagiVpnRenewalRequests, UsagiVpnHistoryLogs
from usagiBot.cogs.VPN.vpn_utils import generate_vpn_user_info, Vpn3xui
from usagiBot.env import BOT_OWNER
from usagiBot.src.UsagiChecks import is_owner
from usagiBot.src.UsagiUtils import get_embed

from datetime import datetime, timedelta


def get_decisions(ctx: discord.AutocompleteContext) -> List:
    return ['Approved', 'Rejected']

# ------- Notify classes ---------
class VpnNotifyButton(discord.ui.Button):
    def __init__(self, view, bot, vpn_profiles, lang):
        super().__init__()
        self.view = view
        self.bot = bot
        self.vpn_profiles = vpn_profiles
        self.lang = lang
        switch_notify_btn = 'on' if not self.vpn_profiles[0].notify_enabled else 'off'
        btn_style = ButtonStyle.green if not self.vpn_profiles[0].notify_enabled else ButtonStyle.danger

        super().__init__(
            style=btn_style,
            label=self.bot.i18n.get_text(f'VPN notify {switch_notify_btn}', self.lang),
        )

    @discord.ui.button()
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.vpn_profiles[0].user_id:
            return None
        self.vpn_profiles[0].notify_enabled = not self.vpn_profiles[0].notify_enabled
        await UsagiVpnUsers.update_all(
            {'user_id': self.vpn_profiles[0].user_id},
            {'notify_enabled': self.vpn_profiles[0].notify_enabled}
        )

        switch_notify_btn = 'on' if not self.vpn_profiles[0].notify_enabled else 'off'
        self.label = self.bot.i18n.get_text(f'VPN notify {switch_notify_btn}', self.lang)
        self.style = ButtonStyle.green if not self.vpn_profiles[0].notify_enabled else ButtonStyle.danger

        embed = await generate_vpn_user_info(self.bot, self.vpn_profiles, self.lang)
        await interaction.response.edit_message(embed=embed, view=self.view)
        return None

class VpnInfoView(discord.ui.View):
    def __init__(self, bot: discord.Bot, vpn_profiles, lang):
        super().__init__()
        self.add_item(VpnNotifyButton(self, bot, vpn_profiles, lang))
# ------- End Notify classes ---------

# ------- Renew classes ---------
class RenewVpnModal(discord.ui.Modal):
    def __init__(self, bot, vpn_profiles, lang) -> None:
        self.bot = bot
        self.vpn_profiles = vpn_profiles
        self.lang = lang
        super().__init__(
            title=self.bot.i18n.get_text('Renew VPN', self.lang)
        )

        self.add_item(
            discord.ui.InputText(
                label=self.bot.i18n.get_text('VPN amount', self.lang),
                placeholder='100'
            )
        )
        self.add_item(
            discord.ui.InputText(
                label=self.bot.i18n.get_text('VPN device count', self.lang),
                value=str(len(vpn_profiles))
            )
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            amount = int(self.children[0].value)
            device_count = int(self.children[1].value)
        except ValueError:
            await interaction.respond(
                embed=get_embed(
                    title=self.bot.i18n.get_text('All fields must be integer', self.lang),
                    color=discord.Color.red(),
                )
            )
            return None
        month_count = amount // device_count // 100
        if month_count < 1:
            await interaction.respond(
                embed=get_embed(
                    title=self.bot.i18n.get_text('Wrong amount and device count', self.lang),
                    color=discord.Color.red(),
                )
            )
            return None

        new_expiry = int(
            (self.vpn_profiles[0].expiration_date + timedelta(days=month_count*31))
            .timestamp() * 1000
        )
        for vpn_profile in self.vpn_profiles:
            date = datetime.now()
            await UsagiVpnRenewalRequests.create(
                user_id=vpn_profile.user_id,
                vpn_username=vpn_profile.vpn_username,
                uuid=vpn_profile.uuid,
                months=month_count,
                new_expiry=new_expiry,
                previous_exp_date=vpn_profile.expiration_date,
                created_at=date,
                active=True,
                status='Pending',
            )
        await interaction.respond(
            embed=get_embed(
                title=self.bot.i18n.get_text('Successful renewal request', self.lang),
                description=self.bot.i18n.get_text('Wait for approval', self.lang),
            )
        )

        renewal_vpns = []
        for idx, vpn_profiles in enumerate(self.vpn_profiles):
            renewal_vpns.append(f'{idx + 1}. <@{vpn_profiles.user_id}> — {vpn_profiles.vpn_username} — {month_count} months')
        result_renewal_vpns = "\n".join(renewal_vpns)

        embed = get_embed(
            title=self.bot.i18n.get_text('New VPN renewal request', self.lang),
            description=result_renewal_vpns
        )
        admin = self.bot.get_user(BOT_OWNER) or await self.bot.fetch_user(BOT_OWNER)
        await admin.send(embed=embed)

        return None

class VpnRenewButton(discord.ui.Button):
    def __init__(self, bot, vpn_profiles, lang):
        self.bot = bot
        self.vpn_profiles = vpn_profiles
        self.lang = lang

        super().__init__(
            style=ButtonStyle.primary,
            label=self.bot.i18n.get_text('VPN renewal request', self.lang),
        )

    @discord.ui.button()
    async def callback(self, interaction):
        await interaction.response.send_modal(
            RenewVpnModal(self.bot, self.vpn_profiles, self.lang)
        )
class VpnInstructionsButton(discord.ui.Button):
    def __init__(self, bot, lang):
        self.bot = bot
        self.lang = lang
        super().__init__(
            style=ButtonStyle.green,
            label=self.bot.i18n.get_text('Instructions', self.lang),
        )

    @discord.ui.button()
    async def callback(self, interaction: discord.Interaction):
        instructions = self.bot.i18n.get_text('VPN full instructions', self.lang)
        embed = get_embed(
            title=self.bot.i18n.get_text('Instructions renew VPN', self.lang),
            description=instructions
        )
        await interaction.respond(embed=embed)

class VpnRenewView(discord.ui.View):
    def __init__(self, bot: discord.Bot, vpn_profiles, lang):
        super().__init__()
        self.add_item(VpnRenewButton(bot, vpn_profiles, lang))
        self.add_item(VpnInstructionsButton(bot, lang))
# ------- End Renew classes ---------


class VPN(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_vpn_expiry.start()

    @tasks.loop(hours=1)
    async def check_vpn_expiry(self):
        """ Checks VPN expiry
            1. Every hour checks VPN expiry.
            2. If there are less than 2 days left -> send message to user
            3. User can press button "Payed", choose period and click "Confirm"
            4. If so, Usagi will ping me to check and confirm the user's extension.
            5. I will check and confirm/decline user's extension.
        """
        vpn_profiles = await UsagiVpnUsers.get_all_by(active=True, notify_enabled=True)
        expired_users = {}
        for vpn_profile in vpn_profiles:
            expiration_delta = vpn_profile.expiration_date - datetime.now()
            if expiration_delta < timedelta(days=2) and not vpn_profile.notified:
                if expired_users.get(vpn_profile.user_id, None) is None:
                    expired_users[vpn_profile.user_id] = [vpn_profile]
                else:
                    expired_users[vpn_profile.user_id].append(vpn_profile)

            if expiration_delta > timedelta(days=2) and vpn_profile.notified:
                await UsagiVpnUsers.update(vpn_profile.id, notified=False)

        for user_id, expired_profiles in expired_users.items():
            lang = self.bot.language.get(int(user_id), "en")
            notify_title = self.bot.i18n.get_text('VPN expire', lang)
            notify_vpns = []
            for idx, expired_profile in enumerate(expired_profiles):
                expired_timer = int(expired_profile.expiration_date.timestamp())
                notify_vpns.append(f'{idx + 1}. {expired_profile.vpn_username} — <t:{expired_timer}:R>')

            max_len = max(len(line.split("—")[0]) for line in notify_vpns)
            formatted_vpn_notify = []
            for line in notify_vpns:
                name, date = line.split(" — ")
                formatted_vpn_notify.append(f"`{name.ljust(max_len)}` — {date}")

            result_vpn_info = "\n".join(formatted_vpn_notify)
            embed = get_embed(title=notify_title, description=result_vpn_info)

            user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
            await user.send(embed=embed, view=VpnRenewView(self.bot, expired_profiles, lang))
            await UsagiVpnUsers.update_all(
                {'user_id': expired_profiles[0].user_id},
                {'notified': True}
            )

    @check_vpn_expiry.before_loop
    async def before_check_vpn_expiry(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Checking VPN expiry.")

    vpn = SlashCommandGroup(
        name="vpn",
        name_localizations={"ru": "впн"},
        description="VPN subscription and info.",
        description_localizations={"ru": "ВПН подписка и информация."},
    )

    @vpn.command(
        name="info",
        name_localizations={"ru": "инфо"},
        description="Full info about VPN subscription.",
        description_localizations={"ru": "Вся информация про ВПН подписку"},
    )
    async def vpn_info(self, ctx: discord.ApplicationContext):
        vpn_profiles = await UsagiVpnUsers.get_all_by(user_id = ctx.author.id, active = True)
        lang = self.bot.language.get(int(ctx.author.id), "en")

        if not vpn_profiles:
            await ctx.respond(_("VPN no profiles"))
            return None

        embed = await generate_vpn_user_info(self.bot, vpn_profiles, lang)
        await ctx.respond(embed=embed, view=VpnInfoView(self.bot, vpn_profiles, lang))
        return None

    @vpn.command(
        name="top",
        name_localizations={"ru": "топ"},
        description="Top of traffic used users.",
        description_localizations={"ru": "Топ пользователей по потреблению траффика."},
    )
    @commands.cooldown(per=60, rate=1, type=commands.BucketType.channel)
    async def vpn_top(self, ctx: discord.ApplicationContext):
        vpn3xui = Vpn3xui()
        await vpn3xui.login()

        top_users = await vpn3xui.get_top_traffic()

        title = _("Top vpn")
        result = list(
            map(
                lambda x: _("Counter vpn users").format(
                    count=x[0] + 1,
                    name=x[1],
                    traffic=top_users[x[1]],
                ),
                enumerate(top_users),
            )
        )

        max_len = max(len(line.split("-")[0]) for line in result)
        formatted_result = []
        for line in result:
            name, traffic = line.split("- ")
            formatted_result.append(f"{name.ljust(max_len)} - {traffic}")

        result_text = "```\n" + "\n".join(formatted_result) + "\n```"
        embed = get_embed(title=title, description=result_text)
        await ctx.respond(embed=embed)

    @vpn.command(
        name="renew",
        name_localizations={"ru": "продлить"},
        description="Renew VPN subscription.",
        description_localizations={"ru": "Продлить ВПН подписку."},
        checks=[is_owner().predicate]
    )
    @discord.commands.option(
        name="decision",
        name_localizations={"ru": "решение"},
        description="Decision about user VPN renewal.",
        description_localizations={"ru": "Решение про продлению ВПНа."},
        required=True,
        autocomplete=get_decisions
    )
    async def renew_vpn(self, ctx: discord.ApplicationContext, user: discord.Member, decision: str):
        # If no payment found or wrong data -> Reject request
        if decision == 'Rejected':
            await UsagiVpnRenewalRequests.update_all(
                {
                    'user_id': user.id,
                    'active': True,
                    'status': 'Pending'
                },
                {
                    'active': False,
                    'status': 'Rejected'
                }
            )
            await ctx.respond(_('Pending profiles rejected').format(user_mention=user.mention))
            await user.send(_('VPN renewal rejected'))
            return None

        # If approved -> update date, add data in tables, inform user
        pending_profiles = await UsagiVpnRenewalRequests.get_all_by(
            user_id = user.id,
            active = True,
            status = 'Pending'
        )
        self.bot.logger.info(f"Pending profiles: {pending_profiles}")
        if not pending_profiles:
            await ctx.respond(_('No pending profiles').format(user_mention=user.mention))
            return None

        vpn3xui = Vpn3xui()
        await vpn3xui.login()

        cur_date = datetime.now()

        # update all user's profiles
        for pending_profile in pending_profiles:
            # update in 3x-ui
            self.bot.logger.info(f"Updating profile: {pending_profile.vpn_username}")
            await vpn3xui.update_user_expiry_time(
                pending_profile.vpn_username,
                pending_profile.uuid,
                pending_profile.new_expiry
            )

            # add logs
            self.bot.logger.info(f"Adding log profile: {pending_profile.vpn_username}")
            await UsagiVpnHistoryLogs.create(
                user_id=pending_profile.user_id,
                uuid = pending_profile.uuid,
                action = 'Renewal',
                months = pending_profile.months,
                new_expiry = datetime.fromtimestamp(pending_profile.new_expiry/1000),
                previous_exp_date = pending_profile.previous_exp_date,
                admin_discord = ctx.author.id,
                timestamp = cur_date
            )

        # update in UsagiVpnUsers
        self.bot.logger.info(f"Update profiles")
        await UsagiVpnUsers.update_all(
            {'user_id': pending_profiles[0].user_id},
            {
                'expiration_date': datetime.fromtimestamp(pending_profiles[0].new_expiry/1000),
                'updated_at': cur_date,
                'notified': False,
            }
        )

        # update in requests
        self.bot.logger.info(f"Update requests")
        await UsagiVpnRenewalRequests.update_all(
            {
                'user_id': user.id,
                'active': True,
                'status': 'Pending'
            },
            {
                'active': False,
                'status': 'Approved'
            }
        )

        await ctx.respond(_('Profiles successfully renewed').format(user_mention=user.mention))
        await user.send(_('Your VPN renewal approved'))
        return None

    @vpn.command(
        name="request",
        name_localizations={"ru": "запрос"},
        description="Manual request for renew VPN subscription.",
        description_localizations={"ru": "Ручной запрос на продление ВПН подписки."},
    )
    async def request_renew_vpn(self, ctx: discord.ApplicationContext):
        vpn_profiles = await UsagiVpnUsers.get_all_by(user_id=ctx.author.id, active=True)
        if not vpn_profiles:
            await ctx.respond(_("VPN no profiles"))
            return None

        lang = self.bot.language.get(int(ctx.author.id), "en")
        renewal_request_title = _("VPN manual renewal request")
        embed = await generate_vpn_user_info(self.bot, vpn_profiles, lang)
        embed.title = renewal_request_title
        embed.fields = []
        await ctx.respond(embed=embed, view=VpnRenewView(self.bot, vpn_profiles, lang))
        return None


def setup(bot):
    bot.add_cog(VPN(bot))