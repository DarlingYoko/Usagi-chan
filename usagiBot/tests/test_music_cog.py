from unittest import IsolatedAsyncioTestCase
from unittest import mock

from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *


class TestMusicModuleWiring(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music import index as music_index
        from usagiBot.cogs.Music import voice_state as music_voice_state

        self.music_index = music_index
        self.music_voice_state = music_voice_state

    def test_all_commands_survived_the_split(self) -> None:
        names = {
            command.name for command in self.music_index.Music.music.subcommands
        }
        expected = {
            "join", "summon", "leave", "now", "pause", "resume", "stop",
            "skip", "queue", "shuffle", "remove", "loop", "play", "search",
            "musicreload", "loopqueue", "seek",
        }
        self.assertEqual(expected - names, set())

    async def test_mixin_commands_bind_to_the_cog(self) -> None:
        import discord

        bot = discord.Bot()
        cog = self.music_index.Music(bot)
        bot.add_cog(cog)

        group = next(command for command in cog.get_commands() if command.name == "music")
        self.assertEqual(len(group.subcommands), 17)
        for command in group.subcommands:
            self.assertIs(command.cog, cog, command.name)
        listeners = [name for name, _ in cog.get_listeners()]
        self.assertIn("on_voice_state_update", listeners)

    def test_polling_loops_are_gone(self) -> None:
        VoiceState = self.music_voice_state.VoiceState

        self.assertFalse(hasattr(VoiceState, "update_voice_state"))
        self.assertFalse(hasattr(VoiceState, "check_user_listening"))
        self.assertFalse(hasattr(VoiceState, "update_volume"))
        self.assertTrue(hasattr(VoiceState, "start_alone_timer"))
        self.assertTrue(hasattr(VoiceState, "cancel_alone_timer"))

    def test_cog_listens_to_voice_state_updates(self) -> None:
        listener = getattr(self.music_index.Music, "on_voice_state_update", None)

        self.assertIsNotNone(listener)
        self.assertTrue(getattr(listener, "__cog_listener__", False))


class TestVoiceStateVolume(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music.voice_state import VoiceState

        self.VoiceState = VoiceState

    def test_volume_setter_applies_to_current_source(self) -> None:
        state = self.VoiceState.__new__(self.VoiceState)
        state._volume = 0.5
        state.current = mock.MagicMock()

        state.volume = 0.8

        self.assertEqual(state._volume, 0.8)
        self.assertEqual(state.current.source.volume, 0.8)
