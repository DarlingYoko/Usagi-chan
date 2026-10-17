import sys
import pytest

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


class TestEndfieldCommands(IsolatedAsyncioTestCase):
    @mock.patch("usagiBot.cogs.ArknightsEndfield.arknights_utils.EndfieldClient")
    @mock.patch("usagiBot.cogs.Main.schemas.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch(
        "usagiBot.cogs.ArknightsEndfield.schemas.UsagiGryphline",
        new_callable=mock.AsyncMock,
    )
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(
        self, mock_engine, mock_UsagiGryphline, mock_UsagiConfig, mock_EndfieldClient
    ) -> None:
        from usagiBot.cogs.ArknightsEndfield.index import Endfield

        self.Endfield = Endfield
        self.mock_UsagiGryphline = mock_UsagiGryphline
        self.mock_UsagiConfig = mock_UsagiConfig
        self.mock_EndfieldClient = mock_EndfieldClient

        self.Endfield.bot = mock.AsyncMock()
        self.Endfield.bot.logger = mock.MagicMock()
        self.Endfield.bot.i18n = init_i18n()
        self.Endfield.bot.language = {}

        self.ctx = mock.AsyncMock()
        self.ctx.guild.id = "g1"
        self.ctx.author.id = "u1"

    async def test_endfield_profile_no_user_awaits_response(self) -> None:
        self.mock_UsagiGryphline.get_all_by.return_value = []
        await self.Endfield.endfield_profile.callback(self.Endfield, self.ctx)
        self.ctx.respond.assert_awaited()

    async def test_endfield_sanity_no_user_awaits_response(self) -> None:
        self.mock_UsagiGryphline.get_all_by.return_value = []
        await self.Endfield.endfield_sanity.callback(self.Endfield, self.ctx)
        self.ctx.respond.assert_awaited()

    async def test_endfield_settings_no_account_awaits_response(self) -> None:
        self.mock_UsagiGryphline.get.return_value = None
        await self.Endfield.endfield_settings.callback(
            self.Endfield, self.ctx, option="Daily reward", uid=123
        )
        self.ctx.respond.assert_awaited()

    async def test_endfield_delete_no_account_awaits_response(self) -> None:
        self.mock_UsagiGryphline.get.return_value = None
        await self.Endfield.endfield_delete.callback(self.Endfield, self.ctx, uid=123)
        self.ctx.respond.assert_awaited()

    @freeze_time("2026-06-13 16:00:00")  # 19:00 Europe/Moscow, when the loop runs
    async def test_claim_loop_skips_attendance_after_failed_signin(self) -> None:
        self.mock_UsagiGryphline.get_all_by_or.return_value = [
            mock.MagicMock(guild_id="g1", user_id="u1", token="t1")
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id=42)
        ]
        self.Endfield.bot.get_channel = mock.MagicMock(return_value=mock.AsyncMock())

        client = self.mock_EndfieldClient.return_value
        client.start = mock.AsyncMock()
        client.close = mock.AsyncMock()
        client.sign_in = mock.AsyncMock(return_value=False)
        client.get_attendance = mock.AsyncMock()

        await self.Endfield.claim_endfield_daily_reward.coro(self.Endfield)

        client.sign_in.assert_awaited()
        client.get_attendance.assert_not_called()

    async def test_check_sanity_survives_db_error(self) -> None:
        self.mock_UsagiGryphline.get_all_by_or.side_effect = Exception("db down")

        await self.Endfield.check_sanity_overflow.coro(self.Endfield)

        self.Endfield.bot.logger.exception.assert_called()

    async def test_check_sanity_survives_user_error(self) -> None:
        self.mock_UsagiGryphline.get_all_by_or.return_value = [
            mock.MagicMock(
                guild_id="g1",
                user_id="u1",
                token="t1",
                endfield_sanity_sub=True,
                endfield_sanity_sub_notified=False,
            ),
            mock.MagicMock(
                guild_id="g1",
                user_id="u2",
                token="t2",
                endfield_sanity_sub=True,
                endfield_sanity_sub_notified=False,
            ),
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id="ch")
        ]
        channel = mock.AsyncMock()
        self.Endfield.bot.get_channel = mock.MagicMock(return_value=channel)

        client_bad = mock.MagicMock()
        client_bad.start = mock.AsyncMock(side_effect=Exception("boom"))
        client_bad.close = mock.AsyncMock()

        client_good = mock.MagicMock()
        client_good.start = mock.AsyncMock()
        client_good.close = mock.AsyncMock()
        client_good.sign_in = mock.AsyncMock(return_value=True)
        profile = mock.MagicMock()
        profile.success = True
        profile.data.sanity.current = 400
        profile.data.nickname = "nick"
        client_good.get_profile = mock.AsyncMock(return_value=profile)

        self.mock_EndfieldClient.side_effect = [client_bad, client_good]

        await self.Endfield.check_sanity_overflow.coro(self.Endfield)

        channel.send.assert_awaited_once()
        self.Endfield.bot.logger.exception.assert_called()
        # config loaded once for the whole loop, not per user
        self.mock_UsagiConfig.get_all_by.assert_awaited_once_with(command_tag="endfield")
        self.mock_UsagiConfig.get.assert_not_called()

    @freeze_time("2026-06-13 16:00:00")
    async def test_claim_loop_survives_user_error(self) -> None:
        self.mock_UsagiGryphline.get_all_by_or.return_value = [
            mock.MagicMock(guild_id="g1", user_id="u1", token="t1"),
            mock.MagicMock(guild_id="g1", user_id="u2", token="t2"),
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id="ch")
        ]
        channel = mock.AsyncMock()
        self.Endfield.bot.get_channel = mock.MagicMock(return_value=channel)

        client_bad = mock.MagicMock()
        client_bad.start = mock.AsyncMock()
        client_bad.close = mock.AsyncMock()
        client_bad.sign_in = mock.AsyncMock(side_effect=Exception("boom"))

        client_good = mock.MagicMock()
        client_good.start = mock.AsyncMock()
        client_good.close = mock.AsyncMock()
        client_good.sign_in = mock.AsyncMock(return_value=True)
        client_good.get_attendance = mock.AsyncMock(
            return_value=mock.MagicMock(success=True)
        )

        self.mock_EndfieldClient.side_effect = [client_bad, client_good]

        await self.Endfield.claim_endfield_daily_reward.coro(self.Endfield)

        channel.send.assert_awaited()
        self.Endfield.bot.logger.exception.assert_called()

    async def test_endfield_settings_toggles_daily(self) -> None:
        account = mock.MagicMock(
            id=9, endfield_daily_sub=False, endfield_sanity_sub=True
        )
        self.mock_UsagiGryphline.get.return_value = account
        await self.Endfield.endfield_settings.callback(
            self.Endfield, self.ctx, option="Daily reward", uid=123
        )
        self.mock_UsagiGryphline.update.assert_awaited_once_with(
            id=9, endfield_daily_sub=True, endfield_sanity_sub=True
        )

    async def test_endfield_settings_toggles_notification(self) -> None:
        account = mock.MagicMock(
            id=9, endfield_daily_sub=True, endfield_sanity_sub=True
        )
        self.mock_UsagiGryphline.get.return_value = account
        await self.Endfield.endfield_settings.callback(
            self.Endfield, self.ctx, option="Notification", uid=123
        )
        self.mock_UsagiGryphline.update.assert_awaited_once_with(
            id=9, endfield_daily_sub=True, endfield_sanity_sub=False
        )

    async def test_endfield_delete_removes_account(self) -> None:
        self.mock_UsagiGryphline.get.return_value = mock.MagicMock(id=9)
        await self.Endfield.endfield_delete.callback(self.Endfield, self.ctx, uid=123)
        self.mock_UsagiGryphline.delete.assert_awaited_once_with(
            guild_id="g1", user_id="u1", uid=123
        )

    async def test_endfield_login_sends_button(self) -> None:
        await self.Endfield.endfield_login.callback(self.Endfield, self.ctx)
        self.ctx.respond.assert_awaited_once()
        self.assertIn("view", self.ctx.respond.await_args.kwargs)


