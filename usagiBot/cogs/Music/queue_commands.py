"""/music queue, shuffle, remove, loop, loopqueue."""
import asyncio

import discord

from usagiBot.cogs.Music.context import MusicContext
from usagiBot.cogs.Music.group import music
from usagiBot.cogs.Music.music_utils import check_user_in_voice, create_music_embed
from usagiBot.cogs.Music.playback import toggle_loop_queue
from usagiBot.cogs.Music.voice_commands import respond_error
from usagiBot.src.UsagiUtils import get_embed

EMPTY_QUEUE = "Empty queue."


class QueueCommands:
    """Mixin for the Music cog."""

    @music.command(name="queue", description="Show song queue")
    @discord.commands.option(
        name="page",
        description="Choose page of queue.",
    )
    async def queue(self, ctx: MusicContext, page: int) -> None:
        if len(ctx.voice_state.songs) == 0 and ctx.voice_state.current is None:
            return await respond_error(ctx, EMPTY_QUEUE)

        # The player may be between songs while it fetches the next source
        while ctx.voice_state.current is None or isinstance(
            ctx.voice_state.current, dict
        ):
            await asyncio.sleep(1)
        await ctx.respond(
            embed=create_music_embed(ctx, max(page, 1)),
            ephemeral=True,
        )

    @music.command(name="shuffle", description="Shuffle the song queue")
    async def shuffle(self, ctx: MusicContext) -> None:
        if not await check_user_in_voice(ctx):
            return
        if len(ctx.voice_state.songs) == 0:
            return await respond_error(ctx, EMPTY_QUEUE)

        ctx.voice_state.songs.shuffle()
        await ctx.respond(
            embed=get_embed(title="Song queue shuffled", color=discord.Color.green()),
            ephemeral=True,
        )

    @music.command(name="remove", description="Remove a song from queue")
    @discord.commands.option(
        name="index",
        description="Choose track to remove.",
    )
    async def remove(self, ctx: MusicContext, index: int) -> None:
        if index < 1:
            return await respond_error(
                ctx, "Please provide a valid song number in queue to remove."
            )
        if not await check_user_in_voice(ctx):
            return
        if len(ctx.voice_state.songs) == 0:
            return await respond_error(ctx, EMPTY_QUEUE)

        name = ctx.voice_state.songs[index - 1]
        ctx.voice_state.songs.remove(index - 1)
        await ctx.respond(
            embed=get_embed(
                title="Song removed.",
                description=f"{name}",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    @music.command(
        name="loop",
        description="Toggle looping for current song",
    )
    async def loop(self, ctx: MusicContext) -> None:
        if not await check_user_in_voice(ctx):
            return

        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.respond(
            embed=get_embed(
                title="Enabled looping" if ctx.voice_state.loop else "Disabled looping",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    @music.command(
        name="loopqueue",
        description="Toggle looping for current queue",
    )
    async def loopqueue(self, ctx: MusicContext) -> None:
        if not await check_user_in_voice(ctx):
            return

        enabled = await toggle_loop_queue(ctx.voice_state)
        await ctx.respond(
            embed=get_embed(
                title="Enabled loop queue" if enabled else "Disabled loop queue",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )
