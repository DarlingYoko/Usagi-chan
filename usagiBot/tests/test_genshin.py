import datetime
import sys
import pytest

import discord
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

        # Mock config per guild — fetched once for all users
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id="ch1"),
            mock.MagicMock(guild_id="g2", generic_id="ch2"),
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
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(
                guild_id="test_guild_id_12", generic_id="generic_channel_id_12"
            ),
            mock.MagicMock(
                guild_id="test_guild_id_22", generic_id="generic_channel_id_22"
            ),
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

        # configs fetched once for all users, no per-user lookups
        self.mock_UsagiConfig.get_all_by.assert_awaited_once_with(
            command_tag="genshin"
        )
        self.mock_UsagiConfig.get.assert_not_called()
        # channels come from the cache, no API fetch needed
        self.Genshin.bot.fetch_channel.assert_not_called()

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

    async def test_check_resin_overflow_batches_config_lookup(self) -> None:
        def make_user(uid, guild_id):
            return mock.MagicMock(
                id=uid,
                guild_id=guild_id,
                genshin_resin_sub_notified=False,
                starrail_resin_sub_notified=False,
                zzz_resin_sub_notified=False,
            )

        self.mock_UsagiHoyolab.get_all_by_or.return_value = [
            make_user(1, "test_guild_1"),
            make_user(2, "test_guild_1"),
            make_user(3, "test_guild_2"),
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="test_guild_1", generic_id="chan_1"),
            mock.MagicMock(guild_id="test_guild_2", generic_id="chan_2"),
        ]
        self.channels["chan_1"] = mock.AsyncMock()
        self.channels["chan_2"] = mock.AsyncMock()
        self.mock_GenshinAPI().get_user_data.return_value = {}

        await self.Genshin.check_resin_overflow(self.Genshin)

        self.mock_UsagiConfig.get_all_by.assert_awaited_once_with(
            command_tag="genshin"
        )
        self.mock_UsagiConfig.get.assert_not_called()

    def _resin_user(self, uid, guild_id, user_id):
        return mock.MagicMock(
            id=uid,
            guild_id=guild_id,
            user_id=user_id,
            genshin_resin_sub=True,
            genshin_resin_sub_notified=False,
            starrail_resin_sub=False,
            starrail_resin_sub_notified=False,
            zzz_resin_sub=False,
            zzz_resin_sub_notified=False,
        )

    @staticmethod
    def _overflow_data():
        return {
            "nickname": "aboba",
            "icon": "icon",
            "genshin": mock.MagicMock(current_resin=195),
            "starrail": None,
            "zzz": None,
            "geetest_error": None,
        }

    async def test_check_resin_overflow_survives_user_error(self) -> None:
        self.mock_UsagiHoyolab.get_all_by_or.return_value = [
            self._resin_user(1, "g1", "u1"),
            self._resin_user(2, "g1", "u2"),
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id="ch1"),
        ]
        ch1 = mock.AsyncMock()
        self.channels["ch1"] = ch1
        # first user blows up mid-API (e.g. Hoyolab maintenance), second is fine
        self.mock_GenshinAPI().get_user_data.side_effect = [
            genshin.errors.GenshinException({}, "maintenance"),
            self._overflow_data(),
        ]

        await self.Genshin.check_resin_overflow(self.Genshin)

        assert ch1.send.await_count == 1
        self.Genshin.bot.logger.exception.assert_called()

    async def test_check_resin_overflow_skips_unfetchable_channel(self) -> None:
        self.mock_UsagiHoyolab.get_all_by_or.return_value = [
            self._resin_user(1, "g_bad", "u1"),
            self._resin_user(2, "g_good", "u2"),
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g_bad", generic_id="bad_ch"),
            mock.MagicMock(guild_id="g_good", generic_id="good_ch"),
        ]
        good_ch = mock.AsyncMock()
        self.channels["good_ch"] = good_ch

        async def mock_fetch(cid):
            if cid == "bad_ch":
                raise discord.NotFound(
                    mock.MagicMock(status=404, reason="Not Found"),
                    "Unknown Channel",
                )
            return self.channels.get(cid)

        self.Genshin.bot.fetch_channel = mock.AsyncMock(side_effect=mock_fetch)
        self.mock_GenshinAPI().get_user_data.side_effect = [self._overflow_data()]

        await self.Genshin.check_resin_overflow(self.Genshin)

        assert good_ch.send.await_count == 1

    async def test_check_resin_overflow_skips_deleted_user(self) -> None:
        self.mock_UsagiHoyolab.get_all_by_or.return_value = [
            self._resin_user(1, "g1", "u1"),
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id="ch1"),
        ]
        ch1 = mock.AsyncMock()
        self.channels["ch1"] = ch1
        # row vanished between the query and the API call
        self.mock_GenshinAPI().get_user_data.return_value = {}

        await self.Genshin.check_resin_overflow(self.Genshin)

        ch1.send.assert_not_awaited()
        self.mock_UsagiHoyolab.update.assert_not_called()

    async def test_check_resin_overflow_survives_db_error(self) -> None:
        self.mock_UsagiHoyolab.get_all_by_or.side_effect = Exception("db down")

        await self.Genshin.check_resin_overflow(self.Genshin)

        self.Genshin.bot.logger.exception.assert_called()

    @freeze_time("2001-03-21 16:00:00")
    async def test_claim_daily_reward_survives_claim_error(self) -> None:
        self.mock_UsagiHoyolab.get_all_by_or.return_value = [
            mock.MagicMock(
                guild_id="g1",
                user_id="u1",
                genshin_daily_sub=True,
                starrail_daily_sub=False,
                zzz_daily_sub=False,
                id=1,
            ),
            mock.MagicMock(
                guild_id="g1",
                user_id="u2",
                genshin_daily_sub=True,
                starrail_daily_sub=False,
                zzz_daily_sub=False,
                id=2,
            ),
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id="ch1"),
        ]
        ch1 = mock.AsyncMock()
        self.channels["ch1"] = ch1
        self.mock_GenshinAPI().claim_daily_reward.side_effect = [
            Exception("boom"),
            True,
        ]

        await self.Genshin.claim_daily_reward(self.Genshin)

        assert ch1.send.await_count == 1
        self.Genshin.bot.logger.exception.assert_called()

    @freeze_time("2001-03-21 16:00:00")
    async def test_daily_reward_claim_notify_batches_config_lookup(self) -> None:
        self.mock_UsagiHoyolab.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", user_id="u1"),
            mock.MagicMock(guild_id="g1", user_id="u2"),
            mock.MagicMock(guild_id="g2", user_id="u3"),
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id="ch1"),
            mock.MagicMock(guild_id="g2", generic_id="ch2"),
        ]
        ch1 = mock.AsyncMock()
        ch2 = mock.AsyncMock()
        self.channels["ch1"] = ch1
        self.channels["ch2"] = ch2

        await self.Genshin.daily_reward_claim_notify(self.Genshin)

        self.mock_UsagiConfig.get_all_by.assert_awaited_once_with(
            command_tag="genshin"
        )
        self.mock_UsagiConfig.get.assert_not_called()
        self.Genshin.bot.fetch_channel.assert_not_called()

        links = (
            "\nGenshin - https://bit.ly/genshin_daily"
            "\nHonkai - https://bit.ly/honkai_daily"
            "\nZZZ - https://bit.ly/zzz_daily"
        )
        ch1.send.assert_awaited_once_with(
            "Don't forget to claim your daily reward!"
            " <:UsagiLove:1084226975113158666> \n<@u1>, <@u2>" + links
        )
        ch2.send.assert_awaited_once_with(
            "Don't forget to claim your daily reward!"
            " <:UsagiLove:1084226975113158666> \n<@u3>" + links
        )

    async def test_check_resin_count_expired_cookie(self) -> None:
        ctx = mock.AsyncMock()
        ctx.guild.id = "g1"
        ctx.user.id = "u1"
        self.mock_UsagiHoyolab.get_all_by.return_value = [mock.MagicMock(id=1)]
        self.mock_GenshinAPI().get_user_data.return_value = {}

        await self.Genshin.check_resin_count.callback(self.Genshin, ctx)

        ctx.respond.assert_called_with(
            content="Your cookie is out of date, pls relogin `/hoyolab login`",
            ephemeral=True,
        )


    async def test_check_resin_count_keeps_dead_account_listed(self) -> None:
        # A second account must not make the first one vanish from the list
        # just because Hoyolab rejected its cookies.
        ctx = mock.AsyncMock()
        ctx.guild.id = "g1"
        ctx.user.id = 5
        self.mock_UsagiHoyolab.get_all_by.return_value = [
            mock.MagicMock(id=2, show_genshin=True, show_starrail=True, show_zzz=True),
            mock.MagicMock(id=1, show_genshin=True, show_starrail=True, show_zzz=True),
        ]
        # fetched in DB-id order: id 1 (dead) first, then id 2
        self.mock_GenshinAPI().get_user_data.side_effect = [
            {},
            {"nickname": "Monopolia", "icon": None, "geetest_error": None},
        ]

        await self.Genshin.check_resin_count.callback(self.Genshin, ctx, "5")

        view = ctx.send_followup.call_args.kwargs["view"]
        labels = [option.label for option in view.account_select.options]
        self.assertEqual(len(labels), 2)
        # sorted by DB id, so the dead account (id 1) comes first
        self.assertIn("#1", labels[0])
        self.assertEqual(labels[1], "Monopolia")
        self.assertIsNotNone(view.games_select)


