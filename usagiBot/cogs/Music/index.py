"""Music cog: per-guild voice state lifecycle; slash commands live in the mixins."""
import logging
from typing import Any

import discord
from discord.ext import commands

from usagiBot.cogs.Music.group import music
from usagiBot.cogs.Music.playback_commands import PlaybackCommands
from usagiBot.cogs.Music.queue_commands import QueueCommands
from usagiBot.cogs.Music.voice_commands import VoiceCommands
from usagiBot.cogs.Music.voice_state import VoiceState
from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError

logger = logging.getLogger(__name__)


class Music(VoiceCommands, PlaybackCommands, QueueCommands, commands.Cog):
    music = music

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.voice_states: dict = {}

    def get_voice_state(self, ctx: Any) -> VoiceState:
        """The guild's VoiceState, created on first use; a dead player task is restarted."""
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx, self)
            self.voice_states[ctx.guild.id] = state
        if state.audio_player and state.audio_player.done():
            state.recreate_bg_task(ctx, self)
        return state

    def cog_unload(self) -> None:
        for state in self.voice_states.values():
            # Leave the channel first or else unexpected behaviour will occur
            self.bot.loop.create_task(state.stop(leave=True))
        self.voice_states.clear()

    def cog_check(self, ctx: Any) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in DM channels.",
            )

        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    async def cog_before_invoke(self, ctx: Any) -> None:
        # Commands read the guild's player through ctx.voice_state
        state = self.get_voice_state(ctx)
        state._ctx = ctx
        ctx.voice_state = state
        ctx.debug = state.debug
        ctx.ctx = {"channel": ctx.channel, "message": ctx.message, "ctx": ctx}
        ctx.from_play = False

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """
        Tracks the bot's own connection and starts/cancels the
        leave-when-alone timer as listeners come and go.
        """
        state = self.voice_states.get(member.guild.id)
        if state is None:
            return

        bot_user = self.bot.user
        if bot_user is not None and member.id == bot_user.id:
            if after.channel is None:
                # Kicked or disconnected — clean everything up
                await state.stop(leave=True)
                self.voice_states.pop(member.guild.id, None)
            else:
                # Joined or moved — refresh the voice client reference
                state.voice = member.guild.voice_client
                if len(after.channel.members) == 1:
                    state.start_alone_timer()
                else:
                    state.cancel_alone_timer()
            return

        if not state.voice or not state.voice.channel:
            return
        channel = state.voice.channel
        if after.channel == channel:
            state.cancel_alone_timer()
        elif before.channel == channel and len(channel.members) == 1:
            state.start_alone_timer()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))
