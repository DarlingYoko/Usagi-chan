import sys
import pytest

from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase
from twitchAPI import helper
from datetime import datetime
from freezegun import freeze_time
from usagiBot.tests.utils import *


@pytest.fixture(autouse=True)
def clear_imports():
    # Store the initial state of sys.modules
    initial_modules = dict(sys.modules)
    from usagiBot.db.base import Base
    Base.metadata.clear()
    # Yield control to the test
    yield

    # Clear any new modules imported during the test
    for module in list(sys.modules.keys()):
        if module not in initial_modules:
            del sys.modules[module]


class TestTwitch(IsolatedAsyncioTestCase):
    @mock.patch("usagiBot.cogs.Twitch.schemas.UsagiTwitchNotify", new_callable=mock.AsyncMock)
    @mock.patch("usagiBot.cogs.Main.schemas.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    @mock.patch.object(helper, "first", new_callable=mock.AsyncMock)
    def setUp(
        self, mock_first, mock_engine, mock_UsagiConfig, mock_UsagiTwitchNotify
    ) -> None:
        from usagiBot.cogs.Twitch.index import Twitch

        self.Twitch = Twitch

        self.mock_UsagiTwitchNotify = mock_UsagiTwitchNotify
        self.mock_UsagiConfig = mock_UsagiConfig
        self.mock_first = mock_first

        self.ctx = mock.AsyncMock()
        self.ctx.interaction.guild.id = "test_guild_id"
        self.ctx.interaction.user.id = "test_user_id"
        self.ctx.author.id = "test_user_id"
        self.ctx.guild.id = "test_guild_id"

        self.Twitch.twitch = mock.AsyncMock()
        self.Twitch.twitch.get_users = mock.MagicMock()
        self.Twitch.bot = mock.AsyncMock()
        self.Twitch.bot.logger = mock.MagicMock()
        self.Twitch.bot.i18n = init_i18n()
        self.Twitch.bot.language = {}

        # IMPORTANT: override get_channel + fetch_channel
        self.channels = {}

        def mock_get_channel(cid):
            return self.channels.get(cid)

        async def mock_fetch_channel(cid):
            return self.channels.get(cid)

        self.Twitch.bot.get_channel = mock.MagicMock(side_effect=mock_get_channel)
        self.Twitch.bot.fetch_channel = mock.AsyncMock(side_effect=mock_fetch_channel)

    @mock.patch(
        "usagiBot.cogs.Twitch.index.get_streamer_icon", new_callable=mock.AsyncMock
    )
    @mock.patch("usagiBot.cogs.Twitch.index.get_notify_src", new_callable=mock.AsyncMock)
    async def test_twitch_notify_loop(
        self, mock_get_notify_src, mock_get_streamer_icon
    ) -> None:
        mock_get_streamer_icon.return_value = "http://icon"
        mock_get_notify_src.return_value = (mock.MagicMock(), mock.MagicMock())
        self.mock_UsagiTwitchNotify.get_all.return_value = [
            mock.MagicMock(
                guild_id="test_guild_id_1",
                user_id="test_user_id_1",
                twitch_username="test_twitch_username_1",
                started_at=datetime(year=2023, month=2, day=12, hour=13),
            ),
            mock.MagicMock(
                guild_id="test_guild_id_1",
                user_id="test_user_id_1",
                twitch_username="test_twitch_username_2",
                started_at=datetime(year=2023, month=2, day=12, hour=13),
            ),
            mock.MagicMock(
                guild_id="test_guild_id_1",
                user_id="test_user_id_2",
                twitch_username="test_twitch_username_3",
                started_at=datetime(year=2023, month=2, day=12, hour=13),
            ),
            mock.MagicMock(
                guild_id="test_guild_id_1",
                user_id="test_user_id_2",
                twitch_username="test_twitch_username_2",
                started_at=datetime(year=2023, month=2, day=12, hour=1),
            ),
        ]

        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(
                guild_id="test_guild_id_1",
                generic_id="test_generic_id_channel_to_notify",
            )
        ]
        # Only streamer 1 is live, with a started_at newer than the stored one.
        live = mock.MagicMock(
            user_login="test_twitch_username_1",
            started_at=datetime(year=2024, month=1, day=1),
        )
        self.captured_logins = []

        async def fake_get_streams(user_login=None):
            self.captured_logins.append(set(user_login))
            for s in [live]:
                if s.user_login in user_login:
                    yield s

        self.Twitch.twitch.get_streams = fake_get_streams

        notify_channel = mock.AsyncMock(channel_id="test_generic_id_channel_to_notify")
        self.channels["test_generic_id_channel_to_notify"] = notify_channel

        await self.Twitch.twitch_notify_loop.coro(self.Twitch)
        self.mock_UsagiTwitchNotify.get_all.assert_called_with()
        self.mock_UsagiConfig.get_all_by.assert_called_with(command_tag="twitch_notify")
        self.mock_UsagiConfig.get.assert_not_called()
        # one batched call resolving every followed streamer
        self.assertEqual(len(self.captured_logins), 1)
        self.assertEqual(
            self.captured_logins[0],
            {
                "test_twitch_username_1",
                "test_twitch_username_2",
                "test_twitch_username_3",
            },
        )
        self.Twitch.bot.get_channel.assert_called_with(
            "test_generic_id_channel_to_notify"
        )

        self.assertEqual(notify_channel.send.call_count, 1)

    async def test_twitch_loop_survives_db_error(self) -> None:
        self.mock_UsagiTwitchNotify.get_all.side_effect = Exception("db down")

        await self.Twitch.twitch_notify_loop.coro(self.Twitch)

        self.Twitch.bot.logger.exception.assert_called()

    async def test_twitch_loop_survives_auth_failure(self) -> None:
        self.Twitch.twitch = None
        with mock.patch(
            "usagiBot.cogs.Twitch.index.twitch_auth", new_callable=mock.AsyncMock
        ) as mock_auth:
            mock_auth.side_effect = Exception("auth down")
            await self.Twitch.twitch_notify_loop.coro(self.Twitch)

        self.Twitch.bot.logger.exception.assert_called()

    @mock.patch("usagiBot.cogs.Twitch.index.get_notify_src", new_callable=mock.AsyncMock)
    @mock.patch(
        "usagiBot.cogs.Twitch.index.get_streamer_icon", new_callable=mock.AsyncMock
    )
    async def test_twitch_loop_survives_streamer_error(
        self, mock_get_streamer_icon, mock_get_notify_src
    ) -> None:
        mock_get_streamer_icon.return_value = "http://icon"
        # first streamer blows up rendering, second still gets notified
        mock_get_notify_src.side_effect = [
            Exception("boom"),
            (mock.MagicMock(), mock.MagicMock()),
        ]
        self.mock_UsagiTwitchNotify.get_all.return_value = [
            mock.MagicMock(
                guild_id="g1",
                user_id="u1",
                twitch_username="s1",
                started_at=datetime(2023, 1, 1),
            ),
            mock.MagicMock(
                guild_id="g1",
                user_id="u2",
                twitch_username="s2",
                started_at=datetime(2023, 1, 1),
            ),
        ]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id="ch")
        ]
        s1 = mock.MagicMock(user_login="s1", started_at=datetime(2024, 1, 1))
        s2 = mock.MagicMock(user_login="s2", started_at=datetime(2024, 1, 1))

        async def fake_get_streams(user_login=None):
            for s in [s1, s2]:
                if s.user_login in user_login:
                    yield s

        self.Twitch.twitch.get_streams = fake_get_streams
        channel = mock.AsyncMock()
        self.channels["ch"] = channel

        await self.Twitch.twitch_notify_loop.coro(self.Twitch)

        self.assertEqual(channel.send.call_count, 1)
        self.Twitch.bot.logger.exception.assert_called()

    @freeze_time("2001-03-21")
    async def test_follow_streamer(self) -> None:
        self.mock_first.return_value = mock.MagicMock(user_name="yoko_0")
        self.mock_UsagiTwitchNotify.get.return_value = None
        self.Twitch.twitch.get_users = mock.MagicMock()
        await self.Twitch.follow_streamer.callback(self.Twitch, self.ctx, "yoko_0")
        self.Twitch.twitch.get_users.assert_called_with(logins=["yoko_0"])
        self.mock_UsagiTwitchNotify.get.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_user_id",
            twitch_username="yoko_0",
        )
        self.mock_UsagiTwitchNotify.create.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_user_id",
            twitch_username="yoko_0",
            started_at=datetime(year=2001, month=3, day=21),
        )
        self.ctx.respond.assert_called_with(
            "Followed you to **yoko_0**", ephemeral=True
        )

    async def test_follow_streamer_fake_streamer(self) -> None:
        self.Twitch.twitch.get_users = mock.MagicMock()
        self.mock_first.return_value = None
        await self.Twitch.follow_streamer.callback(self.Twitch, self.ctx, "asdasdasd")
        self.ctx.respond.assert_called_with(
            "There isn't streamer with that nickname!", ephemeral=True
        )

    async def test_follow_streamer_already_followed(self) -> None:
        self.mock_UsagiTwitchNotify.get.return_value = mock.MagicMock()
        await self.Twitch.follow_streamer.callback(
            self.Twitch, self.ctx, "uselessmouth"
        )
        self.Twitch.twitch.get_users.assert_called_with(logins=["uselessmouth"])
        self.mock_UsagiTwitchNotify.get.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_user_id",
            twitch_username="uselessmouth",
        )
        self.ctx.respond.assert_called_with(
            "You are already followed to this streamer!", ephemeral=True
        )

    async def test_unfollow_streamer(self) -> None:
        self.mock_UsagiTwitchNotify.get.return_value = mock.MagicMock()
        await self.Twitch.unfollow_streamer.callback(
            self.Twitch, self.ctx, "streamer_1"
        )
        self.mock_UsagiTwitchNotify.get.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_user_id",
            twitch_username="streamer_1",
        )
        self.mock_UsagiTwitchNotify.delete.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_user_id",
            twitch_username="streamer_1",
        )
        self.ctx.respond.assert_called_with(
            "Unfollowed you from **streamer_1**", ephemeral=True
        )

    async def test_unfollow_streamer_not_followed(self) -> None:
        self.mock_UsagiTwitchNotify.get.return_value = None
        await self.Twitch.unfollow_streamer.callback(
            self.Twitch, self.ctx, "streamer_2"
        )
        self.mock_UsagiTwitchNotify.get.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_user_id",
            twitch_username="streamer_2",
        )
        self.ctx.respond.assert_called_with(
            "You are not followed to this streamer.", ephemeral=True
        )

    async def test_show_user_follows(self) -> None:
        self.mock_UsagiTwitchNotify.get_all_by.return_value = [
            mock.MagicMock(twitch_username="streamer_1"),
            mock.MagicMock(twitch_username="streamer_2"),
            mock.MagicMock(twitch_username="streamer_3"),
        ]
        await self.Twitch.show_user_follows.callback(self.Twitch, self.ctx)
        self.mock_UsagiTwitchNotify.get_all_by.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_user_id",
        )
        response = (
            "Your followed streamers:\n - streamer_1\n - streamer_2\n - streamer_3\n"
        )
        self.ctx.respond.assert_called_with(response, ephemeral=True)

    async def test_show_user_follows_no_streamers(self) -> None:
        self.mock_UsagiTwitchNotify.get_all_by.return_value = None
        await self.Twitch.show_user_follows.callback(self.Twitch, self.ctx)
        self.mock_UsagiTwitchNotify.get_all_by.assert_called_with(
            guild_id="test_guild_id",
            user_id="test_user_id",
        )
        self.ctx.respond.assert_called_with(
            "You are not followed to any streamer.", ephemeral=True
        )

    async def test_show_all_follows(self) -> None:
        self.mock_UsagiTwitchNotify.get_all_by.return_value = [
            mock.MagicMock(twitch_username="streamer_2"),
            mock.MagicMock(twitch_username="streamer_1"),
            mock.MagicMock(twitch_username="streamer_2"),
            mock.MagicMock(twitch_username="streamer_3"),
        ]
        await self.Twitch.show_all_follows.callback(self.Twitch, self.ctx)
        self.mock_UsagiTwitchNotify.get_all_by.assert_called_with(
            guild_id="test_guild_id",
        )

    async def test_show_all_follows_no(self) -> None:
        self.mock_UsagiTwitchNotify.get_all_by.return_value = None
        await self.Twitch.show_all_follows.callback(self.Twitch, self.ctx)
        self.mock_UsagiTwitchNotify.get_all_by.assert_called_with(
            guild_id="test_guild_id",
        )
        self.ctx.respond.assert_called_with(
            "Your guild not followed to any streamer.", ephemeral=True
        )

    async def test_show_all_follows_empty_list(self) -> None:
        self.mock_UsagiTwitchNotify.get_all_by.return_value = []
        await self.Twitch.show_all_follows.callback(self.Twitch, self.ctx)
        self.ctx.respond.assert_called_with(
            "Your guild not followed to any streamer.", ephemeral=True
        )

    async def test_show_user_follows_empty_list(self) -> None:
        self.mock_UsagiTwitchNotify.get_all_by.return_value = []
        await self.Twitch.show_user_follows.callback(self.Twitch, self.ctx)
        self.ctx.respond.assert_called_with(
            "You are not followed to any streamer.", ephemeral=True
        )


class TestTwitchAuth(IsolatedAsyncioTestCase):
    async def test_twitch_auth_falls_back_to_app_auth_on_dead_refresh_token(self) -> None:
        from twitchAPI.type import InvalidRefreshTokenException

        await self._assert_falls_back(InvalidRefreshTokenException("Invalid refresh token"))

    async def test_twitch_auth_falls_back_when_token_reports_no_scopes(self) -> None:
        # twitchAPI raises TypeError ("NoneType is not iterable") when the
        # token validates but carries no scopes.
        await self._assert_falls_back(TypeError("argument of type 'NoneType' is not iterable"))

    async def _assert_falls_back(self, error: Exception) -> None:
        from usagiBot.cogs.Twitch import twitch_utils

        user_client = mock.MagicMock()
        user_client.set_user_authentication = mock.AsyncMock(side_effect=error)

        class AppClient(mock.MagicMock):
            def __await__(self):
                async def _ready():
                    return self

                return _ready().__await__()

        app_client = AppClient()
        with mock.patch.object(
            twitch_utils, "Twitch", side_effect=[user_client, app_client]
        ):
            result = await twitch_utils.twitch_auth()

        self.assertIs(result, app_client)

