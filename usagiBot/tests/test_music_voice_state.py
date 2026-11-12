import asyncio
from unittest import IsolatedAsyncioTestCase
from unittest import mock

import discord
from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *
from usagiBot.tests.music_helpers import YOUTUBE_URL, make_bot, make_ctx, make_current

VS = "usagiBot.cogs.Music.voice_state"


def audio_source() -> mock.MagicMock:
    source = mock.MagicMock(spec=discord.AudioSource)
    source.is_opus.return_value = False
    return source


class TimeoutAfter:
    """async_timeout stand-in: lets `allowed` blocks run, then times out."""

    def __init__(self, allowed: int) -> None:
        self.allowed = allowed

    def __call__(self, _seconds):
        return self

    async def __aenter__(self):
        if self.allowed == 0:
            raise asyncio.TimeoutError
        self.allowed -= 1

    async def __aexit__(self, *exc):
        return False


class VoiceStateTestCase(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music import voice_state

        self.module = voice_state
        self.bot = make_bot()
        self.ctx = make_ctx()
        self.cog = mock.MagicMock()
        self.cog.voice_states = {}
        self.state = voice_state.VoiceState(self.bot, self.ctx, self.cog)
        self.cog.voice_states[self.ctx.guild.id] = self.state
        self.voice = mock.MagicMock()
        self.voice.disconnect = mock.AsyncMock()
        self.state.voice = self.voice


class TestBasics(VoiceStateTestCase):
    def test_initial_state(self) -> None:
        self.assertIsNone(self.state.current)
        self.assertFalse(self.state.loop)
        self.assertEqual(self.state.volume, 0.5)
        self.assertEqual(self.state.guild_id, self.ctx.guild.id)
        self.bot.loop.create_task.assert_called_once()

    def test_is_playing_needs_voice_and_song(self) -> None:
        self.assertFalse(self.state.is_playing)
        self.state.current = make_current()
        self.assertTrue(self.state.is_playing)

    def test_loop_property(self) -> None:
        self.state.loop = True
        self.assertTrue(self.state._loop)

    def test_volume_ignored_while_between_songs(self) -> None:
        self.state.current = {"url": "x"}

        self.state.volume = 0.9

        self.assertEqual(self.state.volume, 0.9)

    def test_recreate_resets_player(self) -> None:
        self.state.current = make_current()

        self.state.recreate_bg_task(self.ctx, self.cog)

        self.assertIsNone(self.state.current)
        self.assertEqual(self.bot.loop.create_task.call_count, 2)

    def test_skip_stops_voice(self) -> None:
        self.state.current = make_current()

        self.state.skip()

        self.assertTrue(self.state.skipped)
        self.voice.stop.assert_called_once()

    def test_skip_when_idle(self) -> None:
        self.state.skip()

        self.assertTrue(self.state.skipped)
        self.voice.stop.assert_not_called()


class TestStop(VoiceStateTestCase):
    async def test_stop_keeps_connection(self) -> None:
        self.state.current = make_current()
        await self.state.songs.put({"title": "next"})

        await self.state.stop()

        self.assertIsNone(self.state.current)
        self.assertEqual(len(self.state.songs), 0)
        self.voice.stop.assert_called_once()
        self.voice.disconnect.assert_not_called()
        self.state.audio_player.cancel.assert_not_called()

    async def test_stop_and_leave(self) -> None:
        timer = mock.MagicMock()
        timer.done.return_value = False
        self.state.alone_timer = timer

        await self.state.stop(leave=True)

        self.voice.disconnect.assert_awaited_once()
        self.assertIsNone(self.state.voice)
        timer.cancel.assert_called_once()
        self.state.audio_player.cancel.assert_called_once()

    async def test_leave_survives_disconnect_error(self) -> None:
        self.voice.disconnect.side_effect = RuntimeError("gone")

        await self.state.stop(leave=True)

        self.assertIsNone(self.state.voice)


class TestAloneTimer(VoiceStateTestCase):
    def test_start_once(self) -> None:
        self.state.start_alone_timer()
        self.state.start_alone_timer()

        # one call for the player task, one for the timer
        self.assertEqual(self.bot.loop.create_task.call_count, 2)

    def test_cancel(self) -> None:
        self.state.start_alone_timer()
        timer = self.state.alone_timer

        self.state.cancel_alone_timer()

        timer.cancel.assert_called_once()
        self.assertIsNone(self.state.alone_timer)

    @mock.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    async def test_leaves_when_still_alone(self, mock_sleep) -> None:
        self.voice.channel.members = [mock.MagicMock()]

        await self.state._leave_when_alone()

        mock_sleep.assert_awaited_with(self.module.ALONE_TIMEOUT)
        self.voice.disconnect.assert_awaited_once()
        self.assertNotIn(self.ctx.guild.id, self.cog.voice_states)

    @mock.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    async def test_stays_when_someone_came_back(self, _sleep) -> None:
        self.voice.channel.members = [mock.MagicMock(), mock.MagicMock()]

        await self.state._leave_when_alone()

        self.voice.disconnect.assert_not_called()
        self.assertIn(self.ctx.guild.id, self.cog.voice_states)


class TestPlayNextSong(VoiceStateTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.state.current = make_current()
        self.state.start_time = 1000.0

    @mock.patch("time.time", return_value=1000.5)
    def test_instant_end_marks_forbidden(self, _time) -> None:
        self.state.play_next_song()

        self.assertTrue(self.state.forbidden)
        self.assertTrue(self.state.next.is_set())
        self.assertIsNotNone(self.state.current)

    @mock.patch("time.time", return_value=1200.0)
    def test_song_finished(self, _time) -> None:
        self.state.play_next_song(error=RuntimeError("ffmpeg"))

        self.assertFalse(self.state.forbidden)
        self.assertIsNone(self.state.current)
        self.assertTrue(self.state.next.is_set())

    @mock.patch("time.time", return_value=1200.0)
    def test_looping_keeps_song(self, _time) -> None:
        self.state.loop = True

        self.state.play_next_song()

        self.assertIsNotNone(self.state.current)
        self.assertTrue(self.state.next.is_set())

    @mock.patch("time.time", return_value=1200.0)
    def test_seek_restart_does_not_advance(self, _time) -> None:
        self.state.seeking = True

        self.state.play_next_song()

        self.assertFalse(self.state.seeking)
        self.assertFalse(self.state.next.is_set())
        self.assertIsNotNone(self.state.current)


class TestCreateSongSource(VoiceStateTestCase):
    @mock.patch(f"{VS}.get_audio_duration", new_callable=mock.AsyncMock, return_value=90)
    @mock.patch("discord.FFmpegPCMAudio")
    async def test_local_file(self, mock_ffmpeg, _duration) -> None:
        mock_ffmpeg.return_value = audio_source()

        song = await self.state.create_song_source(
            self.ctx, "local@/tmp/a.mp3", title="a", requester="me"
        )

        mock_ffmpeg.assert_called_with("/tmp/a.mp3")
        self.assertTrue(song.is_file)
        self.assertEqual(song.source.url, "local@/tmp/a.mp3")
        self.assertEqual(song.source.duration_int, 90)

    @mock.patch(f"{VS}.get_audio_duration", new_callable=mock.AsyncMock, return_value=90)
    @mock.patch("discord.FFmpegPCMAudio")
    async def test_local_file_with_seek(self, mock_ffmpeg, _duration) -> None:
        mock_ffmpeg.return_value = audio_source()

        await self.state.create_song_source(self.ctx, "local@/tmp/a.mp3", seek=75)

        self.assertEqual(mock_ffmpeg.call_args.kwargs["before_options"], "-ss 1:15")

    @mock.patch(f"{VS}.get_audio_duration", new_callable=mock.AsyncMock)
    async def test_local_file_ffprobe_failure(self, mock_duration) -> None:
        mock_duration.side_effect = RuntimeError("ffprobe")

        result = await self.state.create_song_source(self.ctx, "local@/tmp/a.mp3")

        self.assertEqual(result, "error")

    async def test_remote_source(self) -> None:
        source = mock.MagicMock()
        with mock.patch.object(
            self.module.FFMPEGSource, "create_source", new=mock.AsyncMock(return_value=source)
        ) as create:
            song = await self.state.create_song_source(
                self.ctx, YOUTUBE_URL, requester="me", seek=10
            )

        self.assertIs(song.source, source)
        self.assertTrue(song.is_direct_link)
        self.assertEqual(create.call_args.kwargs["seek"], 10)

    async def test_remote_failure_is_reported(self) -> None:
        self.ctx.channel.send = mock.AsyncMock()
        with mock.patch.object(
            self.module.FFMPEGSource,
            "create_source",
            new=mock.AsyncMock(side_effect=RuntimeError("403")),
        ):
            result = await self.state.create_song_source(self.ctx, YOUTUBE_URL)

        self.assertEqual(result, "error")
        self.ctx.channel.send.assert_awaited_with("Error: 403")


class TestSeek(VoiceStateTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.state.current = make_current(url="https://cdn.example.com/a.mp3")
        self.state.seek_time = 30
        self.new_song = make_current()
        self.state.create_song_source = mock.AsyncMock(return_value=self.new_song)

    @mock.patch("time.time", return_value=2000.0)
    async def test_direct_link_keeps_title(self, _time) -> None:
        await self.state.seek(30, False, True)

        self.voice.stop.assert_called_once()
        self.assertEqual(self.state.create_song_source.call_args.kwargs["title"], "song")
        self.assertEqual(self.state.create_song_source.call_args.kwargs["seek"], 30)
        self.voice.play.assert_called_with(
            self.new_song.source, after=self.state.play_next_song
        )
        self.assertIs(self.state.current, self.new_song)
        self.assertEqual(self.new_song.start_time, 1970.0)
        self.assertEqual(self.new_song.source.volume, 0.5)

    async def test_youtube_refetches_title(self) -> None:
        await self.state.seek(30, False, False)

        self.assertNotIn("title", self.state.create_song_source.call_args.kwargs)


class TestNowPlayingLoop(VoiceStateTestCase):
    """One or two turns of audio_player_task; the next queue wait times out."""

    def setUp(self) -> None:
        super().setUp()
        self.played = []
        self.message = mock.MagicMock()
        self.message.delete = mock.AsyncMock()
        self.state._send_now_playing = mock.AsyncMock(return_value=self.message)
        self.voice.play.side_effect = self.finish_song

    def finish_song(self, source, after=None) -> None:
        self.played.append(source)
        self.state.next.set()

    async def run_player(self, allowed_waits: int, generated) -> None:
        with mock.patch(f"{VS}.timeout", TimeoutAfter(allowed_waits)), mock.patch(
            f"{VS}.generate_source", new=mock.AsyncMock(side_effect=generated)
        ) as self.generate, mock.patch("asyncio.sleep", new=mock.AsyncMock()):
            await self.state.audio_player_task()

    async def test_plays_queued_song_then_leaves_when_idle(self) -> None:
        song = make_current(title="queued")
        await self.state.songs.put(
            {"url": YOUTUBE_URL, "title": "queued", "user": "me", "duration": 1}
        )

        await self.run_player(1, [song])

        self.assertEqual(self.generate.call_args.args[2:], (YOUTUBE_URL, "queued", "me"))
        self.assertEqual(self.played, [song.source])
        self.message.delete.assert_awaited_once()
        self.voice.disconnect.assert_awaited_once()

    async def test_loop_queue_puts_song_back(self) -> None:
        song = make_current(title="again")
        self.state.loop_queue = True
        await self.state.songs.put(
            {"url": YOUTUBE_URL, "title": "again", "user": "me", "duration": 1}
        )

        # keep the queue intact when the idle timeout ends the player
        self.state.stop = mock.AsyncMock()

        await self.run_player(1, [song])

        self.assertEqual(self.state.songs[0]["title"], "again")

    async def test_unplayable_song_is_skipped(self) -> None:
        await self.state.songs.put(
            {"url": YOUTUBE_URL, "title": "broken", "user": "me", "duration": 1}
        )

        await self.run_player(1, ["error"])

        self.assertEqual(self.played, [])
        self.voice.disconnect.assert_awaited_once()

    async def test_looping_replays_current_song(self) -> None:
        first, replay = make_current(title="loop"), make_current(title="loop")
        await self.state.songs.put(
            {"url": YOUTUBE_URL, "title": "loop", "user": "me", "duration": 1}
        )

        def finish_and_enable_loop(source, after=None) -> None:
            self.finish_song(source)
            # first pass turns looping on, the replay turns it off again
            self.state.loop = len(self.played) == 1
            self.state.current = first

        self.voice.play.side_effect = finish_and_enable_loop

        await self.run_player(1, [first, replay])

        self.assertEqual(self.played, [first.source, replay.source])
        self.assertEqual(self.generate.call_args.args[2], first.source.url)

    async def test_skip_while_looping_takes_next_song(self) -> None:
        self.state.loop = True
        self.state.skipped = True
        nxt = make_current(title="next")
        await self.state.songs.put(
            {"url": YOUTUBE_URL, "title": "next", "user": "me", "duration": 1}
        )

        def finish_and_unloop(source, after=None) -> None:
            self.finish_song(source)
            self.state.loop = False

        self.voice.play.side_effect = finish_and_unloop

        await self.run_player(1, [nxt])

        self.assertEqual(self.played, [nxt.source])
        self.assertFalse(self.state.skipped)

    async def test_forbidden_stream_is_retried_without_new_message(self) -> None:
        retry = make_current(title="retry")
        self.state.forbidden = True
        self.state.current = make_current(title="blocked")

        await self.run_player(0, [retry])

        self.assertEqual(self.played, [retry.source])
        self.state._send_now_playing.assert_not_called()
        self.message.delete.assert_not_called()
