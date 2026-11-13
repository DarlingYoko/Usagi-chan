from unittest import TestCase

from usagiBot.tests.utils import *
from usagiBot.tests.music_helpers import make_current


class TestParseSeekTarget(TestCase):
    def setUp(self) -> None:
        from usagiBot.cogs.Music.seek import parse_seek_target

        self.parse = parse_seek_target
        self.song = make_current(start_time=1000.0)

    def test_plain_seconds(self) -> None:
        self.assertEqual(self.parse("75", self.song, now=1100.0), 75)

    def test_clock_units(self) -> None:
        self.assertEqual(self.parse("1h2m3s", self.song, now=1100.0), 3723)
        self.assertEqual(self.parse("2m", self.song, now=1100.0), 120)
        self.assertEqual(self.parse("1h", self.song, now=1100.0), 3600)
        self.assertEqual(self.parse("45s", self.song, now=1100.0), 45)

    def test_relative_forward(self) -> None:
        self.assertEqual(self.parse("+15", self.song, now=1100.0), 115)

    def test_relative_backward_clamps_at_zero(self) -> None:
        self.assertEqual(self.parse("-30", self.song, now=1100.0), 70)
        self.assertEqual(self.parse("-500", self.song, now=1100.0), 0)

    def test_relative_excludes_time_spent_paused(self) -> None:
        self.song.pause_duration = 20
        self.song.paused = True
        self.song.pause_time = 1090.0

        self.assertEqual(self.parse("+0", self.song, now=1100.0), 70)
        # the open pause is folded in so the next seek doesn't count it twice
        self.assertEqual(self.song.pause_duration, 30)
        self.assertEqual(self.song.pause_time, 1100.0)

    def test_rejects_garbage(self) -> None:
        # "s" alone used to match the optional "[0-9]*s" group and seek to 0
        for raw in ("soon", "s", "", "1.5", "+x", "5x", "m1"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.parse(raw, self.song, now=1100.0)


class TestLinkKind(TestCase):
    def setUp(self) -> None:
        from usagiBot.cogs.Music.seek import is_direct_link, is_youtube_domain

        self.is_direct_link = is_direct_link
        self.is_youtube_domain = is_youtube_domain

    def test_youtube_links(self) -> None:
        for url in (
            "https://www.youtube.com/watch?v=a",
            "https://youtube.com/watch?v=a",
            "https://music.youtube.com/watch?v=a",
            "https://m.youtube.com/watch?v=a",
            "https://youtu.be/a",
            "https://WWW.YouTube.com:443/watch?v=a",
        ):
            with self.subTest(url=url):
                self.assertFalse(self.is_direct_link(url))

    def test_direct_links(self) -> None:
        for url in (
            "https://cdn.example.com/a.mp3",
            "http://youtube.internal/watch?v=a",
            "http://notyoutube.com/a",
            "http://youtube.com.evil.test/a",
        ):
            with self.subTest(url=url):
                self.assertTrue(self.is_direct_link(url))

    def test_no_domain(self) -> None:
        self.assertFalse(self.is_youtube_domain(None))
