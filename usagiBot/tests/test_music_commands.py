from unittest import IsolatedAsyncioTestCase
from unittest import mock

import discord
from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *
from usagiBot.tests.music_helpers import (
    YOUTUBE_URL,
    embed_title,
    embed_titles,
    make_bot,
    make_ctx,
    make_current,
)

NOT_IN_VOICE = "You are not connected to any voice channel or the same voice channel."
NOTHING_PLAYING = "There is no songs playing right now."


class MusicCommandTestCase(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music.index import Music
        from usagiBot.cogs.Music.sources import YTDLSource

        self.Music = Music
        self.YTDLSource = YTDLSource
        self.bot = make_bot()
        self.cog = Music(self.bot)
        # direct links get a DNS check; these tests only use public hosts
        patcher = mock.patch(
            "usagiBot.cogs.Music.enqueue.validate_public_http_url",
            new_callable=mock.AsyncMock,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    async def run_command(self, name: str, ctx, *args):
        return await getattr(self.Music, name).callback(self.cog, ctx, *args)

    def leave_voice(self, ctx) -> None:
        ctx.author.voice = None


class TestJoin(MusicCommandTestCase):
    async def test_author_not_in_voice(self) -> None:
        ctx = make_ctx()
        self.leave_voice(ctx)

        result = await self.run_command("join", ctx)

        self.assertFalse(result)
        self.assertEqual(embed_title(ctx.respond), NOT_IN_VOICE)

    async def test_bot_in_another_channel(self) -> None:
        ctx = make_ctx()
        ctx.voice_client = mock.MagicMock()
        ctx.voice_client.channel.id = 1
        ctx.author.voice.channel.id = 2

        result = await self.run_command("join", ctx)

        self.assertFalse(result)
        self.assertEqual(embed_title(ctx.respond), "Bot is already in a voice channel.")

    async def test_bot_already_in_your_channel(self) -> None:
        ctx = make_ctx()
        ctx.voice_client = mock.MagicMock()
        ctx.voice_client.channel.id = ctx.author.voice.channel.id = 1

        result = await self.run_command("join", ctx)

        self.assertFalse(result)
        self.assertEqual(
            embed_title(ctx.respond), "Bot is already in your voice channel."
        )

    async def test_already_joined_is_fine_when_called_from_play(self) -> None:
        ctx = make_ctx()
        ctx.voice_client = mock.MagicMock()
        ctx.voice_client.channel.id = ctx.author.voice.channel.id = 1
        ctx.from_play = True

        result = await self.run_command("join", ctx)

        self.assertTrue(result)
        ctx.respond.assert_not_called()

    async def test_connects_to_author_channel(self) -> None:
        ctx = make_ctx()

        await self.run_command("join", ctx)

        ctx.author.voice.channel.connect.assert_awaited_once()
        self.assertTrue(embed_title(ctx.respond).startswith("Joined"))
        ctx.me.edit.assert_awaited_with(deafen=True)

    async def test_no_connect_permission(self) -> None:
        ctx = make_ctx()
        ctx.author.voice.channel.permissions_for.return_value.connect = False

        await self.run_command("join", ctx)

        ctx.author.voice.channel.connect.assert_not_called()
        self.assertEqual(
            embed_title(ctx.respond), "No permission to join the voice channel!"
        )


class TestSummon(MusicCommandTestCase):
    def make_destination(self, connect: bool = True, spec: type = None) -> mock.MagicMock:
        destination = mock.MagicMock(name="destination", spec=spec)
        destination.permissions_for.return_value.connect = connect
        destination.connect = mock.AsyncMock()
        return destination

    async def test_requires_move_members(self) -> None:
        ctx = make_ctx()
        ctx.author.guild_permissions.move_members = False
        ctx.author.id = 123

        await self.run_command("summon", ctx, self.make_destination())

        self.assertIn("Move Member", embed_title(ctx.respond))

    async def test_bot_owner_bypasses_move_members(self) -> None:
        ctx = make_ctx()
        ctx.author.guild_permissions.move_members = False
        ctx.author.id = int(os.environ["BOT_OWNER"])
        destination = self.make_destination()
        voice = ctx.voice_state.voice

        await self.run_command("summon", ctx, destination)

        voice.move_to.assert_awaited_with(destination)

    async def test_no_permission_for_destination(self) -> None:
        ctx = make_ctx()

        await self.run_command("summon", ctx, self.make_destination(connect=False))

        self.assertEqual(
            embed_title(ctx.respond), "No permission to join the voice channel!"
        )

    async def test_moves_when_already_connected(self) -> None:
        ctx = make_ctx()
        voice = ctx.voice_state.voice
        destination = self.make_destination()

        await self.run_command("summon", ctx, destination)

        voice.move_to.assert_awaited_with(destination)
        self.assertTrue(embed_title(ctx.respond).startswith("Switched"))
        # the state follows the guild's voice client after the move
        self.assertIs(ctx.voice_state.voice, ctx.guild.voice_client)
        # names the channel the bot left, not the one it moved to
        self.assertIn(f"from **{voice.channel}**", embed_title(ctx.respond))

    async def test_connects_when_not_connected(self) -> None:
        ctx = make_ctx()
        ctx.voice_state.voice = None
        destination = self.make_destination()

        await self.run_command("summon", ctx, destination)

        destination.connect.assert_awaited_once()
        ctx.defer.assert_awaited_with(ephemeral=True)
        self.assertTrue(embed_title(ctx.respond).startswith("Joined"))

    @mock.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    async def test_stage_channel_without_speak_permission(self, _sleep) -> None:
        ctx = make_ctx()
        ctx.voice_state.voice = None
        destination = self.make_destination(spec=discord.StageChannel)
        ctx.me.edit.side_effect = discord.Forbidden(mock.MagicMock(), "nope")

        await self.run_command("summon", ctx, destination)

        self.assertEqual(
            embed_title(ctx.respond),
            "I have no permission to speak! Please invite me to speak.",
        )


class TestLeave(MusicCommandTestCase):
    async def test_author_not_in_voice(self) -> None:
        ctx = make_ctx()
        self.leave_voice(ctx)

        await self.run_command("leave", ctx)

        ctx.voice_state.stop.assert_not_called()

    async def test_bot_not_connected(self) -> None:
        ctx = make_ctx()
        ctx.voice_state.voice = None

        await self.run_command("leave", ctx)

        self.assertEqual(
            embed_title(ctx.respond), "Bot is not connected to any voice channel."
        )

    async def test_leaves_and_forgets_state(self) -> None:
        ctx = make_ctx()
        self.cog.voice_states[ctx.guild.id] = ctx.voice_state

        await self.run_command("leave", ctx)

        ctx.voice_state.stop.assert_awaited_with(leave=True)
        self.assertNotIn(ctx.guild.id, self.cog.voice_states)


class TestNowPauseResume(MusicCommandTestCase):
    async def test_now_without_song(self) -> None:
        ctx = make_ctx()

        await self.run_command("now", ctx)

        self.assertEqual(embed_title(ctx.respond), NOTHING_PLAYING)

    async def test_now_shows_current_song(self) -> None:
        current = make_current()
        ctx = make_ctx(current)

        await self.run_command("now", ctx)

        current.create_embed.assert_called_with("now")
        self.assertIs(ctx.respond.call_args.kwargs["embed"], current.create_embed())

    async def test_pause_playing_song(self) -> None:
        ctx = make_ctx(make_current())

        await self.run_command("pause", ctx)

        ctx.voice_state.voice.pause.assert_called_once()
        self.assertTrue(ctx.voice_state.current.paused)
        self.assertEqual(embed_title(ctx.respond), "Music paused.")

    async def test_pause_without_song(self) -> None:
        ctx = make_ctx()

        await self.run_command("pause", ctx)

        ctx.voice_state.voice.pause.assert_not_called()
        self.assertEqual(embed_title(ctx.respond), NOTHING_PLAYING)

    async def test_pause_requires_same_channel(self) -> None:
        ctx = make_ctx(make_current())
        ctx.author.voice.channel = mock.MagicMock(name="other_channel")

        await self.run_command("pause", ctx)

        ctx.voice_state.voice.pause.assert_not_called()
        self.assertEqual(embed_title(ctx.respond), NOT_IN_VOICE)

    @mock.patch("time.time", return_value=1100.0)
    async def test_resume_paused_song(self, _time) -> None:
        current = make_current()
        current.pause_time = 1040.0
        ctx = make_ctx(current)
        ctx.voice_state.voice.is_paused.return_value = True

        await self.run_command("resume", ctx)

        ctx.voice_state.voice.resume.assert_called_once()
        self.assertEqual(current.pause_duration, 60.0)
        self.assertFalse(current.paused)
        self.assertEqual(embed_title(ctx.respond), "Music resumed.")

    async def test_resume_without_paused_song(self) -> None:
        ctx = make_ctx(make_current())

        await self.run_command("resume", ctx)

        ctx.voice_state.voice.resume.assert_not_called()
        self.assertEqual(embed_title(ctx.respond), "There is no songs paused right now.")


class VoteCommandTestCase(MusicCommandTestCase):
    def sleep_then_vote(self, ctx, votes: int) -> mock.AsyncMock:
        """asyncio.sleep stand-in that sets the vote tally during the wait."""

        async def fake_sleep(_seconds):
            ctx.send_followup.call_args.kwargs["view"].votes = votes

        return mock.AsyncMock(side_effect=fake_sleep)

    def verdict(self, ctx) -> str:
        return ctx.send_followup.return_value.edit.call_args.kwargs["embed"].title


class TestStop(VoteCommandTestCase):
    async def test_approved_stop_clears_queue(self) -> None:
        ctx = make_ctx(make_current())
        await ctx.voice_state.songs.put({"title": "next"})

        with mock.patch("asyncio.sleep", self.sleep_then_vote(ctx, 1)):
            await self.run_command("stop", ctx)

        ctx.defer.assert_awaited_once()
        self.assertEqual(
            ctx.send_followup.call_args.kwargs["embed"].title, "Stop current queue?"
        )
        self.assertEqual(len(ctx.voice_state.songs), 0)
        ctx.voice_state.stop.assert_awaited_once()
        self.assertTrue(ctx.voice_state.stopped)
        self.assertEqual(self.verdict(ctx), "Stop approved")
        self.assertEqual(embed_title(ctx.respond), "Music stopped")
        ctx.send_followup.return_value.delete.assert_awaited_with(delay=10)

    async def test_rejected_stop_keeps_queue(self) -> None:
        ctx = make_ctx(make_current())
        await ctx.voice_state.songs.put({"title": "next"})

        with mock.patch("asyncio.sleep", self.sleep_then_vote(ctx, 0)):
            await self.run_command("stop", ctx)

        self.assertEqual(len(ctx.voice_state.songs), 1)
        ctx.voice_state.stop.assert_not_called()
        self.assertEqual(self.verdict(ctx), "Stop canceled")
        ctx.respond.assert_not_called()

    async def test_author_not_in_voice(self) -> None:
        ctx = make_ctx(make_current())
        self.leave_voice(ctx)

        await self.run_command("stop", ctx)

        ctx.send_followup.assert_not_called()


class TestSkip(VoteCommandTestCase):
    async def test_nothing_playing(self) -> None:
        ctx = make_ctx()

        await self.run_command("skip", ctx)

        self.assertEqual(embed_title(ctx.respond), NOTHING_PLAYING)
        ctx.send_followup.assert_not_called()

    async def test_approved_skip(self) -> None:
        ctx = make_ctx(make_current(title="current song"))

        with mock.patch("asyncio.sleep", self.sleep_then_vote(ctx, 2)):
            await self.run_command("skip", ctx)

        self.assertIn(
            "current song", ctx.send_followup.call_args.kwargs["embed"].description
        )
        ctx.voice_state.skip.assert_called_once()
        self.assertEqual(self.verdict(ctx), "Skip approved")
        ctx.send_followup.return_value.delete.assert_awaited_with(delay=10)

    async def test_rejected_skip(self) -> None:
        ctx = make_ctx(make_current())

        with mock.patch("asyncio.sleep", self.sleep_then_vote(ctx, -1)):
            await self.run_command("skip", ctx)

        ctx.voice_state.skip.assert_not_called()
        self.assertEqual(self.verdict(ctx), "Skip canceled")


class TestQueueCommands(MusicCommandTestCase):
    async def fill(self, ctx, count: int) -> None:
        for number in range(count):
            await ctx.voice_state.songs.put(
                {"url": f"https://youtu.be/{number}", "title": f"t{number}", "duration": 60}
            )

    async def test_queue_empty(self) -> None:
        ctx = make_ctx()

        await self.run_command("queue", ctx, 1)

        self.assertEqual(embed_title(ctx.respond), "Empty queue.")

    @mock.patch("time.time", return_value=1050.0)
    async def test_queue_shows_page(self, _time) -> None:
        ctx = make_ctx(make_current(title="now", duration=200, start_time=1000.0))
        await self.fill(ctx, 7)

        await self.run_command("queue", ctx, 2)

        embed = ctx.respond.call_args.kwargs["embed"]
        self.assertEqual(embed.title, "Currently Playing")
        self.assertIn("2 minutes 30 seconds Left", embed.description)
        self.assertIn("`6.`", embed.fields[0].value)
        self.assertEqual(embed.footer.text, "Viewing page 2/2")

    @mock.patch("time.time", return_value=1000.0)
    async def test_queue_page_below_one_is_first_page(self, _time) -> None:
        ctx = make_ctx(make_current())
        await self.fill(ctx, 3)

        await self.run_command("queue", ctx, -5)

        self.assertEqual(
            ctx.respond.call_args.kwargs["embed"].footer.text, "Viewing page 1/1"
        )

    async def test_shuffle_empty(self) -> None:
        ctx = make_ctx()

        await self.run_command("shuffle", ctx)

        self.assertEqual(embed_title(ctx.respond), "Empty queue.")

    @mock.patch("random.shuffle")
    async def test_shuffle(self, mock_shuffle) -> None:
        ctx = make_ctx()
        await self.fill(ctx, 3)

        await self.run_command("shuffle", ctx)

        mock_shuffle.assert_called_once()
        self.assertEqual(embed_title(ctx.respond), "Song queue shuffled")

    async def test_remove_rejects_non_positive_index(self) -> None:
        ctx = make_ctx()

        await self.run_command("remove", ctx, 0)

        self.assertEqual(
            embed_title(ctx.respond),
            "Please provide a valid song number in queue to remove.",
        )

    async def test_remove_from_empty_queue(self) -> None:
        ctx = make_ctx()

        await self.run_command("remove", ctx, 1)

        self.assertEqual(embed_title(ctx.respond), "Empty queue.")

    async def test_remove_song(self) -> None:
        ctx = make_ctx()
        await self.fill(ctx, 3)

        await self.run_command("remove", ctx, 2)

        self.assertEqual([song["title"] for song in ctx.voice_state.songs], ["t0", "t2"])
        self.assertEqual(embed_title(ctx.respond), "Song removed.")

    async def test_loop_toggles(self) -> None:
        ctx = make_ctx(make_current())

        await self.run_command("loop", ctx)
        self.assertTrue(ctx.voice_state.loop)
        self.assertEqual(embed_title(ctx.respond), "Enabled looping")

        await self.run_command("loop", ctx)
        self.assertFalse(ctx.voice_state.loop)
        self.assertEqual(embed_title(ctx.respond), "Disabled looping")

    async def test_loopqueue_requeues_current_song(self) -> None:
        ctx = make_ctx(make_current(title="now"))

        await self.run_command("loopqueue", ctx)

        self.assertTrue(ctx.voice_state.loop_queue)
        self.assertEqual(ctx.voice_state.songs[0]["title"], "now")
        self.assertEqual(embed_title(ctx.respond), "Enabled loop queue")

    async def test_loopqueue_disable(self) -> None:
        ctx = make_ctx(make_current())
        ctx.voice_state.loop_queue = True

        await self.run_command("loopqueue", ctx)

        self.assertFalse(ctx.voice_state.loop_queue)
        self.assertEqual(len(ctx.voice_state.songs), 0)
        self.assertEqual(embed_title(ctx.respond), "Disabled loop queue")


class TestMusicReload(MusicCommandTestCase):
    async def test_reload_forgets_state_even_when_cleanup_fails(self) -> None:
        ctx = make_ctx()
        ctx.voice_client = mock.MagicMock()
        ctx.voice_state.stop.side_effect = RuntimeError("boom")
        ctx.voice_client.disconnect = mock.AsyncMock(side_effect=RuntimeError("boom"))
        ctx.voice_client.cleanup.side_effect = RuntimeError("boom")
        self.cog.voice_states[ctx.guild.id] = ctx.voice_state

        await self.run_command("musicreload", ctx)

        self.assertNotIn(ctx.guild.id, self.cog.voice_states)
        self.assertEqual(embed_title(ctx.respond), "Music bot reloaded.")


class TestPlay(MusicCommandTestCase):
    def patch_extract(self, attr: str, **kwargs):
        ytdl = getattr(self.YTDLSource, attr)
        return mock.patch.object(ytdl, "extract_info", **kwargs)

    def last_status(self, ctx) -> str:
        message = ctx.respond.return_value
        return message.edit_original_response.call_args.kwargs["embed"].title

    async def test_youtube_video_is_enqueued(self) -> None:
        ctx = make_ctx()
        data = {"webpage_url": YOUTUBE_URL, "title": "Video", "duration": 125.0}

        with self.patch_extract("ytdl", return_value=data):
            await self.run_command("play", ctx, YOUTUBE_URL)

        song = ctx.voice_state.songs[0]
        self.assertEqual(song["url"], YOUTUBE_URL)
        self.assertEqual(song["duration"], 125)
        self.assertIs(song["user"], ctx.author)
        self.assertEqual(self.last_status(ctx), "Enqueued **Video**")
        self.assertFalse(ctx.voice_state.stopped)

    async def test_youtube_search_takes_first_entry(self) -> None:
        ctx = make_ctx()
        entry = {"webpage_url": YOUTUBE_URL, "title": "First", "duration": None}

        with self.patch_extract("ytdl", return_value={"entries": [entry]}):
            await self.run_command("play", ctx, "https://youtube.com/results?q=x")

        self.assertEqual(ctx.voice_state.songs[0]["title"], "First")
        self.assertEqual(ctx.voice_state.songs[0]["duration"], 0)

    async def test_youtube_empty_search(self) -> None:
        ctx = make_ctx()

        with self.patch_extract("ytdl", return_value={"entries": []}):
            await self.run_command("play", ctx, YOUTUBE_URL)

        self.assertEqual(len(ctx.voice_state.songs), 0)
        self.assertTrue(self.last_status(ctx).startswith("Couldn't find anything"))

    async def test_youtube_known_error_is_translated(self) -> None:
        ctx = make_ctx()

        with self.patch_extract("ytdl", side_effect=Exception("Video unavailable")):
            await self.run_command("play", ctx, YOUTUBE_URL)

        self.assertEqual(self.last_status(ctx), "Error: Video Unavailable")

    async def test_playlist_enqueues_every_song_with_duration(self) -> None:
        ctx = make_ctx()
        link = "https://www.youtube.com/playlist?list=PL1"
        data = {
            "entries": [
                {"id": "a", "title": "A", "duration": 10},
                {"id": "b", "title": "B", "duration": None},
                {"id": "c", "title": "C", "duration": 30.0},
            ]
        }

        with self.patch_extract("ytdl_playlist", return_value=data):
            await self.run_command("play", ctx, link)

        self.assertEqual(
            [song["url"] for song in ctx.voice_state.songs],
            ["https://youtu.be/a", "https://youtu.be/c"],
        )
        self.assertEqual(self.last_status(ctx), "Enqueued **2** songs")

    async def test_playlist_not_found(self) -> None:
        ctx = make_ctx()
        link = "https://www.youtube.com/playlist?list=PL1"

        with self.patch_extract("ytdl_playlist", return_value=None):
            await self.run_command("play", ctx, link)

        self.assertTrue(self.last_status(ctx).startswith("Couldn't find anything"))

    async def test_direct_link_with_duration(self) -> None:
        ctx = make_ctx()
        link = "https://cdn.example.com/my_song.mp3"
        data = {"title": "my_song", "duration": "61.5", "url": "https://cdn/real"}

        with self.patch_extract("ytdl", return_value=data):
            await self.run_command("play", ctx, link)

        song = ctx.voice_state.songs[0]
        self.assertEqual(song["url"], link)
        self.assertEqual(song["duration"], 61)
        self.assertEqual(song["realurl"], "https://cdn/real")
        self.assertEqual(self.last_status(ctx), "Enqueued **my\\_song**")

    @mock.patch("asyncio.create_subprocess_exec", new_callable=mock.AsyncMock)
    async def test_direct_link_without_duration_asks_ffprobe(self, mock_exec) -> None:
        mock_exec.return_value.communicate.return_value = (b"42.9\n", b"")
        mock_exec.return_value.returncode = 0
        ctx = make_ctx()
        link = "https://cdn.example.com/song.mp3"
        data = {"title": "song", "url": "https://cdn/real"}

        with self.patch_extract("ytdl", return_value=data):
            await self.run_command("play", ctx, link)

        self.assertEqual(ctx.voice_state.songs[0]["duration"], 42)
        self.assertIn(link, mock_exec.call_args.args)

    async def test_direct_link_failure(self) -> None:
        ctx = make_ctx()

        with self.patch_extract("ytdl", side_effect=Exception("unsupported")):
            await self.run_command("play", ctx, "https://cdn.example.com/x.txt")

        self.assertEqual(len(ctx.voice_state.songs), 0)
        self.assertEqual(
            self.last_status(ctx),
            "Unable to add this song, maybe it is not an audio file?",
        )

    async def test_bot_in_another_channel(self) -> None:
        ctx = make_ctx()
        ctx.voice_client = mock.MagicMock()
        ctx.voice_client.channel = mock.MagicMock(name="elsewhere")

        with self.patch_extract("ytdl") as extract:
            await self.run_command("play", ctx, YOUTUBE_URL)

        extract.assert_not_called()
        self.assertEqual(embed_title(ctx.respond), "Bot is already in a voice channel.")

    async def test_joins_first_when_not_connected(self) -> None:
        ctx = make_ctx()
        ctx.voice_state.voice = None
        voice_channel = ctx.author.voice.channel
        connected = mock.MagicMock()
        connected.channel = voice_channel
        voice_channel.connect.return_value = connected
        data = {"webpage_url": YOUTUBE_URL, "title": "Video", "duration": 1}

        with self.patch_extract("ytdl", return_value=data):
            await self.run_command("play", ctx, YOUTUBE_URL)

        voice_channel.connect.assert_awaited_once()
        self.assertEqual(ctx.voice_state.songs[0]["title"], "Video")

    async def test_stops_when_join_fails(self) -> None:
        ctx = make_ctx()
        ctx.voice_state.voice = None
        ctx.author.voice.channel.permissions_for.return_value.connect = False

        with self.patch_extract("ytdl") as extract:
            await self.run_command("play", ctx, YOUTUBE_URL)

        extract.assert_not_called()
        self.assertEqual(
            embed_titles(ctx.respond), ["No permission to join the voice channel!"]
        )


class TestSearch(MusicCommandTestCase):
    async def test_lists_results_in_a_select_menu(self) -> None:
        ctx = make_ctx()
        data = {
            "entries": [
                {"title": "One", "duration": 65, "webpage_url": "https://youtu.be/1"},
                {"title": "Two", "duration": None, "id": "2"},
            ]
        }

        with mock.patch.object(
            self.YTDLSource.ytdl_playlist, "extract_info", return_value=data
        ) as extract:
            await self.run_command("search", ctx, "lofi")

        self.assertEqual(extract.call_args.args[0], "ytsearch10:lofi")
        embed = ctx.respond.call_args.kwargs["embed"]
        self.assertEqual(embed.title, "Search results of lofi")
        self.assertEqual(embed.fields[0].name, "1. One")
        self.assertIn("1 minutes 5 seconds", embed.fields[0].value)
        self.assertIn("https://youtu.be/2", embed.fields[1].value)
        self.assertIn("Unknown", embed.fields[1].value)
        view = ctx.respond.call_args.kwargs["view"]
        self.assertIs(view.message, ctx.respond.return_value)


class TestSeek(MusicCommandTestCase):
    async def seek(self, raw: str, current=None, now: float = 1100.0):
        ctx = make_ctx(current or make_current(start_time=1000.0))
        with mock.patch("time.time", return_value=now):
            await self.run_command("seek", ctx, raw)
        return ctx

    async def test_nothing_playing(self) -> None:
        ctx = make_ctx()

        await self.run_command("seek", ctx, "10")

        ctx.voice_state.seek.assert_not_called()
        self.assertEqual(embed_title(ctx.respond), NOTHING_PLAYING)

    async def test_plain_seconds(self) -> None:
        ctx = await self.seek("75")

        ctx.voice_state.seek.assert_awaited_with(75, False)
        self.assertEqual(embed_title(ctx.respond), "Seek to 75s")

    async def test_hours_minutes_seconds(self) -> None:
        ctx = await self.seek("1h2m3s")

        self.assertEqual(ctx.voice_state.seek.call_args.args[0], 3723)

    async def test_minutes_only(self) -> None:
        ctx = await self.seek("2m")

        self.assertEqual(ctx.voice_state.seek.call_args.args[0], 120)

    async def test_forward_from_current_position(self) -> None:
        ctx = await self.seek("+15")

        self.assertEqual(ctx.voice_state.seek.call_args.args[0], 115)

    async def test_backward_clamps_at_zero(self) -> None:
        ctx = await self.seek("-500")

        self.assertEqual(ctx.voice_state.seek.call_args.args[0], 0)

    async def test_forward_while_paused_excludes_pause(self) -> None:
        current = make_current(start_time=1000.0)
        current.paused = True
        current.pause_time = 1080.0

        ctx = await self.seek("+0", current)

        self.assertEqual(ctx.voice_state.seek.call_args.args[0], 80)
        self.assertEqual(current.pause_time, 1100.0)

    async def test_unparseable_value(self) -> None:
        ctx = await self.seek("soon")

        ctx.voice_state.seek.assert_not_called()
        self.assertEqual(embed_title(ctx.respond), "Unable to parse seconds to seek!")

    async def test_direct_link_flag(self) -> None:
        ctx = await self.seek("5", make_current(url="https://cdn.example.com/a.mp3"))

        ctx.voice_state.seek.assert_awaited_with(5, True)


class TestCogLifecycle(MusicCommandTestCase):
    def test_get_voice_state_creates_once_per_guild(self) -> None:
        ctx = make_ctx()

        first = self.cog.get_voice_state(ctx)
        second = self.cog.get_voice_state(ctx)

        self.assertIs(first, second)
        self.assertIs(self.cog.voice_states[ctx.guild.id], first)

    def test_get_voice_state_restarts_finished_player(self) -> None:
        ctx = make_ctx()
        state = self.cog.get_voice_state(ctx)
        state.audio_player.done.return_value = True

        with mock.patch.object(type(state), "recreate_bg_task") as recreate:
            self.cog.get_voice_state(ctx)

        recreate.assert_called_once_with(ctx, self.cog)

    def test_cog_check_rejects_dm(self) -> None:
        from discord.ext import commands

        ctx = make_ctx()
        ctx.guild = None

        with self.assertRaises(commands.NoPrivateMessage):
            self.cog.cog_check(ctx)

    def test_cog_check_disabled_module(self) -> None:
        from usagiBot.src.UsagiErrors import UsagiModuleDisabledError

        ctx = make_ctx()
        ctx.bot.guild_cogs_settings = {ctx.guild.id: {"Wordle": True}}

        with self.assertRaises(UsagiModuleDisabledError):
            self.cog.cog_check(ctx)

    def test_cog_check_enabled_module(self) -> None:
        ctx = make_ctx()
        ctx.bot.guild_cogs_settings = {ctx.guild.id: {"Music": True}}

        self.assertTrue(self.cog.cog_check(ctx))

    async def test_before_invoke_attaches_voice_state(self) -> None:
        ctx = make_ctx()
        del ctx.voice_state

        await self.cog.cog_before_invoke(ctx)

        self.assertIs(ctx.voice_state, self.cog.voice_states[ctx.guild.id])
        self.assertFalse(ctx.from_play)
        self.assertEqual(ctx.debug, ctx.voice_state.debug)

    def test_cog_unload_stops_every_state(self) -> None:
        state = mock.MagicMock()
        state.stop = mock.MagicMock(return_value=mock.MagicMock())
        self.cog.voice_states[1] = state

        self.cog.cog_unload()

        state.stop.assert_called_with(leave=True)
        self.assertEqual(self.cog.voice_states, {})


class TestVoiceStateUpdateListener(MusicCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.state = mock.MagicMock()
        self.state.stop = mock.AsyncMock()
        self.channel = mock.MagicMock(name="bot_channel")
        self.state.voice.channel = self.channel
        self.cog.voice_states[1] = self.state

    def member(self, member_id: int = 5) -> mock.MagicMock:
        member = mock.MagicMock()
        member.id = member_id
        member.guild.id = 1
        return member

    def voice(self, channel) -> mock.MagicMock:
        return mock.MagicMock(channel=channel)

    async def test_ignores_guild_without_state(self) -> None:
        member = self.member()
        member.guild.id = 2

        await self.cog.on_voice_state_update(member, self.voice(None), self.voice(None))

        self.state.start_alone_timer.assert_not_called()

    async def test_bot_disconnected_cleans_up(self) -> None:
        await self.cog.on_voice_state_update(
            self.member(self.bot.user.id), self.voice(self.channel), self.voice(None)
        )

        self.state.stop.assert_awaited_with(leave=True)
        self.assertNotIn(1, self.cog.voice_states)

    async def test_bot_moved_into_empty_channel_starts_timer(self) -> None:
        empty = mock.MagicMock(members=[mock.MagicMock()])
        member = self.member(self.bot.user.id)

        await self.cog.on_voice_state_update(member, self.voice(None), self.voice(empty))

        self.assertIs(self.state.voice, member.guild.voice_client)
        self.state.start_alone_timer.assert_called_once()

    async def test_bot_moved_into_busy_channel_cancels_timer(self) -> None:
        busy = mock.MagicMock(members=[mock.MagicMock(), mock.MagicMock()])

        await self.cog.on_voice_state_update(
            self.member(self.bot.user.id), self.voice(None), self.voice(busy)
        )

        self.state.cancel_alone_timer.assert_called_once()

    async def test_user_joins_bot_channel_cancels_timer(self) -> None:
        await self.cog.on_voice_state_update(
            self.member(), self.voice(None), self.voice(self.channel)
        )

        self.state.cancel_alone_timer.assert_called_once()

    async def test_last_user_leaves_starts_timer(self) -> None:
        self.channel.members = [mock.MagicMock()]

        await self.cog.on_voice_state_update(
            self.member(), self.voice(self.channel), self.voice(None)
        )

        self.state.start_alone_timer.assert_called_once()

    async def test_bot_not_connected_ignores_users(self) -> None:
        self.state.voice = None

        await self.cog.on_voice_state_update(
            self.member(), self.voice(None), self.voice(self.channel)
        )

        self.state.cancel_alone_timer.assert_not_called()
