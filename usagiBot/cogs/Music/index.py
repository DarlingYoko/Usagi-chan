import asyncio
import functools
import logging
import re
import shutil
import time

import discord
from discord import SlashCommandGroup
from discord.ext import commands

from usagiBot.cogs.Music.music_utils import (
    check_user_in_voice,
    create_music_embed,
    get_audio_duration,
    join_voice_channel,
    parse_duration,
    parse_songs,
)
from usagiBot.cogs.Music.sources import YTDLError, YTDLSource, error_messages
from usagiBot.cogs.Music.views import SearchView, SkipVoteView, StopVoteView
from usagiBot.cogs.Music.voice_state import VoiceState
from usagiBot.env import BOT_OWNER
from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.src.UsagiUtils import get_embed

logger = logging.getLogger(__name__)

# Users in this set are allowed to use command "running-servers"
authors = (BOT_OWNER,)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    music = SlashCommandGroup(
        name="music",
        description="Listen any music from YouTube!",
    )

    # Get the voice state from the dictionary, create if it does not exist
    def get_voice_state(self, ctx):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx, self)
            self.voice_states[ctx.guild.id] = state
        # When invoking this function, check whether the audio player task is done
        # If it is done, recreate the task
        if state.audio_player and state.audio_player.done():
            state.recreate_bg_task(ctx, self)
        return state

    # Stop all async tasks for each voice state
    def cog_unload(self):
        for state in self.voice_states.values():
            # Leave the channel first or else unexpected behaviour will occur
            self.bot.loop.create_task(state.stop(leave=True))
        self.voice_states.clear()
        try:
            shutil.rmtree("./tempMusic")
        except Exception as e:
            logger.error("Couldn't remove tempMusic: %s", e)

    # All commands from this cog cannot be used in DM
    def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in DM channels.",
            )

        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    # Before invoking any commands, get the voice state first
    # Update the context object also
    async def cog_before_invoke(self, ctx):
        self.get_voice_state(ctx)._ctx = ctx
        ctx.voice_state = self.get_voice_state(ctx)
        ctx.debug = ctx.voice_state.debug
        ctx.ctx = {"channel": ctx.channel, "message": ctx.message, "ctx": ctx}
        ctx.from_play = False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Event-driven replacement for the old per-guild 1s polling tasks:
        tracks the bot's own connection state and starts/cancels the
        leave-when-alone timer.
        """
        state = self.voice_states.get(member.guild.id)
        if state is None:
            return

        if member.id == self.bot.user.id:
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

    @music.command(
        name="join",
        invoke_without_subcommand=True,
        description="Joins the current voice channel",
    )
    async def join(self, ctx):
        # Joins the channel

        # If the user is not in any voice channel, don't join
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.respond(
                embed=get_embed(
                    title="You are not connected to any voice channel or the same voice channel.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return False

        # If the bot is in the voice channel, check whether it is in the same voice channel or not
        if ctx.voice_client:
            if ctx.voice_client.channel.id != ctx.author.voice.channel.id:
                await ctx.respond(
                    embed=get_embed(
                        title="Bot is already in a voice channel.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
                return False
            else:
                if not ctx.from_play:
                    await ctx.respond(
                        embed=get_embed(
                            title="Bot is already in your voice channel.",
                            color=discord.Color.red(),
                        ),
                        ephemeral=True,
                    )
                    return False
                return True

        await join_voice_channel(ctx)

    @music.command(
        name="summon",
        description="Summon the bot to current voice channel (Requires Move Member permission)",
    )
    @discord.commands.option(
        name="channel",
        description="Choose channel to summon Usagi",
    )
    async def summon(self, ctx, channel: discord.VoiceChannel):
        # Only allow members with "Move member" permission to use this command
        if (
            not ctx.author.guild_permissions.move_members
            and ctx.author.id not in authors
        ):
            return await ctx.respond(
                embed=get_embed(
                    title='Only members with "Move Member" permission are allowed to use this command.',
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        # Summon the bot to another channel or the current channel

        destination = channel

        # Check permission
        if not destination.permissions_for(ctx.me).connect:
            return await ctx.respond(
                embed=get_embed(
                    title="No permission to join the voice channel!",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        # Move to the specific channel and update internal memory
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            msg = await ctx.respond(
                embed=get_embed(
                    title=f"Switched from **{ctx.voice_state.voice.channel}** to **{destination}**.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
            ctx.voice_state.voice = msg.guild.voice_client
        else:
            # Not in any channel, use connect instead
            ctx.voice_state.voice = await destination.connect()
            await ctx.respond(
                embed=get_embed(
                    title=f"Joined **{destination}**.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
        # If the channel is a stage channel, wait for 1 second and try to unmute itself
        if isinstance(ctx.voice_state.voice.channel, discord.StageChannel):
            try:
                await asyncio.sleep(1)
                await ctx.me.edit(suppress=False)
            except Exception as e:
                logger.error("Couldn't unmute self on stage: %s", e)
                await ctx.respond(
                    embed=get_embed(
                        title="I have no permission to speak! Please invite me to speak.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )

    @music.command(
        name="leave",
        description="Leave the voice channel",
    )
    async def leave(self, ctx):
        # Clears the queue and leave the channel

        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return

        if not ctx.voice_state.voice:
            return await ctx.respond(
                embed=get_embed(
                    title="Bot is not connected to any voice channel.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        await ctx.respond(
            embed=get_embed(
                title="Bot left the voice channel.", color=discord.Color.green()
            ),
            ephemeral=True,
        )
        # Leaves the channel and delete the data from memory
        await ctx.voice_state.stop(leave=True)
        del self.voice_states[ctx.guild.id]

    @music.command(
        name="now",
        description="Display current song",
    )
    async def now(self, ctx):
        # Display currently playing song
        if ctx.voice_state.current is None:
            return await ctx.respond(
                embed=get_embed(
                    title="There is no songs playing right now.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        await ctx.respond(
            embed=ctx.voice_state.current.create_embed("now"), ephemeral=True
        )

    @music.command(name="pause", description="Pause the song")
    async def pause(self, ctx):
        # Pauses the player
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return
        # If the bot is playing, pause it
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.respond(
                embed=get_embed(title="Music paused.", color=discord.Color.green()),
                ephemeral=True,
            )
            # Sets the pause time
            ctx.voice_state.current.pause_time = time.time()
            ctx.voice_state.current.paused = True
        else:
            await ctx.respond(
                embed=get_embed(
                    title="There is no songs playing right now.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

    @music.command(
        name="resume",
        description="Resume paused song",
    )
    async def resume(self, ctx):
        # Resumes the bot
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return
        # If the bot is paused, resume it
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.respond(
                embed=get_embed(title="Music resumed.", color=discord.Color.green()),
                ephemeral=True,
            )
            # Updates internal data for handling song progress that was paused
            ctx.voice_state.current.pause_duration += (
                time.time() - ctx.voice_state.current.pause_time
            )
            ctx.voice_state.current.pause_time = 0
            ctx.voice_state.current.paused = False
        else:
            await ctx.respond(
                embed=get_embed(
                    title="There is no songs paused right now.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

    @music.command(
        name="stop",
        description="Remove all songs in queue and stop the bot",
    )
    async def stop(self, ctx):
        # Stops the bot and clears the queue
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return

        await ctx.defer()

        vote_view = StopVoteView(
            self.bot,
            ctx.voice_state,
            {"agree": [ctx.user], "disagree": []},
        )
        await ctx.send_followup(
            embed=get_embed(
                title="Stop current queue?",
                description="Votes to Stop - 1",
            ),
            view=vote_view,
        )
        await asyncio.sleep(10)
        if vote_view.votes > 0:
            await ctx.edit(
                embed=get_embed(title="Stop approved", color=discord.Color.green()),
                view=None,
            )
            ctx.voice_state.songs.clear()

            if ctx.voice_state.is_playing:
                await ctx.voice_state.stop()
                ctx.voice_state.stopped = True
                await ctx.respond(
                    embed=get_embed(title="Music stopped", color=discord.Color.green()),
                    ephemeral=True,
                )
        else:
            await ctx.edit(
                embed=get_embed(title="Stop canceled", color=discord.Color.red()),
                view=None,
            )
        await ctx.delete(delay=10)

    @music.command(
        name="skip",
        description="Skip current song",
    )
    async def skip(self, ctx):
        # Skips the current song
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return

        if not ctx.voice_state.is_playing:
            return await ctx.respond(
                embed=get_embed(
                    title="There is no songs playing right now.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        await ctx.defer()

        vote_view = SkipVoteView(
            self.bot,
            ctx.voice_state,
            {"agree": [ctx.user], "disagree": []},
        )
        await ctx.send_followup(
            embed=get_embed(
                title="Skip current song?",
                description=f"```{ctx.voice_state.current.source.title}```\nVotes to skip - 1",
            ),
            view=vote_view,
        )
        await asyncio.sleep(10)
        if vote_view.votes > 0:
            await ctx.edit(
                embed=get_embed(title="Skip approved", color=discord.Color.green()),
                view=None,
            )
            ctx.voice_state.skip()
        else:
            await ctx.edit(
                embed=get_embed(title="Skip canceled", color=discord.Color.red()),
                view=None,
            )

        await ctx.delete(delay=10)

    @music.command(name="queue", description="Show song queue")
    @discord.commands.option(
        name="page",
        description="Choose page of queue.",
    )
    async def queue(self, ctx, page: int):
        # Shows the queue, add page number to view different pages
        if page < 1:
            page = 1
        if len(ctx.voice_state.songs) == 0 and ctx.voice_state.current is None:
            return await ctx.respond(
                embed=get_embed(title="Empty queue.", color=discord.Color.red()),
                ephemeral=True,
            )

        # Invoking queue while the bot is retrieving another song will cause error, wait for 1 second
        while ctx.voice_state.current is None or isinstance(
            ctx.voice_state.current, dict
        ):
            await asyncio.sleep(1)
        return await ctx.respond(
            embed=create_music_embed(ctx, page),
            ephemeral=True,
        )

    @music.command(name="shuffle", description="Shuffle the song queue")
    async def shuffle(self, ctx):
        # Shuffles the queue
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return
        if len(ctx.voice_state.songs) == 0:
            return await ctx.respond(
                embed=get_embed(title="Empty queue.", color=discord.Color.red()),
                ephemeral=True,
            )

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
    async def remove(self, ctx, index: int):
        if index < 1:
            return await ctx.respond(
                embed=get_embed(
                    title="Please provide a valid song number in queue to remove.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return
        if ctx.voice_state.voice.channel != ctx.author.voice.channel:
            return
        if len(ctx.voice_state.songs) == 0:
            return await ctx.respond(
                embed=get_embed(title="Empty queue.", color=discord.Color.red()),
                ephemeral=True,
            )
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
    async def loop(self, ctx):
        # Toggle the looping of the current song
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return

        if ctx.voice_state.voice.channel != ctx.author.voice.channel:
            return

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.respond(
            embed=get_embed(
                title=(
                    "Enabled looping" if ctx.voice_state.loop else "Disabled looping"
                ),
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    @music.command(
        name="play",
        description="Plays a song or a playlist",
    )
    @discord.commands.option(
        name="link",
        description="Enter music link!",
    )
    async def play(self, ctx, link: str):
        # Plays a song, mostly from YouTube
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        # Joins the channel if it hasn't
        if not ctx.voice_state.voice:
            ctx.from_play = True
            await self.join(ctx)
        # Errors may occur while joining the channel, if the voice is None, don't continue
        if not ctx.voice_state.voice:
            return
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                return await ctx.respond(
                    embed=get_embed(
                        title="Bot is already in a voice channel.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )

        loop = self.bot.loop
        try:
            msg = await ctx.respond(
                embed=get_embed(
                    title=f"Searching for: **<{link}>**",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
            if isinstance(msg, discord.WebhookMessage):
                respond = msg.edit
            else:
                respond = msg.edit_original_response
            # Supports playing a playlist but it must be like https://youtube.com/playlist?
            if "/playlist?" in link and ("youtu.be" in link or "youtube.com" in link):
                partial = functools.partial(
                    YTDLSource.ytdl_playlist.extract_info, link, download=False
                )
                data = await loop.run_in_executor(None, partial)
                if data is None:
                    return await respond(
                        embed=get_embed(
                            title=f"Couldn't find anything that matches `{link}`",
                            color=discord.Color.red(),
                        )
                    )

                playlist = await parse_songs(ctx, data)
                await respond(
                    embed=get_embed(
                        title=f"Enqueued **{len(playlist)}** songs",
                        color=discord.Color.green(),
                    )
                )
            else:
                # Just a single song
                try:
                    domain = link.split("/")[2]
                except IndexError:
                    domain = "youtube"
                if "youtube" not in domain and "youtu.be" not in domain:
                    # Direct link or another site
                    try:
                        partial = functools.partial(
                            YTDLSource.ytdl.extract_info, link, download=False
                        )
                        data = await loop.run_in_executor(None, partial)
                        if "entries" in data:
                            if len(data["entries"]) > 0:
                                data = data["entries"][0]
                            else:
                                return await respond(
                                    embed=get_embed(
                                        title=f"Couldn't find anything that matches `{link}`",
                                        color=discord.Color.red(),
                                    )
                                )
                        title = data["title"]
                        if "duration" in data:
                            await ctx.voice_state.songs.put(
                                {
                                    "url": link,
                                    "title": title,
                                    "user": ctx.author,
                                    "duration": int(float(data["duration"])),
                                    "realurl": data["url"],
                                }
                            )
                        else:
                            await ctx.voice_state.songs.put(
                                {
                                    "url": link,
                                    "title": title,
                                    "user": ctx.author,
                                    "duration": await get_audio_duration(link),
                                    "realurl": data["url"],
                                }
                            )
                    except Exception as e:
                        logger.error("Couldn't enqueue direct link %r: %s", link, e)
                        return await respond(
                            embed=get_embed(
                                title="Unable to add this song, maybe it is not an audio file?",
                                color=discord.Color.red(),
                            )
                        )
                    await respond(
                        embed=get_embed(
                            title="Enqueued **{0}**".format(title.replace("_", "\\_")),
                            color=discord.Color.green(),
                        )
                    )
                else:
                    try:
                        partial = functools.partial(
                            YTDLSource.ytdl.extract_info, link, download=False
                        )
                        data = await loop.run_in_executor(None, partial)
                    except Exception as e:
                        # Get the error message from the dictionary, if it doesn't exist in dict, return the original
                        # error message
                        message = error_messages.get(str(e), str(e))
                        return await respond(
                            embed=get_embed(
                                title=f"Error: {message}",
                                color=discord.Color.red(),
                            )
                        )
                    if "entries" in data:
                        if len(data["entries"]) > 0:
                            data = data["entries"][0]
                        else:
                            return await respond(
                                embed=get_embed(
                                    title=f"Couldn't find anything that matches `{link}`",
                                    color=discord.Color.red(),
                                )
                            )
                    # Add the song to the pending list
                    try:
                        duration = int(data["duration"])
                    except Exception as e:
                        logger.error("Couldn't parse duration: %s", e)
                        duration = 0
                    await ctx.voice_state.songs.put(
                        {
                            "url": data["webpage_url"],
                            "title": data["title"],
                            "user": ctx.author,
                            "duration": duration,
                        }
                    )
                    await respond(
                        embed=get_embed(
                            title=f"Enqueued **{data['title']}**",
                            color=discord.Color.green(),
                        )
                    )
            ctx.voice_state.stopped = False
        except YTDLError as e:
            await ctx.respond(
                embed=get_embed(
                    title=f"Error: {str(e)}",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

    @music.command(name="search", description="Search a song from Youtube")
    @discord.commands.option(
        name="keyword",
        description="Search any music/video in YouTube.",
    )
    async def search(self, ctx, keyword: str):
        # Search from YouTube and returns 10 songs
        original_keyword = keyword
        keyword = "ytsearch10:" + keyword
        partial = functools.partial(
            YTDLSource.ytdl_playlist.extract_info, keyword, download=False
        )
        data = await self.bot.loop.run_in_executor(None, partial)
        result = []
        # Get 10 songs from the result
        for index, entry in enumerate(data["entries"]):
            try:
                duration = parse_duration(int(entry.get("duration")))
            except Exception as e:
                logger.error("Couldn't parse duration: %s", e)
                duration = "Unknown"
            result.append(
                {
                    "title": entry.get("title"),
                    "duration": duration,
                    "url": entry.get(
                        "webpage_url", "https://youtu.be/" + entry.get("id")
                    ),
                    "index": index,
                }
            )
        embed = get_embed(
            title=f"Search results of {original_keyword}",
            description="Please select the search result by selecting the option in the menu",
            color=discord.Color.green(),
        )
        # For each song, combine the details to a string
        for count, entry in enumerate(result):
            embed.add_field(
                name=f"{count + 1}. {entry['title']}",
                value=f"[Link]({entry['url']})\nDuration: {entry['duration']}\n",
                inline=False,
            )
        # Send the message of the results
        view = SearchView(self.bot, result, ctx, self)

        message = await ctx.respond(embed=embed, view=view, ephemeral=True)
        if isinstance(message, discord.Interaction):
            message = await message.original_response()
        view.message = message

    @music.command(
        name="musicreload",
        description="Reload the music bot",
    )
    async def musicreload(self, ctx):
        # Disconnect the bot and delete voice state from internal memory in case something goes wrong
        try:
            await ctx.voice_state.stop(leave=True)
        except Exception as e:
            logger.error("musicreload stop failed: %s", e)
        try:
            await ctx.voice_client.disconnect()
        except Exception as e:
            logger.error("musicreload disconnect failed: %s", e)
        try:
            ctx.voice_client.cleanup()
        except Exception as e:
            logger.error("musicreload clean_up failed: %s", e)
        self.voice_states.pop(ctx.guild.id, None)
        await ctx.respond(
            embed=get_embed(title="Music bot reloaded.", color=discord.Color.green()),
            ephemeral=True,
        )

    @music.command(
        name="loopqueue",
        description="Toggle looping for current queue",
    )
    async def loopqueue(self, ctx):
        # Loops the queue
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return

        # Inverse the boolean
        ctx.voice_state.loop_queue = not ctx.voice_state.loop_queue
        # The current song will also loop if loop queue enabled
        try:
            if ctx.voice_state.loop_queue:
                await ctx.voice_state.songs.put(
                    {
                        "url": ctx.voice_state.current.source.url,
                        "title": ctx.voice_state.current.source.title,
                        "user": ctx.voice_state.current.source.requester,
                        "duration": ctx.voice_state.current.source.duration_int,
                    }
                )
        except Exception as e:
            logger.error("Couldn't requeue current song: %s", e)
        await ctx.respond(
            embed=get_embed(
                title=(
                    "Enabled loop queue"
                    if ctx.voice_state.loop_queue
                    else "Disabled loop queue"
                ),
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    @music.command(name="seek", description="Seek to a specific point")
    @discord.commands.option(
        name="seconds",
        description="Seek to any place in song. '+' For seek forward, '-' For seek back",
    )
    async def seek(self, ctx, seconds: str):
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.seeking = True
            try:
                # Parse which hour, minute, second to seek to
                regexp = re.compile("([0-9]*h)?([0-9]*m)?([0-9]*s)?")
                if regexp.match(seconds).group() != "":
                    hour_regexp = re.compile("([0-9]+h)").search(seconds)
                    hour_regexp = (
                        int(hour_regexp.group()[0:-1]) if hour_regexp is not None else 0
                    )

                    minute_regexp = re.compile("([0-9]+m)").search(seconds)
                    minute_regexp = (
                        int(minute_regexp.group()[0:-1])
                        if minute_regexp is not None
                        else 0
                    )

                    second_regexp = re.compile("([0-9]+s)").search(seconds)
                    second_regexp = (
                        int(second_regexp.group()[0:-1])
                        if second_regexp is not None
                        else 0
                    )

                    seconds = hour_regexp * 60 * 60 + minute_regexp * 60 + second_regexp
                elif seconds[0] == "+":
                    # Fast-forward by x seconds
                    if ctx.voice_state.current.paused:
                        ctx.voice_state.current.pause_duration += (
                            time.time() - ctx.voice_state.current.pause_time
                        )
                        ctx.voice_state.current.pause_time = time.time()
                    seconds = int(
                        time.time()
                        - ctx.voice_state.current.start_time
                        - ctx.voice_state.current.pause_duration
                    ) + int(seconds[1:])
                elif seconds[0] == "-":
                    # Backward by x seconds
                    if ctx.voice_state.current.paused:
                        ctx.voice_state.current.pause_duration += (
                            time.time() - ctx.voice_state.current.pause_time
                        )
                        ctx.voice_state.current.pause_time = time.time()
                    seconds = max(
                        (
                            int(
                                time.time()
                                - ctx.voice_state.current.start_time
                                - ctx.voice_state.current.pause_duration
                            )
                            - int(seconds[1:])
                        ),
                        0,
                    )
                else:
                    seconds = int(seconds)
            except Exception as e:
                logger.error("Couldn't parse seek seconds %r: %s", seconds, e)
                return await ctx.respond(
                    embed=get_embed(
                        title="Unable to parse seconds to seek!",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            ctx.voice_state.seek_time = seconds
            current = ctx.voice_state.current
            try:
                domain = current.source.url.split("/")[2]
            except Exception as e:
                logger.error("Couldn't parse domain for seek: %s", e)
                domain = ""
            await ctx.voice_state.seek(
                seconds,
                "local@" in current.source.url,
                not ("youtube" in domain or "youtu.be" in domain),
            )
            await ctx.respond(
                embed=get_embed(
                    title=f"Seek to {seconds}s",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
        else:
            await ctx.respond(
                embed=get_embed(
                    title="There is no songs playing right now.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(Music(bot))
