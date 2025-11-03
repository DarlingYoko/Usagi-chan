import datetime
import sys
import pytest

import genshin
from sqlalchemy.ext import asyncio
from unittest import IsolatedAsyncioTestCase, mock
from freezegun import freeze_time

from usagiBot.tests.utils import *


@pytest.fixture(autouse=True)
def clear_imports():
    from usagiBot.db.base import Base
    Base.metadata.clear()
    initial_modules = dict(sys.modules)
    yield
    for module in list(sys.modules.keys()):
        if module not in initial_modules:
            del sys.modules[module]


class TestHoyolabMethods(IsolatedAsyncioTestCase):
    @mock.patch("usagiBot.cogs.Hoyolab.genshin_utils.HoyolabAPI")
    @mock.patch("usagiBot.cogs.Hoyolab.schemas.UsagiHoyolab", new_callable=mock.AsyncMock)
    @mock.patch("usagiBot.cogs.Main.schemas.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(
        self, mock_engine, mock_UsagiConfig, mock_UsagiHoyolab, mock_GenshinAPI
    ) -> None:
        from usagiBot.cogs.Hoyolab.index import Hoyolab

        self.Genshin = Hoyolab

        import usagiBot.cogs.Hoyolab.genshin_utils as genshin_utils

        self.genshin_utils = genshin_utils

        self.mock_UsagiHoyolab = mock_UsagiHoyolab
        self.mock_UsagiConfig = mock_UsagiConfig
        self.mock_GenshinAPI = mock_GenshinAPI

        self.ctx = mock.AsyncMock()
        self.Genshin.bot = mock.AsyncMock()
        # self.Genshin.bot.fetch_channel = mock.AsyncMock()
        self.Genshin.bot.logger = mock.MagicMock()
        self.Genshin.bot.i18n = init_i18n()
        self.Genshin.bot.language = {}
        self.mock_GenshinAPI().get_user_data = mock.AsyncMock()
        self.mock_GenshinAPI().claim_daily_reward = mock.AsyncMock()

        # IMPORTANT: override get_channel + fetch_channel
        self.channels = {}

        def mock_get_channel(cid):
            return self.channels.get(cid)

        async def mock_fetch_channel(cid):
            return self.channels.get(cid)

        self.Genshin.bot.get_channel = mock.MagicMock(side_effect=mock_get_channel)
        self.Genshin.bot.fetch_channel = mock.AsyncMock(side_effect=mock_fetch_channel)

    async def test_check_resin_overflow_loop(self):
        # Mock DB users
        self.mock_UsagiHoyolab.get_all_by_or.return_value = [
            mock.MagicMock(
                guild_id="g1",
                user_id="u1",
                genshin_resin_sub=True,
                starrail_resin_sub=True,
                zzz_resin_sub=True,
                genshin_resin_sub_notified=True,
                starrail_resin_sub_notified=False,
                zzz_resin_sub_notified=False,
                id="u1",
            ),
            mock.MagicMock(
                guild_id="g1",
                user_id="u2",
                genshin_resin_sub=True,
                starrail_resin_sub=True,
                zzz_resin_sub=True,
                genshin_resin_sub_notified=True,
                starrail_resin_sub_notified=False,
                zzz_resin_sub_notified=False,
                id="u2",
            ),
            mock.MagicMock(
                guild_id="g2",
                user_id="u3",
                genshin_resin_sub=True,
                starrail_resin_sub=True,
                zzz_resin_sub=True,
                genshin_resin_sub_notified=False,
                starrail_resin_sub_notified=False,
                zzz_resin_sub_notified=False,
                id="u3",
            ),
        ]

        # Mock config per guild
        self.mock_UsagiConfig.get.side_effect = [
            mock.MagicMock(generic_id="ch1"),
            mock.MagicMock(generic_id="ch1"),
            mock.MagicMock(generic_id="ch2"),
        ]

        # Create fake channels with proper send() mocks
        ch1 = mock.AsyncMock(channel_id="ch1")
        ch2 = mock.AsyncMock(channel_id="ch2")
        self.channels["ch1"] = ch1
        self.channels["ch2"] = ch2

        # API returns
        self.mock_GenshinAPI().get_user_data.side_effect = [
            {
                "nickname": "aboba",
                "icon": "icon",
                "genshin": mock.MagicMock(current_resin=100),
                "starrail": mock.MagicMock(current_stamina=100),
                "zzz": mock.MagicMock(battery_charge=mock.MagicMock(current=100)),
                "geetest_error": None,
            },
            {
                "nickname": "aboba",
                "icon": "icon",
                "genshin": mock.MagicMock(current_resin=195),
                "starrail": mock.MagicMock(current_stamina=155),
                "zzz": mock.MagicMock(battery_charge=mock.MagicMock(current=100)),
                "geetest_error": None,
            },
            {
                "nickname": "aboba",
                "icon": "icon",
                "genshin": mock.MagicMock(current_resin=195),
                "starrail": mock.MagicMock(current_stamina=225),
                "zzz": mock.MagicMock(battery_charge=mock.MagicMock(current=225)),
                "geetest_error": None,
            },
        ]

        await self.Genshin.check_resin_overflow(self.Genshin)

        # database calls
        self.mock_UsagiHoyolab.get_all_by_or.assert_called_with(
            genshin_resin_sub=True, starrail_resin_sub=True, zzz_resin_sub=True
        )

        # u3 should get 2 messages (resin + stamina + zzz)
        assert ch2.send.await_count == 3

        ch2.send.assert_any_call(
            content="<@u3>, you have already 195 resin on `aboba` account! <a:dinkDonk:865127621112102953>"
        )
        ch2.send.assert_any_call(
            content="<@u3>, you have already 225 stamina on `aboba` account! <a:dinkDonk:865127621112102953>"
        )
        ch2.send.assert_any_call(
            content="<@u3>, you have already 225 energy on `aboba` account! <a:dinkDonk:865127621112102953>"
        )

    @freeze_time("2001-03-21 16:00:00")
    async def test_claim_daily_reward_loop(self) -> None:
        self.mock_UsagiHoyolab.get_all_by_or.return_value = [
            mock.MagicMock(
                guild_id="test_guild_id_12",
                user_id="test_user_id_1",
                genshin_daily_sub=True,
                starrail_daily_sub=False,
                zzz_daily_sub=False,
                id="test_user_id_1",
            ),
            mock.MagicMock(
                guild_id="test_guild_id_12",
                user_id="test_user_id_2",
                genshin_daily_sub=False,
                starrail_daily_sub=True,
                zzz_daily_sub=False,
                id="test_user_id_2",
            ),
            mock.MagicMock(
                guild_id="test_guild_id_22",
                user_id="test_user_id_3",
                genshin_daily_sub=True,
                starrail_daily_sub=False,
                zzz_daily_sub=False,
                id="test_user_id_3",
            ),
        ]
        self.mock_UsagiConfig.get.side_effect = [
            mock.MagicMock(generic_id="generic_channel_id_12"),
            mock.MagicMock(generic_id="generic_channel_id_12"),
            mock.MagicMock(generic_id="generic_channel_id_22"),
            None,
        ]
        # Create fake channels with proper send() mocks
        channel_1 = mock.AsyncMock()
        channel_2 = mock.AsyncMock()
        self.channels["generic_channel_id_12"] = channel_1
        self.channels["generic_channel_id_22"] = channel_2

        self.mock_GenshinAPI().claim_daily_reward.side_effect = [
            True,
            False,
            True,
        ]

        await self.Genshin.claim_daily_reward(self.Genshin)
        self.mock_UsagiHoyolab.get_all_by_or.assert_called_with(
            genshin_daily_sub=True, starrail_daily_sub=True, zzz_daily_sub=True
        )

        self.mock_UsagiConfig.get.assert_has_calls(
            [
                mock.call(guild_id="test_guild_id_12", command_tag="genshin"),
                mock.call(guild_id="test_guild_id_12", command_tag="genshin"),
                mock.call(guild_id="test_guild_id_22", command_tag="genshin"),
            ],
            any_order=False,
        )

        self.Genshin.bot.fetch_channel.assert_has_calls(
            [
                mock.call("generic_channel_id_12"),
                mock.call("generic_channel_id_12"),
                mock.call("generic_channel_id_22"),
            ],
            any_order=False,
        )
        self.mock_GenshinAPI().claim_daily_reward.assert_has_calls(
            [
                mock.call(db_id="test_user_id_1", game=genshin.Game.GENSHIN),
                mock.call(db_id="test_user_id_2", game=genshin.Game.STARRAIL),
                mock.call(db_id="test_user_id_3", game=genshin.Game.GENSHIN),
            ],
            any_order=False,
        )
        text = (
            "Claimed daily rewards.\n"
            "To follow use `/hoyolab sub genshin_reward_claim/honkai_reward_claim `"
        )
        channel_1.send.assert_called_with(content=text)
        channel_2.send.assert_called_with(content=text)

    @freeze_time("2001-03-21 15:00:00")
    async def test_generate_resin_fields(self) -> None:
        data = {
            "genshin": mock.MagicMock(
                remaining_resin_recovery_time=datetime.timedelta(hours=2),
                remaining_realm_currency_recovery_time=datetime.timedelta(hours=10),
                current_resin=100,
                current_realm_currency=1400,
                max_realm_currency=1600,
                claimed_commission_reward=True,
                completed_commissions=4,
            )
        }
        fields = self.genshin_utils.generate_fields(data)
        self.assertEqual(fields[0].name, "Resin count:")
        self.assertEqual(
            fields[0].value,
            "```ansi\n[2;31m[2;34m100[0m[2;31m[0m```200 resin\n<t:985194000:R>",
        )
        self.assertEqual(fields[0].inline, True)
        self.assertEqual(fields[1].name, "Realm currency:")
        self.assertEqual(
            fields[1].value, "```ansi\n[2;31m1400[0m```1600 realm\n<t:985222800:R>"
        )
        self.assertEqual(fields[1].inline, True)
        self.assertEqual(fields[2].name, "Dailies:")
        self.assertEqual(
            fields[2].value,
            "_ _\nCompleted: 4\nWithdrawn: <:greenTick:874767321007276143>",
        )
        self.assertEqual(fields[2].inline, True)

    @freeze_time("2023-03-21 15:00:00")
    async def test_generate_notes_fields(self) -> None:
        fields = self.genshin_utils.generate_notes_fields()
        self.assertEqual(fields[0].name, "_ _\nAbyss reset:")
        self.assertEqual(fields[0].value, "<t:1680361200:R>")
        self.assertEqual(fields[0].inline, True)
        self.assertEqual(fields[1].name, "_ _\nPresentation:")
        self.assertEqual(fields[1].value, "<t:1680264000:R>")
        self.assertEqual(fields[1].inline, True)
        self.assertEqual(fields[2].name, "_ _\nNew patch:")
        self.assertEqual(fields[2].value, "<t:1681268400:R>")
        self.assertEqual(fields[2].inline, True)

    async def test_check_genshin_login(self) -> None:
        ctx = mock.AsyncMock()
        ctx.guild.id = "test_guild_id_1"
        ctx.user.id = "test_user_id_1"
        user = mock.MagicMock()
        self.mock_UsagiHoyolab.get.return_value = user

        test_user = await self.genshin_utils.check_genshin_login(ctx)
        self.mock_UsagiHoyolab.get.assert_called_with(
            guild_id="test_guild_id_1", user_id="test_user_id_1"
        )
        self.assertEqual(test_user, user)

    async def test_check_genshin_login_no(self) -> None:
        ctx = mock.AsyncMock()
        ctx.guild.id = "test_guild_id_2"
        ctx.user.id = "test_user_id_22"
        self.mock_UsagiHoyolab.get.return_value = None

        test_user = await self.genshin_utils.check_genshin_login(ctx)
        self.mock_UsagiHoyolab.get.assert_called_with(
            guild_id="test_guild_id_2", user_id="test_user_id_22"
        )
        ctx.send_followup.assert_called_with(
            content="You are not logged in. Pls go `/hoyolab login`", ephemeral=True
        )
        self.assertEqual(test_user, None)
