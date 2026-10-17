from unittest import IsolatedAsyncioTestCase
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
