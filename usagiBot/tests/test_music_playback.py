from unittest import IsolatedAsyncioTestCase
from unittest import mock

from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *
from usagiBot.tests.music_helpers import make_current, make_state


class PlaybackTestCase(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music import playback

        self.playback = playback
        self.current = make_current(start_time=1000.0)
        self.state = make_state(mock.MagicMock(), self.current)


class TestPauseResume(PlaybackTestCase):
    @mock.patch("time.time", return_value=1050.0)
    def test_pause(self, _time) -> None:
        self.assertTrue(self.playback.pause_song(self.state))

        self.state.voice.pause.assert_called_once()
        self.assertTrue(self.current.paused)
        self.assertEqual(self.current.pause_time, 1050.0)

    def test_pause_when_nothing_plays(self) -> None:
        self.state.voice.is_playing.return_value = False

        self.assertFalse(self.playback.pause_song(self.state))
        self.state.voice.pause.assert_not_called()

    @mock.patch("time.time", return_value=1080.0)
    def test_resume(self, _time) -> None:
        self.state.voice.is_paused.return_value = True
        self.current.paused = True
        self.current.pause_time = 1050.0
        self.current.pause_duration = 5

        self.assertTrue(self.playback.resume_song(self.state))

        self.state.voice.resume.assert_called_once()
        self.assertEqual(self.current.pause_duration, 35.0)
        self.assertEqual(self.current.pause_time, 0)
        self.assertFalse(self.current.paused)

    def test_resume_when_not_paused(self) -> None:
        self.assertFalse(self.playback.resume_song(self.state))
        self.state.voice.resume.assert_not_called()


class TestQueueActions(PlaybackTestCase):
    async def test_stop_queue(self) -> None:
        await self.state.songs.put({"title": "next"})

        stopped = await self.playback.stop_queue(self.state)

        self.assertTrue(stopped)
        self.assertEqual(len(self.state.songs), 0)
        self.state.stop.assert_awaited_once_with()
        self.assertTrue(self.state.stopped)

    async def test_stop_queue_when_idle_only_clears(self) -> None:
        self.state.is_playing = False
        await self.state.songs.put({"title": "next"})

        stopped = await self.playback.stop_queue(self.state)

        self.assertFalse(stopped)
        self.assertEqual(len(self.state.songs), 0)
        self.state.stop.assert_not_called()

    async def test_requeue_current(self) -> None:
        await self.playback.requeue_current(self.state)

        self.assertEqual(
            self.state.songs[0],
            {
                "url": self.current.source.url,
                "title": "song",
                "user": self.current.source.requester,
                "duration": 200,
            },
        )

    async def test_requeue_without_current_song(self) -> None:
        self.state.current = None

        await self.playback.requeue_current(self.state)

        self.assertEqual(len(self.state.songs), 0)

    async def test_toggle_loop_queue_requeues_on_enable(self) -> None:
        enabled = await self.playback.toggle_loop_queue(self.state)

        self.assertTrue(enabled)
        self.assertTrue(self.state.loop_queue)
        self.assertEqual(len(self.state.songs), 1)

    async def test_toggle_loop_queue_disable(self) -> None:
        self.state.loop_queue = True

        enabled = await self.playback.toggle_loop_queue(self.state)

        self.assertFalse(enabled)
        self.assertEqual(len(self.state.songs), 0)
