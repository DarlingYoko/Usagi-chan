from unittest import IsolatedAsyncioTestCase
from unittest import mock

from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *
from usagiBot.tests.music_helpers import YOUTUBE_URL, make_bot, make_state


class TestEnqueueLink(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music.enqueue import enqueue_link
        from usagiBot.cogs.Music.sources import YTDLSource

        self.enqueue_link = enqueue_link
        self.YTDLSource = YTDLSource
        self.loop = make_bot().loop
        self.state = make_state(mock.MagicMock())
        self.state.stopped = True
        self.requester = mock.MagicMock(name="requester")

    async def enqueue(self, link: str, attr: str = "ytdl", **extract):
        with mock.patch.object(
            getattr(self.YTDLSource, attr), "extract_info", **extract
        ) as patched:
            result = await self.enqueue_link(self.loop, self.state, link, self.requester)
        self.extract = patched
        return result

    async def test_youtube_video(self) -> None:
        data = {"webpage_url": YOUTUBE_URL, "title": "Video", "duration": 99.9}

        result = await self.enqueue(YOUTUBE_URL, return_value=data)

        self.assertTrue(result.ok)
        self.assertEqual(result.message, "Enqueued **Video**")
        self.assertEqual(
            self.state.songs[0],
            {"url": YOUTUBE_URL, "title": "Video", "user": self.requester, "duration": 99},
        )
        self.assertFalse(self.state.stopped)
        self.assertEqual(self.extract.call_args.kwargs, {"download": False})

    async def test_plain_text_is_searched_on_youtube(self) -> None:
        data = {"entries": [{"webpage_url": YOUTUBE_URL, "title": "Hit", "duration": 3}]}

        result = await self.enqueue("never gonna", return_value=data)

        self.assertTrue(result.ok)
        self.assertEqual(self.state.songs[0]["title"], "Hit")

    async def test_missing_duration_becomes_zero(self) -> None:
        data = {"webpage_url": YOUTUBE_URL, "title": "Live", "duration": None}

        await self.enqueue(YOUTUBE_URL, return_value=data)

        self.assertEqual(self.state.songs[0]["duration"], 0)

    async def test_no_results(self) -> None:
        result = await self.enqueue(YOUTUBE_URL, return_value={"entries": []})

        self.assertFalse(result.ok)
        self.assertEqual(result.message, f"Couldn't find anything that matches `{YOUTUBE_URL}`")
        self.assertEqual(len(self.state.songs), 0)
        self.assertTrue(self.state.stopped)

    async def test_known_extractor_error_is_translated(self) -> None:
        result = await self.enqueue(YOUTUBE_URL, side_effect=Exception("Video unavailable"))

        self.assertFalse(result.ok)
        self.assertEqual(result.message, "Error: Video Unavailable")

    async def test_unknown_extractor_error_is_passed_through(self) -> None:
        result = await self.enqueue(YOUTUBE_URL, side_effect=Exception("HTTP 429"))

        self.assertEqual(result.message, "Error: HTTP 429")

    async def test_playlist(self) -> None:
        link = "https://www.youtube.com/playlist?list=PL1"
        data = {
            "entries": [
                {"id": "a", "title": "A", "duration": 10},
                {"id": "b", "title": "B", "duration": None},
                {"id": "c", "title": "C", "duration": 30.5},
            ]
        }

        result = await self.enqueue(link, attr="ytdl_playlist", return_value=data)

        self.assertTrue(result.ok)
        self.assertEqual(result.message, "Enqueued **2** songs")
        self.assertEqual(
            list(self.state.songs),
            [
                {"url": "https://youtu.be/a", "title": "A", "user": self.requester, "duration": 10},
                {"url": "https://youtu.be/c", "title": "C", "user": self.requester, "duration": 30},
            ],
        )
        self.assertFalse(self.state.stopped)

    async def test_playlist_not_found(self) -> None:
        link = "https://youtu.be/playlist?list=PL1"

        result = await self.enqueue(link, attr="ytdl_playlist", return_value=None)

        self.assertFalse(result.ok)
        self.assertTrue(result.message.startswith("Couldn't find anything"))

    async def test_playlist_param_on_other_site_is_a_direct_link(self) -> None:
        link = "https://cdn.example.com/playlist?x=1"
        data = {"title": "t", "duration": 5, "url": "https://cdn/real"}

        result = await self.enqueue(link, return_value=data)

        self.assertTrue(result.ok)
        self.assertEqual(self.state.songs[0]["realurl"], "https://cdn/real")

    async def test_direct_link(self) -> None:
        link = "https://cdn.example.com/a_b.mp3"
        data = {"entries": [{"title": "a_b", "duration": "12.7", "url": "https://cdn/real"}]}

        result = await self.enqueue(link, return_value=data)

        self.assertTrue(result.ok)
        self.assertEqual(result.message, "Enqueued **a\\_b**")
        self.assertEqual(
            self.state.songs[0],
            {
                "url": link,
                "title": "a_b",
                "user": self.requester,
                "duration": 12,
                "realurl": "https://cdn/real",
            },
        )

    async def test_direct_link_with_empty_entries(self) -> None:
        result = await self.enqueue(
            "https://cdn.example.com/a.mp3", return_value={"entries": []}
        )

        self.assertFalse(result.ok)
        self.assertTrue(result.message.startswith("Couldn't find anything"))

    @mock.patch("usagiBot.cogs.Music.enqueue.get_audio_duration", new_callable=mock.AsyncMock)
    async def test_direct_link_without_duration_uses_ffprobe(self, mock_duration) -> None:
        mock_duration.return_value = 321
        link = "https://cdn.example.com/a.mp3"

        await self.enqueue(link, return_value={"title": "a", "url": "https://cdn/real"})

        mock_duration.assert_awaited_with(link)
        self.assertEqual(self.state.songs[0]["duration"], 321)

    async def test_direct_link_that_is_not_audio(self) -> None:
        result = await self.enqueue(
            "https://cdn.example.com/a.txt", side_effect=Exception("unsupported")
        )

        self.assertFalse(result.ok)
        self.assertEqual(
            result.message, "Unable to add this song, maybe it is not an audio file?"
        )
