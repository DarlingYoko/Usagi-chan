"""Buttons under the now-playing message."""
import asyncio
from typing import Any

import discord

from usagiBot.cogs.Music.music_utils import (
    check_user_in_voice_interaction,
    create_music_embed,
)
from usagiBot.cogs.Music.playback import (
    pause_song,
    resume_song,
    stop_queue,
    toggle_loop_queue,
)
from usagiBot.cogs.Music.voting import SkipVoteView, StopVoteView, run_vote
from usagiBot.src.UsagiUtils import get_embed

PAUSE_ID, SKIP_ID, STOP_ID, LOOP_ID, LOOP_QUEUE_ID, QUEUE_ID = "0", "1", "2", "3", "4", "5"


def get_button(view: discord.ui.View, custom_id: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and child.custom_id == custom_id:
            return child
    raise KeyError(custom_id)


def set_loop_btns(view: "PlayerControlView") -> None:
    get_button(view, LOOP_ID).label = (
        "Disable Looping" if view.voice_state.loop else "Enable Looping"
    )
    get_button(view, LOOP_QUEUE_ID).label = (
        "Disable Loop Queue" if view.voice_state.loop_queue else "Enable Loop Queue"
    )


class PlayerControlView(discord.ui.View):
    def __init__(self, bot: discord.Bot, voice_state: Any) -> None:
        self.bot = bot
        self.voice_state = voice_state
        super().__init__(timeout=None)
        set_loop_btns(self)

    def _set_pause_button(self, paused: bool) -> None:
        button = get_button(self, PAUSE_ID)
        button.emoji = "▶" if paused else "⏸"
        button.label = "Resume" if paused else "Pause"

    @discord.ui.button(
        label="Pause",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id=PAUSE_ID,
        emoji="⏸",
    )
    async def pause(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        if not await check_user_in_voice_interaction(self, interaction):
            return
        await interaction.response.defer()
        if pause_song(self.voice_state):
            self._set_pause_button(paused=True)
        elif resume_song(self.voice_state):
            self._set_pause_button(paused=False)
        await interaction.edit_original_response(view=self)

    @discord.ui.button(
        label="Skip",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id=SKIP_ID,
        emoji="⏭",
    )
    async def skip(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        channel = interaction.channel
        if channel is None or not await check_user_in_voice_interaction(
            self, interaction
        ):
            return
        await interaction.response.defer()

        async def skip_song() -> None:
            self.voice_state.skip()

        await run_vote(
            SkipVoteView(self.bot, self.voice_state, interaction.user),
            channel.send,
            skip_song,
        )

    @discord.ui.button(
        label="Stop",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id=STOP_ID,
        emoji="⏹",
    )
    # not "stop": that would shadow discord.ui.View.stop()
    async def stop_btn(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        channel = interaction.channel
        if channel is None or not await check_user_in_voice_interaction(
            self, interaction
        ):
            return
        await interaction.response.defer()

        async def stop_playing() -> None:
            await stop_queue(self.voice_state)

        await run_vote(
            StopVoteView(self.bot, self.voice_state, interaction.user),
            channel.send,
            stop_playing,
        )

    @discord.ui.button(
        label="Loop",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id=LOOP_ID,
        emoji="🔂",
    )
    async def loop(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        if not await check_user_in_voice_interaction(self, interaction):
            return
        await interaction.response.defer()
        self.voice_state.loop = not self.voice_state.loop
        set_loop_btns(self)
        await interaction.edit_original_response(view=self)

    @discord.ui.button(
        label="Queue",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id=QUEUE_ID,
        emoji="📜",
    )
    async def queue(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        if len(self.voice_state.songs) == 0 and self.voice_state.current is None:
            await interaction.response.send_message(
                embed=get_embed(title="Empty queue.", color=discord.Color.red()),
                ephemeral=True,
            )
            return

        # The player may be between songs while it fetches the next source
        while self.voice_state.current is None or isinstance(
            self.voice_state.current, dict
        ):
            await asyncio.sleep(1)
        await interaction.response.send_message(
            embed=create_music_embed(self, 1),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Loop Queue",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id=LOOP_QUEUE_ID,
        emoji="🔂",
    )
    async def loopqueue(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        if not await check_user_in_voice_interaction(self, interaction):
            return
        await interaction.response.defer()
        await toggle_loop_queue(self.voice_state)
        set_loop_btns(self)
        await interaction.edit_original_response(view=self)