class TestEndfieldProfileSettings(IsolatedAsyncioTestCase):
    @mock.patch(
        "usagiBot.src.UsagiNet.fetch_image",
        new_callable=mock.AsyncMock,
    )
    @mock.patch(
        "usagiBot.cogs.ArknightsEndfield.schemas.UsagiEndfieldProfile",
        new_callable=mock.AsyncMock,
    )
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine, mock_Profile, mock_fetch) -> None:
        from usagiBot.cogs.ArknightsEndfield.index import Endfield

        self.Endfield = Endfield
        self.mock_Profile = mock_Profile
        self.mock_fetch = mock_fetch

        self.Endfield.bot = mock.AsyncMock()
        self.Endfield.bot.i18n = init_i18n()
        self.Endfield.bot.language = {}

        self.ctx = mock.AsyncMock()
        self.ctx.guild.id = "g1"
        self.ctx.author.id = "u1"

    async def test_set_bg_creates_when_absent(self) -> None:
        self.mock_fetch.return_value = b"img"
        self.mock_Profile.get.return_value = None
        await self.Endfield.endfield_set_bg.callback(
            self.Endfield, self.ctx, url="http://x/a.png"
        )
        self.mock_Profile.create.assert_awaited_once_with(
            guild_id="g1", user_id="u1", background_url="http://x/a.png"
        )

    async def test_set_bg_updates_when_present(self) -> None:
        self.mock_fetch.return_value = b"img"
        self.mock_Profile.get.return_value = mock.MagicMock(id=3)
        await self.Endfield.endfield_set_bg.callback(
            self.Endfield, self.ctx, url="http://x/a.png"
        )
        self.mock_Profile.update.assert_awaited_once_with(
            id=3, background_url="http://x/a.png"
        )

    async def test_set_bg_rejects_unsafe_url(self) -> None:
        from usagiBot.src.UsagiNet import UnsafeUrlError

        self.mock_fetch.side_effect = UnsafeUrlError("nope")
        await self.Endfield.endfield_set_bg.callback(
            self.Endfield, self.ctx, url="http://127.0.0.1/a.png"
        )
        self.ctx.respond.assert_awaited()
        self.mock_Profile.create.assert_not_called()
        self.mock_Profile.update.assert_not_called()

    async def test_set_theme_rejects_invalid(self) -> None:
        await self.Endfield.endfield_set_theme.callback(
            self.Endfield, self.ctx, theme="Rainbow"
        )
        self.ctx.respond.assert_awaited()
        self.mock_Profile.create.assert_not_called()

    async def test_set_theme_creates_when_absent(self) -> None:
        self.mock_Profile.get.return_value = None
        await self.Endfield.endfield_set_theme.callback(
            self.Endfield, self.ctx, theme="Dark"
        )
        self.mock_Profile.create.assert_awaited_once_with(
            guild_id="g1", user_id="u1", theme="Dark"
        )

    async def test_set_color_updates_when_present(self) -> None:
        self.mock_Profile.get.return_value = mock.MagicMock(id=4)
        color = mock.MagicMock()
        color.to_rgb.return_value = (255, 0, 128)
        await self.Endfield.endfield_set_color.callback(
            self.Endfield, self.ctx, color
        )
        self.mock_Profile.update.assert_awaited_once_with(id=4, accent_color="#ff0080")


