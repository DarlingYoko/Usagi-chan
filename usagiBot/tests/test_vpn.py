from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase
from unittest import mock

from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *


class TestVpn(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.VPN import index as vpn_index

        self.vpn_index = vpn_index
        self.VPN = vpn_index.VPN

        self.bot = mock.AsyncMock()
        self.bot.i18n = init_i18n()
        self.bot.language = {}
        self.VPN.bot = self.bot

        self.ctx = mock.AsyncMock()
        self.ctx.author.id = 123456789

    @mock.patch("usagiBot.cogs.VPN.index.Vpn3xui")
    async def test_vpn_top(self, mock_Vpn3xui) -> None:
        vpn3xui = mock_Vpn3xui.return_value = mock.AsyncMock()
        vpn3xui.get_top_traffic.return_value = {
            "uid1": {"sub_name": "vpn_user1", "traffic": 100},
            "uid2": {"sub_name": "vpn_user2", "traffic": 50},
            "uid3": {"sub_name": "vpn_user3", "traffic": 10},
        }

        await self.VPN.vpn_top.callback(self.VPN, self.ctx)

        vpn3xui.get_top_traffic.assert_awaited_once()
        called_embed = self.ctx.respond.call_args.kwargs["embed"]
        self.assertEqual(called_embed.title, "Top vpn users by traffic.")
        self.assertEqual(
            called_embed.description,
            "```\n"
            "1. vpn_user1  - 100GB\n"
            "2. vpn_user2  - 50GB\n"
            "3. vpn_user3  - 10GB\n"
            "```",
        )

    @staticmethod
    def _make_inbound() -> mock.MagicMock:
        gb = 1024 ** 3
        client1 = mock.MagicMock(
            sub_id="uid1", email="vpn_user1-DE", expiry_time=1000000000
        )
        client2 = mock.MagicMock(
            sub_id="uid2", email="vpn_user2-DE", expiry_time=1005500000
        )
        stat1 = mock.MagicMock(email="vpn_user1-DE", up=0, down=100 * gb)
        stat2 = mock.MagicMock(email="vpn_user2-DE", up=0, down=50 * gb)
        inbound = mock.MagicMock(client_stats=[stat1, stat2])
        inbound.settings.clients = [client1, client2]
        return inbound

    @mock.patch("usagiBot.cogs.VPN.vpn_utils.Vpn3xui")
    @mock.patch("usagiBot.cogs.VPN.index.UsagiVpnUsers", new_callable=mock.AsyncMock)
    async def test_vpn_info(self, mock_UsagiVpnUsers, mock_Vpn3xui) -> None:
        profiles = [
            mock.MagicMock(sub_name="vpn_user1", uid="uid1", notify_enabled=True),
            mock.MagicMock(sub_name="vpn_user2", uid="uid2", notify_enabled=True),
        ]
        mock_UsagiVpnUsers.get_all_by.return_value = profiles

        vpn3xui = mock_Vpn3xui.return_value = mock.AsyncMock()
        vpn3xui.api.inbound.get_list.return_value = [self._make_inbound()]

        await self.VPN.vpn_info.callback(self.VPN, self.ctx)

        mock_UsagiVpnUsers.get_all_by.assert_awaited_with(
            user_id=123456789, active=True
        )
        # one inbound fetch for the whole command, not one per profile
        self.assertEqual(vpn3xui.api.inbound.get_list.await_count, 1)

        called_embed = self.ctx.respond.call_args.kwargs["embed"]
        self.assertEqual(called_embed.title, "Your VPN profiles")
        self.assertEqual(
            called_embed.description,
            "`1. vpn_user1 ` — 100.0GB — <t:1000000:R>\n"
            "`2. vpn_user2 ` — 50.0GB — <t:1005500:R>",
        )

    def test_sub_info_from_inbounds(self) -> None:
        from usagiBot.cogs.VPN.vpn_utils import sub_info_from_inbounds

        info = sub_info_from_inbounds([self._make_inbound()], "uid1")

        self.assertEqual(info, {"traffic": 100.0, "expiryTime": 1000000})

    def test_top_traffic_from_inbounds(self) -> None:
        from usagiBot.cogs.VPN.vpn_utils import top_traffic_from_inbounds

        top = top_traffic_from_inbounds([self._make_inbound()])

        self.assertEqual(
            top,
            {
                "uid1": {"sub_name": "vpn_user1", "traffic": 100.0},
                "uid2": {"sub_name": "vpn_user2", "traffic": 50.0},
            },
        )
        self.assertEqual(list(top), ["uid1", "uid2"])

    async def test_renew_modal_rejects_zero_subscriptions(self) -> None:
        modal = self.vpn_index.RenewVpnModal(self.bot, [mock.MagicMock()], "en")
        modal.children[0].value = "1000"
        modal.children[1].value = "0"
        interaction = mock.AsyncMock()

        await modal.callback(interaction)

        called_embed = interaction.respond.call_args.kwargs["embed"]
        self.assertEqual(
            called_embed.title,
            self.bot.i18n.get_text("Wrong amount and subscriptions count", "en"),
        )

    async def test_create_vpn_user_invalid_date_responds_error(self) -> None:
        await self.VPN.create_vpn_user.callback(
            self.VPN,
            self.ctx,
            user=mock.MagicMock(),
            sub_name="sub",
            expiry_date="garbage",
        )

        called_embed = self.ctx.respond.call_args.kwargs["embed"]
        self.assertIn("garbage", called_embed.title)

    @mock.patch("usagiBot.cogs.VPN.index.datetime")
    async def test_create_vpn_user_handles_key_error(self, mock_datetime) -> None:
        mock_datetime.strptime.side_effect = KeyError("boom")

        await self.VPN.create_vpn_user.callback(
            self.VPN,
            self.ctx,
            user=mock.MagicMock(),
            sub_name="sub",
            expiry_date="01.01.2030",
        )

        called_embed = self.ctx.respond.call_args.kwargs["embed"]
        self.assertIn("01.01.2030", called_embed.title)

    @mock.patch("usagiBot.cogs.VPN.index.UsagiVpnUsers", new_callable=mock.AsyncMock)
    async def test_check_vpn_expiry_batches_notified_reset(self, mock_users) -> None:
        far_future = datetime.now() + timedelta(days=30)
        mock_users.get_all_by.return_value = [
            mock.MagicMock(id=1, expiration_date=far_future, notified=True, user_id=111),
            mock.MagicMock(id=2, expiration_date=far_future, notified=True, user_id=222),
        ]

        await self.VPN.check_vpn_expiry(self.VPN)

        mock_users.update_by_ids.assert_awaited_once_with([1, 2], {"notified": False})
        mock_users.update.assert_not_called()
