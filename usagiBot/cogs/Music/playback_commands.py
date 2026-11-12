"""/music play, search, now, pause, resume, seek, skip, stop."""
import functools
import logging
import time
from typing import Any, Awaitable, Callable, List

import discord
from discord.ext import commands

from usagiBot.cogs.Music.enqueue import enqueue_link
from usagiBot.cogs.Music.context import MusicContext
from usagiBot.cogs.Music.group import music
from usagiBot.cogs.Music.music_utils import check_user_in_voice, parse_duration
from usagiBot.cogs.Music.playback import pause_song, resume_song, stop_queue
from usagiBot.cogs.Music.search_view import SearchView
from usagiBot.cogs.Music.seek import parse_seek_target, source_kind
from usagiBot.cogs.Music.sources import YTDLSource
from usagiBot.cogs.Music.voice_commands import respond_error
from usagiBot.cogs.Music.voting import SkipVoteView, StopVoteView, run_vote
from usagiBot.src.UsagiUtils import get_embed

logger = logging.getLogger(__name__)

NOTHING_PLAYING = "There is no songs playing right now."
SEARCH_RESULTS = 10


def search_results(data: dict) -> List[dict]:
    """Flatten yt-dlp search entries into what the select menu shows."""
    results = []
    for index, entry in enumerate(data["entries"]):
        try:
            duration = parse_duration(int(entry.get("duration")))
        except (TypeError, ValueError):
            duration = "Unknown"
        results.append(
            {
                "title": entry.get("title"),
                "duration": duration,
                "url": entry.get("webpage_url") or f"https://youtu.be/{entry.get('id')}",
                "index": index,
            }
        )
    return results


class PlaybackCommands:
    """Mixin for the Music cog; VoiceCommands provides connect_author_channel."""

    bot: commands.Bot
    # annotation only: the implementation comes from VoiceCommands via the MRO
    connect_author_channel: Callable[[MusicContext], Awaitable[bool]]

    @music.command(
        name="play",
        description="Plays a song or a playlist",
    )
    @discord.commands.option(
        name="link",
        description="Enter music link!",
    )
    async def play(self, ctx: MusicContext, link: str) -> None:
        """
        Queue a YouTube video/playlist, a direct audio link, or the first
        YouTube search hit for plain text.
        """
        if not ctx.voice_state.voice:
            ctx.from_play = True
            await self.connect_author_channel(ctx)
        # Joining may have failed (and already told the user why)
        if not ctx.voice_state.voice:
            return
        if not await check_user_in_voice(ctx):
            return
        author_voice = ctx.author.voice
        if (
            ctx.voice_client
            and author_voice
            and ctx.voice_client.channel != author_voice.channel
        ):
            return await respond_error(ctx, "Bot is already in a voice channel.")

        msg = await ctx.respond(
            embed=get_embed(
                title=f"Searching for: **<{link}>**",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )
        edit: Callable[..., Awaitable[Any]] = (
            msg.edit
            if isinstance(msg, discord.WebhookMessage)
            else msg.edit_original_response
        )

        result = await enqueue_link(self.bot.loop, ctx.voice_state, link, ctx.author)
        await edit(
            embed=get_embed(
                title=result.message,
                color=discord.Color.green() if result.ok else discord.Color.red(),
            )
        )

    @music.command(name="search", description="Search a song from Youtube")
    @discord.commands.option(
        name="keyword",
        description="Search any music/video in YouTube.",
    )
    async def search(self, ctx: MusicContext, keyword: str) -> None:
        partial = functools.partial(
            YTDLSource.ytdl_playlist.extract_info,
            f"ytsearch{SEARCH_RESULTS}:{keyword}",
            download=False,
        )
        data = await self.bot.loop.run_in_executor(None, partial)
        results = search_results(data)

        embed = get_embed(
            title=f"Search results of {keyword}",
            description="Please select the search result by selecting the option in the menu",
            color=discord.Color.green(),
        )
        for count, entry in enumerate(results, start=1):
            embed.add_field(
                name=f"{count}. {entry['title']}",
                value=f"[Link]({entry['url']})\nDuration: {entry['duration']}\n",
                inline=False,
            )
        view = SearchView(self.bot, results, ctx)

        response = await ctx.respond(embed=embed, view=view, ephemeral=True)
        view.message = (
            await response.original_response()
            if isinstance(response, discord.Interaction)
            else response
        )

    @music.command(
        name="now",
        description="Display current song",
    )
    async def now(self, ctx: MusicContext) -> None:
        if ctx.voice_state.current is None:
            return await respond_error(ctx, NOTHING_PLAYING)
        await ctx.respond(
            embed=ctx.voice_state.current.create_embed("now"), ephemeral=True
        )

    @music.command(name="pause", description="Pause the song")
    async def pause(self, ctx: MusicContext) -> None:
        if not await check_user_in_voice(ctx):
            return
        if not pause_song(ctx.voice_state):
            return await respond_error(ctx, NOTHING_PLAYING)
        await ctx.respond(
            embed=get_embed(title="Music paused.", color=discord.Color.green()),
            ephemeral=True,
        )

    @music.command(
        name="resume",
        description="Resume paused song",
    )
    async def resume(self, ctx: MusicContext) -> None:
        if not await check_user_in_voice(ctx):
            return
        if not resume_song(ctx.voice_state):
            return await respond_error(ctx, "There is no songs paused right now.")
        await ctx.respond(
            embed=get_embed(title="Music resumed.", color=discord.Color.green()),
            ephemeral=True,
        )

    @music.command(name="seek", description="Seek to a specific point")
    @discord.commands.option(
        name="seconds",
        description="Seek to any place in song. '+' For seek forward, '-' For seek back",
    )
    async def seek(self, ctx: MusicContext, seconds: str) -> None:
        if not await check_user_in_voice(ctx):
            return
        state = ctx.voice_state
        if not (state.is_playing and state.voice and state.voice.is_playing()):
            return await respond_error(ctx, NOTHING_PLAYING)

        try:
            target = parse_seek_target(seconds, state.current, time.time())
        except ValueError as e:
            logger.info("Rejected seek value: %s", e)
            return await respond_error(ctx, "Unable to parse seconds to seek!")

        state.seeking = True
        state.seek_time = target
        is_local, is_direct_link = source_kind(state.current.source.url)
        await state.seek(target, is_local, is_direct_link)
        await ctx.respond(
            embed=get_embed(title=f"Seek to {target}s", color=discord.Color.green()),
            ephemeral=True,
        )

    @music.command(
        name="skip",
        description="Skip current song",
    )
    async def skip(self, ctx: MusicContext) -> None:
        if not await check_user_in_voice(ctx):
            return
        if not ctx.voice_state.is_playing:
            return await respond_error(ctx, NOTHING_PLAYING)

        await ctx.defer()

        async def skip_song() -> None:
            ctx.voice_state.skip()

        await run_vote(
            SkipVoteView(self.bot, ctx.voice_state, ctx.user),
            ctx.send_followup,
            skip_song,
        )

    @music.command(
        name="stop",
        description="Remove all songs in queue and stop the bot",
    )
    async def stop(self, ctx: MusicContext) -> None:
        if not await check_user_in_voice(ctx):
            return

        await ctx.defer()

        async def stop_playing() -> None:
            if await stop_queue(ctx.voice_state):
                await ctx.respond(
                    embed=get_embed(title="Music stopped", color=discord.Color.green()),
                    ephemeral=True,
                )

        await run_vote(
            StopVoteView(self.bot, ctx.voice_state, ctx.user),
            ctx.send_followup,
            stop_playing,
        )