class TestEndfieldProfileRender(IsolatedAsyncioTestCase):
    @mock.patch(
        "usagiBot.src.UsagiNet.fetch_image", new_callable=mock.AsyncMock
    )
    @mock.patch("usagiBot.cogs.ArknightsEndfield.arknights_utils.draw_endfield_profile")
    @mock.patch("usagiBot.cogs.ArknightsEndfield.arknights_utils.EndfieldClient")
    @mock.patch(
        "usagiBot.cogs.ArknightsEndfield.schemas.UsagiEndfieldProfile",
        new_callable=mock.AsyncMock,
    )
    @mock.patch(
        "usagiBot.cogs.ArknightsEndfield.schemas.UsagiGryphline",
        new_callable=mock.AsyncMock,
    )
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(
        self,
        mock_engine,
        mock_Gryphline,
        mock_Profile,
        mock_Client,
        mock_draw,
        mock_fetch,
    ) -> None:
        from io import BytesIO
        from usagiBot.cogs.ArknightsEndfield.index import Endfield

        self.Endfield = Endfield
        self.mock_Gryphline = mock_Gryphline
        self.mock_Profile = mock_Profile
        self.mock_Client = mock_Client
        mock_draw.return_value = BytesIO(b"img")

        self.Endfield.bot = mock.AsyncMock()
        self.Endfield.bot.i18n = init_i18n()
        self.Endfield.bot.language = {}

        self.ctx = mock.AsyncMock()
        self.ctx.guild.id = "g1"
        self.ctx.author.id = "u1"

        client = mock_Client.return_value
        client.start = mock.AsyncMock()
        client.close = mock.AsyncMock()
        client.sign_in = mock.AsyncMock(return_value=True)
        profile = mock.MagicMock()
        profile.success = True
        profile.data.nickname = "Nick"
        profile.data.uid = 100
        profile.data.sanity.current = 120
        profile.data.sanity.max = 240
        profile.data.sanity.recover_ts = 0
        client.get_profile = mock.AsyncMock(return_value=profile)

    async def test_profile_renders_file(self) -> None:
        self.mock_Gryphline.get_all_by.return_value = [mock.MagicMock(token="t1")]
        self.mock_Profile.get.return_value = None

        await self.Endfield.endfield_profile.callback(self.Endfield, self.ctx)

        self.ctx.respond.assert_awaited()
        self.assertIn("file", self.ctx.respond.await_args.kwargs)

    async def test_sanity_renders_embed(self) -> None:
        self.mock_Gryphline.get_all_by.return_value = [mock.MagicMock(token="t1")]

        await self.Endfield.endfield_sanity.callback(self.Endfield, self.ctx)

        self.ctx.respond.assert_awaited()
        self.assertIn("embed", self.ctx.respond.await_args.kwargs)


class TestEndfieldSetup(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def test_setup_adds_cog(self, mock_engine) -> None:
        from usagiBot.cogs.ArknightsEndfield.index import setup

        bot = mock.MagicMock()
        bot.wait_until_ready = mock.AsyncMock()
        setup(bot)
        bot.add_cog.assert_called_once()
