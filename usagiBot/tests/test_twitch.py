from sqlalchemy.ext import asyncio
from unittest import mock
from unittest import IsolatedAsyncioTestCase
from twitchAPI import helper
from datetime import datetime
from freezegun import freeze_time


class TestTwitch(IsolatedAsyncioTestCase):
    @classmethod
    @mock.patch("usagiBot.db.models.UsagiTwitchNotify", new_callable=mock.AsyncMock)
    @mock.patch("usagiBot.db.models.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch.object(asyncio, "create_async_engine")
    @mock.patch.object(helper, "first", new_callable=mock.AsyncMock)
    def setUpClass(
        cls, mock_first, mock_engine, mock_UsagiConfig, mock_UsagiTwitchNotify
    ) -> None:
        from usagiBot.cogs.Twitch.index import Twitch

        cls.Twitch = Twitch

        cls.mock_UsagiTwitchNotify = mock_UsagiTwitchNotify
        cls.mock_UsagiConfig = mock_UsagiConfig
        cls.mock_first = mock_first

        cls.ctx = mock.AsyncMock()
        cls.ctx.interaction.guild.id = "test_guild_id"
        cls.ctx.interaction.user.id = "test_user_id"
        cls.ctx.author.id = "test_user_id"
        cls.ctx.guild.id = "test_guild_id"

        cls.Twitch.twitch = mock.AsyncMock()
        cls.Twitch.bot = mock.AsyncMock()

    async def test_twitch_notify_loop(self) -> None:
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

        self.Twitch.twitch.get_streams = mock.MagicMock()
        self.mock_UsagiConfig.get.return_value = mock.MagicMock(
            generic_id="test_generic_id_channel_to_notify"
        )
        stream = mock.MagicMock(
            user_name="test_twitch_username_1",
            title="test_title_1",
            game_name="test_game_name_1",
        )
        self.mock_first.side_effect = [
            stream,
            None,
            None,
            None,
        ]

        notify_channel = mock.AsyncMock()
        self.Twitch.bot.fetch_channel = mock.AsyncMock(return_value=notify_channel)
        await self.Twitch.twitch_notify_loop(self.Twitch)
        self.mock_UsagiTwitchNotify.get_all.assert_called_with()
        self.mock_UsagiConfig.get.assert_called_with(
            guild_id="test_guild_id_1", command_tag="twitch_notify"
        )
        self.Twitch.bot.fetch_channel.assert_called_with(
            "test_generic_id_channel_to_notify"
        )

        self.assertEqual(notify_channel.send.call_count, 1)

    @freeze_time("2023-01-14")
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
            started_at=datetime(year=2023, month=1, day=14),
        )
        self.ctx.respond.assert_called_with(
            f"Followed you to **yoko_0**", ephemeral=True
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
            f"You are already followed to this streamer!", ephemeral=True
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
            f"Unfollowed you from **streamer_1**", ephemeral=True
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
            f"You are not followed to this streamer", ephemeral=True
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
            "You are not followed to any streamer", ephemeral=True
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
            "Your guild not followed to any streamer", ephemeral=True
        )
