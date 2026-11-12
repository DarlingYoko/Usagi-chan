from unittest import IsolatedAsyncioTestCase
from unittest import mock

from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *
from usagiBot.tests.music_helpers import (
    YOUTUBE_URL,
    embed_title,
    embed_titles,
    make_bot,
    make_ctx,
    make_current,
    make_interaction,
    make_state,
)


class TestPlayerControlView(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music import player_view

        self.player_view = player_view
        self.listener = mock.MagicMock(name="listener")
        self.channel = mock.MagicMock(name="voice_channel")
        self.channel.members = [self.listener]
        self.state = make_state(self.channel, make_current(title="Song"))

    async def asyncSetUp(self) -> None:
        self.view = self.player_view.PlayerControlView(make_bot(), self.state)

    def button(self, custom_id: str):
        return self.player_view.get_button(self.view, custom_id)

    async def press(self, custom_id: str, user=None) -> mock.MagicMock:
        interaction = make_interaction(user or self.listener)
        await self.button(custom_id).callback(interaction)
        return interaction

    async def test_loop_labels_follow_state(self) -> None:
        self.assertEqual(self.button("3").label, "Enable Looping")
        self.assertEqual(self.button("4").label, "Enable Loop Queue")

    async def test_unknown_custom_id(self) -> None:
        with self.assertRaises(KeyError):
            self.button("nope")

    async def test_outsider_is_rejected(self) -> None:
        interaction = await self.press("0", user=mock.MagicMock(name="outsider"))

        self.state.voice.pause.assert_not_called()
        self.assertEqual(
            embed_title(interaction.response.send_message),
            "You are not in the same voice channel.",
        )

    async def test_pause_then_resume(self) -> None:
        await self.press("0")

        self.state.voice.pause.assert_called_once()
        self.assertEqual(self.button("0").label, "Resume")

        self.state.voice.is_playing.return_value = False
        self.state.voice.is_paused.return_value = True
        interaction = await self.press("0")

        self.state.voice.resume.assert_called_once()
        self.assertEqual(self.button("0").label, "Pause")
        interaction.edit_original_response.assert_awaited_with(view=self.view)

    async def test_loop_toggle_relabels(self) -> None:
        await self.press("3")

        self.assertTrue(self.state.loop)
        self.assertEqual(self.button("3").label, "Disable Looping")

    async def test_loop_queue_toggle_requeues(self) -> None:
        await self.press("4")

        self.assertTrue(self.state.loop_queue)
        self.assertEqual(self.state.songs[0]["title"], "Song")
        self.assertEqual(self.button("4").label, "Disable Loop Queue")

    async def test_queue_empty(self) -> None:
        self.state.current = None

        interaction = await self.press("5")

        self.assertEqual(embed_title(interaction.response.send_message), "Empty queue.")

    @mock.patch("time.time", return_value=1000.0)
    async def test_queue_shows_first_page(self, _time) -> None:
        interaction = await self.press("5")

        embed = interaction.response.send_message.call_args.kwargs["embed"]
        self.assertEqual(embed.title, "Currently Playing")
        self.assertEqual(embed.footer.text, "Viewing page 1/1")

    def approve_after_wait(self) -> mock.AsyncMock:
        async def fake_sleep(_seconds):
            pass

        return mock.AsyncMock(side_effect=fake_sleep)

    async def test_skip_vote_posts_in_channel(self) -> None:
        with mock.patch("asyncio.sleep", self.approve_after_wait()):
            interaction = await self.press("1")

        sent = interaction.channel.send
        self.assertEqual(sent.call_args.kwargs["embed"].title, "Skip current song?")
        self.state.skip.assert_called_once()
        sent.return_value.delete.assert_awaited_once()

    async def test_stop_vote_clears_queue(self) -> None:
        await self.state.songs.put({"title": "next"})

        with mock.patch("asyncio.sleep", self.approve_after_wait()):
            interaction = await self.press("2")

        self.assertEqual(
            interaction.channel.send.call_args.kwargs["embed"].title,
            "Stop current queue?",
        )
        self.assertEqual(len(self.state.songs), 0)
        self.state.stop.assert_awaited_once()


class TestSearchMenu(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music import search_view
        from usagiBot.cogs.Music.sources import YTDLSource

        self.search_view = search_view
        self.YTDLSource = YTDLSource
        self.bot = make_bot()
        self.ctx = make_ctx()
        self.ctx.guild.voice_client = None
        self.results = [
            {"title": "One", "duration": "1 minutes", "url": YOUTUBE_URL, "index": 0},
            {"title": "Two", "duration": "Unknown", "url": "https://youtu.be/2", "index": 1},
        ]

    async def asyncSetUp(self) -> None:
        self.view = self.search_view.SearchView(self.bot, self.results, self.ctx)
        self.menu = self.view.children[0]

    async def pick(self, value: str, **extract) -> mock.MagicMock:
        interaction = make_interaction()
        self.menu._selected_values = [value]
        self.menu._interaction = interaction
        with mock.patch.object(self.YTDLSource.ytdl, "extract_info", **extract):
            await self.menu.callback(interaction)
        return interaction

    def statuses(self, interaction) -> list:
        return embed_titles(interaction.followup.edit_message)

    async def test_options(self) -> None:
        labels = [option.label for option in self.menu.options]
        self.assertEqual(labels, ["One", "Two", "Cancel"])
        self.assertEqual(self.menu.options[1].description, "Duration: Unknown")

    async def test_cancel(self) -> None:
        interaction = await self.pick("11")

        self.assertTrue(self.menu.completed)
        self.assertEqual(embed_title(interaction.response.edit_message), "Cancelled")

    async def test_pick_enqueues_song(self) -> None:
        data = {"webpage_url": YOUTUBE_URL, "title": "One", "duration": 60}

        interaction = await self.pick("0", return_value=data)

        self.assertEqual(
            interaction.response.edit_message.call_args.kwargs["embed"].description, "One"
        )
        self.assertEqual(
            self.statuses(interaction),
            [f"Searching for: **<{YOUTUBE_URL}>**", "Enqueued **One**"],
        )
        self.assertEqual(self.ctx.voice_state.songs[0]["title"], "One")
        self.assertTrue(self.menu.completed)

    async def test_pick_reports_extractor_error(self) -> None:
        interaction = await self.pick("1", side_effect=Exception("Video unavailable"))

        self.assertEqual(self.statuses(interaction)[-1], "Error: Video Unavailable")
        self.assertEqual(len(self.ctx.voice_state.songs), 0)

    async def test_author_left_voice(self) -> None:
        self.ctx.author.voice = None

        interaction = await self.pick("0")

        self.assertEqual(
            self.statuses(interaction),
            ["You are not connected to any voice channel or the same voice channel."],
        )

    async def test_bot_busy_elsewhere(self) -> None:
        self.ctx.guild.voice_client = mock.MagicMock()

        interaction = await self.pick("0")

        self.assertEqual(self.statuses(interaction), ["Bot is already in a voice channel."])

    async def test_joins_before_enqueue(self) -> None:
        self.ctx.voice_state.voice = None
        connected = mock.MagicMock()
        connected.channel = self.ctx.author.voice.channel
        self.ctx.author.voice.channel.connect.return_value = connected
        data = {"webpage_url": YOUTUBE_URL, "title": "One", "duration": 60}

        await self.pick("0", return_value=data)

        self.ctx.author.voice.channel.connect.assert_awaited_once()
        self.assertEqual(len(self.ctx.voice_state.songs), 1)

    async def test_join_failure_stops_quietly(self) -> None:
        self.ctx.voice_state.voice = None
        self.ctx.author.voice.channel.permissions_for.return_value.connect = False

        interaction = await self.pick("0")

        self.assertEqual(self.statuses(interaction), [])
        self.assertEqual(len(self.ctx.voice_state.songs), 0)

    async def test_author_in_other_channel_than_bot(self) -> None:
        self.ctx.voice_state.voice.channel = mock.MagicMock(name="elsewhere")

        interaction = await self.pick("0")

        self.assertEqual(
            self.statuses(interaction),
            ["You are not connected to any voice channel or the same voice channel."],
        )

    async def test_timeout_marks_message(self) -> None:
        self.view.message = mock.MagicMock()
        self.view.message.edit = mock.AsyncMock()

        await self.view.on_timeout()

        self.assertEqual(embed_title(self.view.message.edit), "Timed out")

    async def test_timeout_after_pick_is_silent(self) -> None:
        self.view.message = mock.MagicMock()
        self.view.message.edit = mock.AsyncMock()
        self.menu.completed = True

        await self.view.on_timeout()

        self.view.message.edit.assert_not_called()
