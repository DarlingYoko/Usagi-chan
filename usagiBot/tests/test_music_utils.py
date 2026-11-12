from unittest import IsolatedAsyncioTestCase, TestCase
from unittest import mock

from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *


class TestGetAudioDuration(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music.music_utils import get_audio_duration

        self.get_audio_duration = get_audio_duration

    def _make_proc(self, stdout: bytes = b"123.45\n", returncode: int = 0) -> mock.AsyncMock:
        proc = mock.AsyncMock()
        proc.communicate.return_value = (stdout, b"")
        proc.returncode = returncode
        return proc

    @mock.patch("asyncio.create_subprocess_exec", new_callable=mock.AsyncMock)
    async def test_link_is_passed_as_single_argv_element(self, mock_exec) -> None:
        mock_exec.return_value = self._make_proc()
        link = 'http://x/a"; echo pwned #'

        await self.get_audio_duration(link)

        args = mock_exec.call_args.args
        self.assertEqual(args[0], "ffprobe")
        self.assertIn(link, args)
        self.assertNotIn("shell", mock_exec.call_args.kwargs)

    @mock.patch("asyncio.create_subprocess_exec", new_callable=mock.AsyncMock)
    async def test_returns_duration_in_whole_seconds(self, mock_exec) -> None:
        mock_exec.return_value = self._make_proc(stdout=b"245.78\n")

        result = await self.get_audio_duration("http://example.com/song.mp3")

        self.assertEqual(result, 245)

    @mock.patch("asyncio.create_subprocess_exec", new_callable=mock.AsyncMock)
    async def test_raises_on_ffprobe_failure(self, mock_exec) -> None:
        mock_exec.return_value = self._make_proc(stdout=b"", returncode=1)

        with self.assertRaises(RuntimeError):
            await self.get_audio_duration("http://example.com/song.mp3")


class TestDurations(TestCase):
    def setUp(self) -> None:
        from usagiBot.cogs.Music.music_utils import parse_duration, parse_duration_raw

        self.parse_duration = parse_duration
        self.parse_duration_raw = parse_duration_raw

    def test_human_duration(self) -> None:
        self.assertEqual(self.parse_duration(0), "")
        self.assertEqual(self.parse_duration(61), "1 minutes 1 seconds")
        self.assertEqual(self.parse_duration(90061), "1 days 1 hours 1 minutes 1 seconds")

    def test_clock_duration(self) -> None:
        self.assertEqual(self.parse_duration_raw(5), "0:05")
        self.assertEqual(self.parse_duration_raw(605), "10:05")
        self.assertEqual(self.parse_duration_raw(3605), "1:00:05")
        self.assertEqual(self.parse_duration_raw(90000), "1:01:00:00")


class TestQueueEmbed(TestCase):
    def setUp(self) -> None:
        from usagiBot.cogs.Music.music_utils import queue_embed

        self.queue_embed = queue_embed

    def songs(self, count: int) -> list:
        return [
            {"url": f"https://youtu.be/{n}", "title": f"t{n}", "duration": 60}
            for n in range(count)
        ]

    def test_empty_queue_is_one_page(self) -> None:
        embed = self.queue_embed([], 1, "Header", "Desc", "url")

        self.assertEqual(embed.fields[0].value, "No songs in queue...")
        self.assertEqual(embed.footer.text, "Viewing page 1/1")

    def test_page_past_the_end_clamps(self) -> None:
        embed = self.queue_embed(self.songs(6), 9, "Header", "Desc", "url")

        self.assertEqual(embed.footer.text, "Viewing page 2/2")
        self.assertEqual(embed.fields[0].value, "`6.` [**t5**](https://youtu.be/5) (1:00)\n")
        self.assertEqual(embed.fields[0].name, "**6 tracks** - 6 minutes")

    def test_local_files_and_ids(self) -> None:
        local = [{"id": "local@/a_b.mp3", "title": "a_b", "duration": 61}]

        embed = self.queue_embed(local, 1, "Header", "Desc", "id")

        self.assertEqual(embed.fields[0].value, "`1.` **a\\_b** (1 minutes 1 seconds)\n")


class TestVoiceChecks(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music import music_utils
        from usagiBot.tests.music_helpers import make_ctx

        self.music_utils = music_utils
        self.ctx = make_ctx()

    async def test_user_in_bot_channel(self) -> None:
        self.assertTrue(await self.music_utils.check_user_in_voice(self.ctx))
        self.ctx.respond.assert_not_called()

    async def test_user_not_in_voice(self) -> None:
        self.ctx.author.voice = None

        self.assertFalse(await self.music_utils.check_user_in_voice(self.ctx))
        self.ctx.respond.assert_awaited_once()

    async def test_user_in_other_channel(self) -> None:
        self.ctx.author.voice.channel = mock.MagicMock()

        self.assertFalse(await self.music_utils.check_user_in_voice(self.ctx))

    async def test_any_channel_when_bot_not_connected(self) -> None:
        self.ctx.voice_state.voice = None
        self.ctx.author.voice.channel = mock.MagicMock()

        self.assertTrue(await self.music_utils.check_user_in_voice(self.ctx))

    @mock.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    async def test_unmute_self(self, _sleep) -> None:
        await self.music_utils.unmute_self(self.ctx)

        self.ctx.me.edit.assert_awaited_with(suppress=False)
        self.ctx.respond.assert_not_called()

    async def test_generate_source_keeps_title_for_direct_links(self) -> None:
        holder = mock.MagicMock()
        holder.create_song_source = mock.AsyncMock()

        await self.music_utils.generate_source(holder, "youtu.be", "u", "t", "me")
        self.assertNotIn("title", holder.create_song_source.call_args.kwargs)

        await self.music_utils.generate_source(holder, "cdn.example.com", "u", "t", "me")
        self.assertEqual(holder.create_song_source.call_args.kwargs["title"], "t")
