from unittest import IsolatedAsyncioTestCase
from unittest import mock

import discord
from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *

FIELD_VALUE_LIMIT = 1024
FIELD_NAME_LIMIT = 256
DESCRIPTION_LIMIT = 4096


class TestSongEmbed(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music.sources import Song

        self.Song = Song

    def _make_song(self, **source_attrs) -> object:
        source = mock.MagicMock()
        source.requester.mention = "<@1>"
        source.title = "title"
        source.duration = "3:00"
        source.duration_raw = "3:00"
        source.uploader = "uploader"
        source.uploader_url = "https://youtube.com/@uploader"
        source.url = "https://youtube.com/watch?v=abc"
        source.thumbnail = "https://i.ytimg.com/x.jpg"
        for name, value in source_attrs.items():
            setattr(source, name, value)
        return self.Song(source)

    def test_oversized_metadata_stays_within_discord_limits(self) -> None:
        # Discord rejects the whole message with 50035 when any field is over
        # 1024 chars, which killed the player task and left the bot silent.
        song = self._make_song(
            title="t" * 5000,
            uploader="u" * 3000,
            uploader_url="https://youtube.com/" + "p" * 3000,
            url="https://youtube.com/watch?v=" + "q" * 3000,
        )

        embed = song.create_embed("play")

        self.assertLessEqual(len(embed.description), DESCRIPTION_LIMIT)
        for field in embed.fields:
            self.assertLessEqual(len(field.name), FIELD_NAME_LIMIT)
            self.assertLessEqual(len(field.value), FIELD_VALUE_LIMIT, field.name)

    def test_regular_metadata_is_unchanged(self) -> None:
        embed = self._make_song().create_embed("play")

        values = {field.name: field.value for field in embed.fields}
        self.assertEqual(values["Uploader"], "[uploader](https://youtube.com/@uploader)")
        self.assertEqual(values["URL"], "[Click](https://youtube.com/watch?v=abc)")


class TestNowPlayingMessage(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music.voice_state import VoiceState

        self.state = VoiceState.__new__(VoiceState)
        self.state.bot = mock.MagicMock()
        self.state.current = mock.MagicMock()

    async def test_send_failure_does_not_raise(self) -> None:
        self.state.current.source.channel.send = mock.AsyncMock(
            side_effect=discord.HTTPException(
                mock.MagicMock(status=400, reason="Bad Request"),
                {"code": 50035, "message": "Invalid Form Body"},
            )
        )

        with mock.patch("usagiBot.cogs.Music.voice_state.PlayerControlView"):
            message = await self.state._send_now_playing()

        self.assertIsNone(message)

    async def test_returns_sent_message(self) -> None:
        sent = mock.MagicMock()
        self.state.current.source.channel.send = mock.AsyncMock(return_value=sent)

        with mock.patch("usagiBot.cogs.Music.voice_state.PlayerControlView"):
            message = await self.state._send_now_playing()

        self.assertIs(message, sent)


class TestJoinDefersInteraction(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music.music_utils import join_voice_channel

        self.join_voice_channel = join_voice_channel

    def _make_ctx(self, order: list, already_done: bool = False) -> mock.MagicMock:
        ctx = mock.MagicMock()
        ctx.interaction.response.is_done.return_value = already_done
        ctx.defer = mock.AsyncMock(side_effect=lambda **kw: order.append("defer"))
        ctx.respond = mock.AsyncMock()
        ctx.me.edit = mock.AsyncMock()
        destination = ctx.author.voice.channel
        destination.permissions_for.return_value.connect = True
        destination.connect = mock.AsyncMock(
            side_effect=lambda: order.append("connect") or mock.MagicMock()
        )
        return ctx

    async def test_defers_before_the_slow_voice_connect(self) -> None:
        # Connecting with DAVE takes a few seconds; the 3s interaction window
        # would otherwise expire (10062 Unknown interaction) before we respond.
        order: list = []
        ctx = self._make_ctx(order)

        await self.join_voice_channel(ctx)

        self.assertEqual(order, ["defer", "connect"])
        self.assertTrue(ctx.defer.call_args.kwargs["ephemeral"])

    async def test_does_not_defer_twice(self) -> None:
        order: list = []
        ctx = self._make_ctx(order, already_done=True)

        await self.join_voice_channel(ctx)

        ctx.defer.assert_not_called()
        self.assertEqual(order, ["connect"])
