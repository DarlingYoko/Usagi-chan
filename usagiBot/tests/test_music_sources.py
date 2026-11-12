from unittest import IsolatedAsyncioTestCase
from unittest import mock

import discord
from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *
from usagiBot.tests.music_helpers import YOUTUBE_URL, make_bot, make_ctx

VIDEO = {
    "url": "https://stream/a",
    "webpage_url": YOUTUBE_URL,
    "title": "Video",
    "duration": 3725,
    "uploader": "Uploader",
    "uploader_url": "https://youtube.com/@u",
    "upload_date": "20240131",
    "thumbnail": "https://i.ytimg.com/a.jpg",
    "view_count": 10,
    "like_count": 2,
}


def audio_source() -> mock.MagicMock:
    source = mock.MagicMock(spec=discord.AudioSource)
    source.is_opus.return_value = False
    return source


class SourcesTestCase(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music import sources

        self.sources = sources
        self.ctx = make_ctx()
        self.ctx.respond = mock.AsyncMock()
        self.loop = make_bot().loop
        patcher = mock.patch("discord.FFmpegPCMAudio", side_effect=lambda *a, **k: audio_source())
        self.ffmpeg = patcher.start()
        self.addCleanup(patcher.stop)


class TestYTDLSource(SourcesTestCase):
    def test_metadata(self) -> None:
        source = self.sources.YTDLSource(
            self.ctx, audio_source(), data=dict(VIDEO, requester="me")
        )

        self.assertEqual(source.upload_date, "31.01.2024")
        self.assertEqual(source.duration, "1 hours 2 minutes 5 seconds")
        self.assertEqual(source.duration_raw, "1:02:05")
        self.assertEqual(source.duration_int, 3725)
        self.assertEqual(source.url, YOUTUBE_URL)
        self.assertEqual(source.requester, "me")
        self.assertEqual(str(source), "**Video** by **Uploader**")

    async def create(self, *responses, seek=None):
        with mock.patch.object(
            self.sources.YTDLSource.ytdl, "extract_info", side_effect=list(responses)
        ):
            return await self.sources.YTDLSource.create_source(
                self.ctx, "query", loop=self.loop, requester="me", seek=seek
            )

    async def test_create_from_search(self) -> None:
        source = await self.create(
            {"entries": [None, {"webpage_url": YOUTUBE_URL}]}, dict(VIDEO)
        )

        self.assertEqual(source.title, "Video")
        self.assertEqual(source.requester, "me")
        self.assertEqual(self.ffmpeg.call_args.args[0], "https://stream/a")

    async def test_create_with_seek(self) -> None:
        await self.create(dict(VIDEO), dict(VIDEO), seek=90)

        self.assertIn("-ss 1:30", self.ffmpeg.call_args.kwargs["before_options"])

    async def test_processed_entries_take_first(self) -> None:
        source = await self.create(dict(VIDEO), {"entries": [dict(VIDEO, title="First")]})

        self.assertEqual(source.title, "First")

    async def test_nothing_found(self) -> None:
        await self.create(None)

        self.assertTrue(
            self.ctx.respond.call_args.kwargs["embed"].title.startswith("Couldn't find")
        )

    async def test_search_without_usable_entries(self) -> None:
        await self.create({"entries": [None]})

        self.assertTrue(
            self.ctx.respond.call_args.kwargs["embed"].title.startswith("Couldn't find")
        )

    async def test_video_page_unavailable(self) -> None:
        await self.create(dict(VIDEO), None)

        self.assertEqual(
            self.ctx.respond.call_args.kwargs["embed"].title,
            f"Couldn't fetch `{YOUTUBE_URL}`",
        )

    async def test_video_page_empty_entries(self) -> None:
        await self.create(dict(VIDEO), {"entries": []})

        self.assertTrue(
            self.ctx.respond.call_args.kwargs["embed"].title.startswith("Couldn't find")
        )


class TestFFMPEGSource(SourcesTestCase):
    def test_metadata(self) -> None:
        source = self.sources.FFMPEGSource(
            self.ctx,
            audio_source(),
            data={"title": "File", "url": "local@/a.mp3", "duration": "65"},
        )

        self.assertIs(source.requester, self.ctx.author)
        self.assertEqual(source.duration, "1 minutes 5 seconds")
        self.assertEqual(source.duration_raw, "1:05")
        self.assertEqual(str(source), "**File**")

    async def test_create_source(self) -> None:
        with mock.patch.object(
            self.sources.FFMPEGSource.ytdl, "extract_info", return_value=dict(VIDEO)
        ):
            source = await self.sources.FFMPEGSource.create_source(
                self.ctx, "https://cdn/a.mp3", loop=self.loop, requester="me"
            )

        self.assertEqual(source.title, "Video")
        self.assertEqual(source.data["requester"], "me")


class TestSong(SourcesTestCase):
    def make_song(self, **kwargs):
        source = mock.MagicMock()
        source.title = "Song"
        source.duration = "3 minutes"
        source.duration_raw = "3:00"
        source.url = "https://cdn/a.mp3"
        return self.sources.Song(source, **kwargs)

    @mock.patch("time.time", return_value=1100.0)
    def test_now_embed_shows_progress_without_pauses(self, _time) -> None:
        song = self.make_song(is_file=True)
        song.start_time = 1000.0
        song.paused = True
        song.pause_time = 1090.0

        embed = song.create_embed("now")

        values = {field.name: field.value for field in embed.fields}
        self.assertEqual(values["Duration"], "1:30/3:00")
        self.assertNotIn("Uploader", values)

    def test_direct_link_embed_has_url(self) -> None:
        embed = self.make_song(is_file=True, is_direct_link=True).create_embed("play")

        values = {field.name: field.value for field in embed.fields}
        self.assertEqual(values["Duration"], "3 minutes")
        self.assertEqual(values["URL"], "[Click](https://cdn/a.mp3)")


class TestSongQueue(SourcesTestCase):
    async def asyncSetUp(self) -> None:
        self.queue = self.sources.SongQueue()
        for title in "abcd":
            await self.queue.put(title)

    def test_sequence_access(self) -> None:
        self.assertEqual(len(self.queue), 4)
        self.assertEqual(self.queue[1], "b")
        self.assertEqual(self.queue[1:3], ["b", "c"])
        self.assertEqual(list(self.queue), ["a", "b", "c", "d"])

    def test_remove_and_clear(self) -> None:
        self.queue.remove(0)
        self.assertEqual(list(self.queue), ["b", "c", "d"])

        self.queue.clear()
        self.assertEqual(len(self.queue), 0)

    @mock.patch("random.shuffle")
    def test_shuffle(self, mock_shuffle) -> None:
        self.queue.shuffle()

        mock_shuffle.assert_called_once_with(self.queue._queue)