class TestHoyolabAPI(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        import usagiBot.cogs.Hoyolab.genshin_utils as genshin_utils

        self.genshin_utils = genshin_utils
        init_i18n()
        self.api = genshin_utils.HoyolabAPI()
        self.api.client = mock.MagicMock()

    async def test_get_user_data_returns_empty_on_genshin_error(self) -> None:
        with mock.patch.object(
            self.genshin_utils, "UsagiHoyolab", new_callable=mock.AsyncMock
        ) as mock_hoyolab:
            mock_hoyolab.get.return_value = mock.MagicMock(
                ltuid_v2="1", ltmid_v2="2", ltoken_v2="3", cookie_token_v2="4"
            )
            self.api.client.get_hoyolab_user = mock.AsyncMock(
                side_effect=genshin.errors.GenshinException({}, "maintenance")
            )
            data = await self.api.get_user_data(db_id=1)

        self.assertEqual(data, {})

    async def test_check_cookies_false_on_generic_error(self) -> None:
        self.api.client.get_genshin_user = mock.AsyncMock(
            side_effect=genshin.errors.GenshinException({}, "maintenance")
        )

        result = await self.api.check_cookies({"ltuid_v2": "1"})

        self.assertFalse(result)

    async def test_redeem_code_cooldown_then_success(self) -> None:
        self.api.client.redeem_code = mock.AsyncMock(
            side_effect=[genshin.RedemptionCooldown(), None]
        )

        with mock.patch.object(
            self.genshin_utils.asyncio, "sleep", new_callable=mock.AsyncMock
        ):
            result = await self.api.redeem_code("CODE", "Genshin")

        self.assertEqual(result, "Successfully redeemed.")
        self.assertEqual(self.api.client.redeem_code.await_count, 2)

    async def test_redeem_code_cooldown_bounded(self) -> None:
        self.api.client.redeem_code = mock.AsyncMock(
            side_effect=genshin.RedemptionCooldown()
        )

        with mock.patch.object(
            self.genshin_utils.asyncio, "sleep", new_callable=mock.AsyncMock
        ):
            result = await self.api.redeem_code("CODE", "Genshin")

        self.assertEqual(result, genshin.RedemptionCooldown.msg)
        self.assertLessEqual(self.api.client.redeem_code.await_count, 3)
