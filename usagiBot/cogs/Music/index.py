import functools
import itertools
import math
import random

import yt_dlp as youtube_dl
from async_timeout import timeout
from discord import SlashCommandGroup

from usagiBot.cogs.Music.music_utils import *
from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.src.UsagiUtils import get_embed

import subprocess
import shutil
import re

useEmbed = True
# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ""

# Error messages for returning meaningfully error message to user
error_messages = {
    "ERROR: Sign in to confirm your age\nThis video may be inappropriate for some users.": "This video is "
                                                                                           "age-restricted",
    "Video unavailable": "Video Unavailable",
    "ERROR: Private video\nSign in if you've been granted access to this video": "This video is private video",
}

# Insert authors' id in here, user in this set is allowed to use command "running-servers"
authors = (290166276796448768,)


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class FFMPEGSource(discord.PCMVolumeTransformer):
    def __init__(
        self,
        ctx,
        source: discord.FFmpegPCMAudio,
        *,
        data: dict,
        volume: float = 0.5,
    ):
        super().__init__(source, volume)
        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")
        try:
            self.duration = parse_duration(int(data.get("duration")))
        except Exception as e:
            print("ERROR 1- ", e)
            self.duration = "Unknown"
        try:
            self.duration_raw = parse_duration_raw(int(data.get("duration")))
        except Exception as e:
            print("ERROR 2- ", e)
            self.duration = "Unknown"
        self.duration_int = int(data.get("duration"))

    def __str__(self):
        return f"**{self.title}**"

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    @classmethod
    async def create_source(
        cls,
        ctx,
        url: str,
        *,
        loop: [asyncio.BaseEventLoop, asyncio.AbstractEventLoop] = None,
        requester=None,
        seek=None,
    ):
        loop = loop or asyncio.get_event_loop()

        # Extract data with youtube-dl
        partial = functools.partial(cls.ytdl.extract_info, url, download=False)
        data = await loop.run_in_executor(None, partial)
        info = {
            "url": data["url"],
            "webpage_url": data["webpage_url"],
            "title": data["title"],
            "duration": data["duration"],
            "requester": requester,
        }
        return get_source(cls, ctx, seek, info)


class YTDLSource(discord.PCMVolumeTransformer):
    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)
    ytdl_playlist = youtube_dl.YoutubeDL(YTDL_OPTIONS_PLAYLIST)

    def __init__(
        self,
        ctx,
        source: discord.FFmpegPCMAudio,
        *,
        data: dict,
        volume: float = 0.5,
    ):
        super().__init__(source, volume)

        self.requester = data.get("requester")
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get("uploader")
        self.uploader_url = data.get("uploader_url")
        date = data.get("upload_date")
        self.upload_date = date[6:8] + "." + date[4:6] + "." + date[0:4]
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        try:
            self.duration = parse_duration(int(data.get("duration")))
        except Exception as e:
            print("ERROR 3- ", e)
            self.duration = "Unknown"
        try:
            self.duration_raw = parse_duration_raw(int(data.get("duration")))
        except Exception as e:
            print("ERROR 4- ", e)
            self.duration_raw = "Unknown"
        self.duration_int = int(data.get("duration"))
        self.tags = data.get("tags")
        self.url = data.get("webpage_url")
        self.views = data.get("view_count")
        self.likes = data.get("like_count")
        self.dislikes = data.get("dislike_count")
        self.stream_url = data.get("url")

    def __str__(self):
        return "**{0.title}** by **{0.uploader}**".format(self)

    @classmethod
    async def create_source(
        cls,
        ctx,
        search: str,
        *,
        loop: [asyncio.BaseEventLoop, asyncio.AbstractEventLoop] = None,
        requester=None,
        seek=None,
    ):
        loop = loop or asyncio.get_event_loop()

        # Extract data with youtube-dl
        partial = functools.partial(
            cls.ytdl.extract_info, search, download=False, process=False
        )
        data = await loop.run_in_executor(None, partial)

        # Return error if nothing can be found
        if data is None:
            return await ctx.respond(
                embed=get_embed(
                    title=f"Couldn't find anything that matches `{search}`",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        # process_info retrieves the first entry of the returned data, but the data could be the entry itself
        if "entries" not in data:
            process_info = data
        else:
            process_info = None
            for entry in data["entries"]:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                return await ctx.respond(
                    embed=get_embed(
                        title=f"Couldn't find anything that matches `{search}`",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )

        # Retrieve the video details
        webpage_url = process_info["webpage_url"]
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            return await ctx.respond(
                embed=get_embed(
                    title=f"Couldn't fetch `{webpage_url}`", color=discord.Color.red()
                ),
                ephemeral=True,
            )

        if "entries" not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info["entries"].pop(0)
                except IndexError:
                    return await ctx.respond(
                        embed=get_embed(
                            title=f"Couldn't find anything that matches `{webpage_url}`",
                            color=discord.Color.red(),
                        ),
                        ephemeral=True,
                    )

        # requester for saving the user who plays this song, shown in command now
        info["requester"] = requester
        return get_source(cls, ctx, seek, info)


class Song:
    __slots__ = (
        "source",
        "requester",
        "start_time",
        "pause_time",
        "pause_duration",
        "paused",
        "is_file",
        "is_direct_link",
        "time_invoke_seek",
    )

    # start_time stores when does the song start
    # pause_duration stores how long does the song being paused, updates when the song resumes
    # pause_time stores when does the song paused, used for calculating the pause_duration
    def __init__(self, source, is_file=False, is_direct_link=False):
        self.source = source
        self.requester = source.requester
        self.start_time = None
        self.pause_duration = 0
        self.pause_time = 0
        self.paused = False
        self.is_file = is_file
        self.is_direct_link = is_direct_link
        self.time_invoke_seek = -1

    def create_embed(self, status: str):
        # If a new song is being played, it will simply display how long the song is
        # But if the command now is being executed, it will show how long the song has been played
        if self.paused:
            self.pause_duration += time.time() - self.pause_time
            self.pause_time = time.time()
        embed = (
            get_embed(
                title="Now Playing",
                description=f"```css\n{self.source.title}\n```",
            )
            .add_field(
                name="Duration",
                value=(
                    self.source.duration
                    if status == "play"
                    else parse_duration_raw(
                        int(time.time() - self.start_time - self.pause_duration)
                    )
                    + "/"
                    + self.source.duration_raw
                ),
            )
            .add_field(name="Requested by", value=self.requester.mention)
        )
        # If it is not a file, it is a YouTube video
        if not self.is_file:
            embed.add_field(
                name="Uploader",
                value=f"[{self.source.uploader}]({self.source.uploader_url})",
            )
            embed.add_field(
                name="URL",
                value=f"[Click]({self.source.url})",
            )
            embed.set_thumbnail(url=self.source.thumbnail)
        if self.is_direct_link:
            embed.add_field(
                name="URL",
                value=f"[Click]({self.source.url})",
            )

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx, cog):
        self.bot = bot
        self._ctx = ctx
        self.me = None

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.next_song = None
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5

        self.audio_player = bot.loop.create_task(self.audio_player_task())
        self.skipped = False
        self.pause_time = 0.0
        self.pause_duration = 0.0
        self.seek_time = 0
        self.stopped = None
        self.start_time = None

        self.loop_queue = False
        self.seeking = False
        self.guild_id = ctx.guild.id

        self.voice_state_updater = bot.loop.create_task(self.update_voice_state())
        self.timer = 0
        self.volume_updater = None
        self.listener_task = None

        self.debug = {"debug": False, "channel": None, "debug_log": False}

        # Create a task for checking is the bot alone
        self.listener_task = self.bot.loop.create_task(self.check_user_listening())

        self.forbidden = False

        self.cog = cog

    def recreate_bg_task(self, ctx, cog):
        self.__init__(self.bot, ctx, cog)

    def __del__(self):
        if self.audio_player:
            self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    # Function for seeking
    async def seek(self, seconds, is_local, is_direct_link):
        # Stop the current playing song
        self.voice.stop()
        # Recreate ffmpeg object
        if is_local or is_direct_link:
            self.current = await self.create_song_source(
                self._ctx,
                self.current.source.url,
                title=self.current.source.title,
                requester=self.current.source.requester,
                seek=seconds,
            )
        else:
            self.current = await self.create_song_source(
                self._ctx,
                self.current.source.url,
                requester=self.current.source.requester,
                seek=seconds,
            )
        # Update volume
        self.current.source.volume = self._volume
        # Play the seeked song
        self.voice.play(self.current.source, after=self.play_next_song)
        self.current.time_invoke_seek = time.time()
        # Update the start_time since the song was seeked
        self.current.start_time = time.time() - self.seek_time
        self.volume_updater.cancel()
        self.volume_updater = self.bot.loop.create_task(self.update_volume())

    async def update_volume(self):
        # If it is not playing, don't check, also the task will be recreated when a new song is being played
        while self.is_playing:
            # Without sleep, it will cause lag (at least it lagged on my laptop)
            await asyncio.sleep(1)
            # If the volume is updated, update it
            if (
                not isinstance(self.current, dict)
                and not isinstance(self.current, str)
                and self.current
                and self.current.source.volume != self._volume
            ):
                self.current.source.volume = self._volume

    async def create_song_source(self, ctx, url, title=None, requester=None, seek=None):
        try:
            domain = url.split("/")[2]
        except Exception as e:
            print("ERROR 5- ", e)
            domain = ""
        if "local@" in url:
            # It is a local file
            url = url[6:]
            try:
                # Try to get the duration of the uploaded file
                duration = str(
                    int(
                        float(
                            subprocess.check_output(
                                f"ffprobe -v error -show_entries format=duration -of "
                                f'default=noprint_wrappers=1:nokey=1 "{url}"',
                                shell=True,
                            )
                            .decode("ascii")
                            .replace("\r", "")
                            .replace("\n", "")
                        )
                    )
                )
            except Exception as e:
                print("ERROR 6- ", e)
                return "error"
            # Return the song object with ffmpeg
            if seek is not None:
                return Song(
                    FFMPEGSource(
                        ctx,
                        discord.FFmpegPCMAudio(
                            url,
                            before_options="-ss " + parse_duration_raw(seek),
                        ),
                        data={
                            "duration": duration,
                            "title": title,
                            "url": "local@" + url,
                            "requester": requester,
                        },
                    ),
                    True,
                )
            else:
                return Song(
                    FFMPEGSource(
                        ctx,
                        discord.FFmpegPCMAudio(url),
                        data={
                            "duration": duration,
                            "title": title,
                            "url": "local@" + url,
                            "requester": requester,
                        },
                    ),
                    True,
                )
        elif "youtube" in domain or "youtu.be" in domain:
            try:
                result = Song(
                    await YTDLSource.create_source(
                        ctx, url, loop=self.bot.loop, requester=requester, seek=seek
                    )
                )
            except Exception as e:
                await ctx.channel.send(str(e))
                return "error"
            return result
        else:
            # Direct Link or another source
            try:
                result = Song(
                    await FFMPEGSource.create_source(
                        ctx, url, loop=self.bot.loop, requester=requester, seek=seek
                    ),
                    True,
                    True,
                )
            except Exception as e:
                await ctx.channel.send("Error: " + str(e))
                return "error"
            return result

    async def check_user_listening(self):
        while True:
            await asyncio.sleep(1)
            try:
                # If there is only 1 member in the voice channel, starts the checking task
                if self.voice and len(self.voice.channel.members) == 1:
                    self.timer = 0
                    # 180 seconds = 3 minutes, if the bot is alone for 3 minutes, it will leave the channel
                    while self.timer != 180:
                        await asyncio.sleep(1)
                        self.timer += 1
                        try:
                            # If there are at least 2 members in the channel or being kicked out of the channel,
                            # reset the timer and break the loop
                            if (
                                len(self.voice.channel.members) > 1
                                or self.me not in self.voice.channel.members
                            ):
                                self.timer = 0
                                break
                        except Exception as e:
                            print("ERROR 7- ", e)
                    # Leave the channel and stop everything
                    # Case 1: only 1 member in the channel and the member the bot itself
                    # Case 2: the bot is kicked out from the channel
                    if (
                        len(self.voice.channel.members) == 1
                        and self.me in self.voice.channel.members
                    ) or self.me not in self.voice.channel.members:
                        await self.stop(leave=True)
                        break
            except Exception as e:
                print("ERROR 8- ", e)

    # Update a voice state guild object in the background
    async def update_voice_state(self):
        await asyncio.sleep(3)
        while self.voice:
            await asyncio.sleep(1)
            guild = self.bot.get_guild(self.guild_id)
            if guild is None:
                print("[ERROR] Couldn't retrieve guild " + str(self.guild_id))
            else:
                # If the bot is kicked, the voice_client should be None
                if guild.voice_client:
                    self.voice = guild.voice_client
                else:
                    await self.stop(leave=True)
                    self.voice = None
                self.me = guild.me

    async def audio_player_task(self):
        while True:
            self.next.clear()
            if self.forbidden:
                # if "local@" in self.current.source.url:
                try:
                    domain = self.current["url"].split("/")[2]
                except Exception as e:
                    print("ERROR 9- ", e)
                    domain = ""
                self.current = await generate_source(
                    self,
                    domain,
                    self.current.source.url,
                    self.current.source.title,
                    self.current.source.requester,
                )
            else:
                if not self.loop:
                    # Try to get the next song within 2 minutes.
                    # If no song was added to the queue in time,
                    # the player will disconnect due to performance
                    # reasons.
                    try:
                        async with timeout(120):  # 2 minutes
                            # If it is skipped, clear the current song
                            if self.skipped:
                                self.current = None
                            # Get the next song
                            self.next_song = await self.songs.get()
                            # If the url contains local@, it is a local file
                            # if "local@" in self.current["url"]:
                            try:
                                domain = self.current["url"].split("/")[2]
                            except TypeError:
                                domain = ""
                            self.current = await generate_source(
                                self,
                                domain,
                                self.next_song["url"],
                                self.next_song["title"],
                                self.next_song["user"],
                            )

                            if self.current != "error":
                                # If loop queue, put the current song back to the end of the queue
                                if self.loop_queue:
                                    await self.songs.put(
                                        {
                                            "url": self.current.source.url,
                                            "title": self.current.source.title,
                                            "user": self.current.source.requester,
                                            "duration": self.current.source.duration_int,
                                        }
                                    )
                                self.skipped = False
                                self.stopped = False
                    except asyncio.TimeoutError:
                        return await self.stop(leave=True)
                else:
                    # Loop but skipped, proceed to the next song and keep looping
                    if self.skipped or self.stopped:
                        self.current = None
                        try:
                            async with timeout(120):  # 2 minutes
                                self.current = await self.songs.get()
                                # if "local@" in self.current["url"]:
                                try:
                                    domain = self.current["url"].split("/")[2]
                                except Exception as e:
                                    print("ERROR 11- ", e)
                                    domain = ""
                                self.current = await generate_source(
                                    self,
                                    domain,
                                    self.current["url"],
                                    self.current["title"],
                                    self.current["user"],
                                )

                                if self.current != "error":
                                    self.skipped = False
                                    self.stopped = False
                        except asyncio.TimeoutError:
                            return await self.stop(leave=True)
                    else:
                        # Looping, get the looped song
                        # if "local@" in self.current.source.url:
                        try:
                            domain = self.current.source.url.split("/")[2]
                        except Exception as e:
                            print("ERROR 12- ", e)
                            domain = ""
                        self.current = await generate_source(
                            self,
                            domain,
                            self.current.source.url,
                            self.current.source.title,
                            self.current.source.requester,
                        )

            if self.current != "error":
                self.current.source.volume = self._volume
                await asyncio.sleep(0.25)
                self.start_time = time.time()
                self.current.start_time = time.time()
                # if not self.forbidden:
                #     self.message = await self.current.source.channel.send(
                #         embed=self.current.create_embed("play"),
                #         view=PlayerControlView(self.bot, self),
                #     )
                self.forbidden = False
                self.voice.play(self.current.source, after=self.play_next_song)
                # Create a task for updating volume
                self.volume_updater = self.bot.loop.create_task(self.update_volume())
                await self.next.wait()
                # Delete the message of the song playing
                # if not self.forbidden:
                #     try:
                #         await self.message.delete()
                #     except:
                #         pass

    def play_next_song(self, error=None):
        end_time = time.time()
        play_duration = end_time - self.start_time
        if play_duration < 1 and self.current.source.duration_int != 1:
            self.forbidden = True
            self.next.set()
            return
        else:
            self.forbidden = False
        if error:
            print(f"Song finished with error: {str(error)}")
        # If it is not looping or seeking, clear the current song
        if not self.loop and not self.seeking:
            self.current = None
        # If it is not seeking, send a signal for await self.next.wait() to stop
        if not self.seeking:
            self.next.set()
        else:
            self.seeking = False

    def skip(self):
        # Skip the song by stopping the current song
        self.skipped = True
        if self.is_playing:
            self.voice.stop()

    async def stop(self, leave=False):
        # Clear the queue
        self.songs.clear()
        self.current = None
        if self.voice:
            # Stops the voice
            self.voice.stop()
            # If the bot should leave, then leave and cleanup things
            if leave:
                if self.voice_state_updater and not self.voice_state_updater.done():
                    self.voice_state_updater.cancel()
                self.voice_state_updater = None
                try:
                    await self.voice.disconnect()
                except Exception as e:
                    print("ERROR 13- ", e)
                    pass
                self.voice = None
        if leave:
            if self.audio_player and not self.audio_player.done():
                self.audio_player.cancel()
            if self.listener_task and not self.listener_task.done():
                self.listener_task.cancel()
            if self.volume_updater and not self.volume_updater.done():
                self.volume_updater.cancel()
                self.volume_updater = None


class SearchMenu(discord.ui.Select):
    def __init__(self, bot, options_raw, cog, ctx):
        self.bot = bot
        self.cog = cog
        self.ctx = ctx
        reaction_list = [
            "1️⃣",
            "2️⃣",
            "3️⃣",
            "4️⃣",
            "5️⃣",
            "6️⃣",
            "7️⃣",
            "8️⃣",
            "9️⃣",
            "🔟",
        ]
        options = [
            discord.SelectOption(
                label=data["title"],
                description=f"Duration: {data['duration']}",
                value=str(data["index"]),
                emoji=reaction_list[data["index"]],
            )
            for data in options_raw
        ]
        options.append(
            discord.SelectOption(
                label="Cancel",
                description="Cancel the search",
                value="11",
                emoji="❌",
            )
        )
        self.data = options_raw
        self.completed = False
        super().__init__(
            placeholder="Select the desired song...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction):
        if int(self.values[0]) == 11:
            self.completed = True
            return await interaction.response.edit_message(
                embed=get_embed(
                    title="Cancelled",
                    description=None,
                    color=discord.Color.green(),
                ),
                view=None,
            )
        # Edit the message to reduce its size
        await interaction.response.edit_message(
            embed=get_embed(
                title="Selected:",
                description=self.data[int(self.values[0])]["title"],
                color=discord.Color.green(),
            ),
            view=None,
        )
        msg = await interaction.original_response()

        # Invoke the play command

        if not self.ctx.author.voice or not self.ctx.author.voice.channel:
            return await interaction.followup.edit_message(
                message_id=msg.id,
                embed=get_embed(
                    title="You are not connected to any voice channel or the same voice channel.",
                    color=discord.Color.red(),
                ),
            )
        voice_client = (await self.bot.fetch_guild(interaction.guild_id)).voice_client
        if voice_client:
            if voice_client.channel != self.ctx.author.voice.channel:
                return await interaction.followup.edit_message(
                    message_id=msg.id,
                    embed=get_embed(
                        title="Bot is already in a voice channel.",
                        color=discord.Color.red(),
                    ),
                )

        ctx = self.ctx
        search = self.data[int(self.values[0])]["url"]
        if search is None:
            return await interaction.followup.edit_message(
                message_id=msg.id,
                embed=get_embed(
                    title="Bot is already in a voice channel.",
                    color=discord.Color.red(),
                ),
            )
        # Joins the channel if it hasn't
        if not ctx.voice_state.voice:
            ctx.from_play = True
            await join_voice_channel(ctx)
        # Errors may occur while joining the channel, if the voice is None, don't continue
        if not ctx.voice_state.voice:
            return
        if not ctx.debug["debug"]:
            # If the user invoking this command is not in the same channel, return error
            if (
                not ctx.author.voice
                or not ctx.author.voice.channel
                or (
                    ctx.voice_state.voice
                    and ctx.author.voice.channel != ctx.voice_state.voice.channel
                )
            ):
                return await interaction.followup.edit_message(
                    message_id=msg.id,
                    embed=get_embed(
                        title="You are not connected to any voice channel or the same voice channel.",
                        color=discord.Color.red(),
                    ),
                )

            if ctx.voice_client:
                if ctx.voice_client.channel != ctx.author.voice.channel:
                    return await interaction.followup.edit_message(
                        message_id=msg.id,
                        embed=get_embed(
                            title="Bot is already in a voice channel.",
                            color=discord.Color.red(),
                        ),
                    )

        loop = self.bot.loop
        try:
            await interaction.followup.edit_message(
                message_id=msg.id,
                embed=get_embed(
                    title=f"Searching for: **<{search}>**",
                    color=discord.Color.green(),
                ),
            )
            # Supports playing a playlist but it must be like https://youtube.com/playlist?
            if "/playlist?" in search:
                partial = functools.partial(
                    YTDLSource.ytdl_playlist.extract_info, search, download=False
                )
                data = await loop.run_in_executor(None, partial)
                if data is None:
                    return await interaction.followup.edit_message(
                        message_id=msg.id,
                        embed=get_embed(
                            title=f"Couldn't find anything that matches `{search}`",
                            color=discord.Color.red(),
                        ),
                    )
                playlist = await parse_songs(ctx, data)
                await interaction.followup.edit_message(
                    message_id=msg.id,
                    embed=get_embed(
                        title=f"Enqueued **{len(playlist)}** songs",
                        color=discord.Color.green(),
                    ),
                )
            else:
                # Just a single song
                try:
                    partial = functools.partial(
                        YTDLSource.ytdl.extract_info, search, download=False
                    )
                    data = await loop.run_in_executor(None, partial)
                except Exception as e:
                    # Get the error message from the dictionary, if it doesn't exist in dict, return the original error
                    # message
                    message = error_messages.get(str(e), str(e))
                    return await interaction.followup.edit_message(
                        message_id=msg.id,
                        embed=get_embed(
                            title=f"Error: {message}",
                            color=discord.Color.red(),
                        ),
                    )
                if "entries" in data:
                    if len(data["entries"]) > 0:
                        data = data["entries"][0]
                    else:
                        return await interaction.followup.edit_message(
                            message_id=msg.id,
                            embed=get_embed(
                                title=f"Couldn't find anything that matches `{search}`",
                                color=discord.Color.red(),
                            ),
                        )
                # Add the song to the pending list
                try:
                    duration = int(data["duration"])
                except Exception as e:
                    print("ERROR 36-", e)
                    duration = 0
                await ctx.voice_state.songs.put(
                    {
                        "url": data["webpage_url"],
                        "title": data["title"],
                        "user": ctx.author,
                        "duration": duration,
                    }
                )
                await interaction.followup.edit_message(
                    message_id=msg.id,
                    embed=get_embed(
                        title=f"Enqueued **{data['title']}**",
                        color=discord.Color.green(),
                    ),
                )
            ctx.voice_state.stopped = False
        except YTDLError as e:
            await interaction.followup.edit_message(
                message_id=msg.id,
                embed=get_embed(
                    title=f"Error: {str(e)}",
                    color=discord.Color.red(),
                ),
            )
        self.completed = True


class SearchView(discord.ui.View):
    def __init__(self, bot, data, ctx, cog):
        self.bot = bot
        self.ctx = ctx
        self.data = data
        self.cog = cog
        super().__init__(timeout=60)
        self.add_item(SearchMenu(self.bot, data, cog, ctx))

    async def on_timeout(self):
        if not self.children[0].completed:
            await self.message.edit(
                embed=get_embed(title="Timed out", color=0xFF0000),
                view=None,
            )


class SkipVoteView(discord.ui.View):
    def __init__(self, bot, voice_state, voting):
        self.bot = bot
        self.voice_state = voice_state
        self.voting = voting
        self.votes = 1
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.success,
        emoji="<:greenTick:874767321007276143>",
    )
    async def yes_btn(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        if interaction.user in self.voting["agree"]:
            return await interaction.followup.send(
                embed=get_embed(
                    title="You already voted for skip.", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        if interaction.user in self.voting["disagree"]:
            self.voting["disagree"].remove(interaction.user)

        self.voting["agree"].append(interaction.user)
        self.votes += 1

        await interaction.edit_original_response(
            embed=get_embed(
                title="Skip current song?",
                description=f"```{self.voice_state.current.source.title}```\nVotes to skip - {self.votes}",
            ),
            view=self,
        )
        return await interaction.followup.send(
            embed=get_embed(title="Voted you to agree", color=discord.Color.green()),
            ephemeral=True,
        )

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.danger,
        emoji="<:redThick:874767320915005471>",
    )
    async def no_btn(self, button, interaction):
        if interaction.user not in self.voice_state.voice.channel.members:
            return await interaction.response.send(
                embed=get_embed(
                    title="You are not in the same voice channel.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        await interaction.response.defer()

        if interaction.user in self.voting["disagree"]:
            return await interaction.response.send_message(
                embed=get_embed(
                    title="You already voted against skip.", color=discord.Color.red()
                ),
                ephemeral=True,
            )

        if interaction.user in self.voting["agree"]:
            self.voting["agree"].remove(interaction.user)

        self.voting["disagree"].append(interaction.user)
        self.votes -= 1

        await interaction.edit_original_response(
            embed=get_embed(
                title="Skip current song?",
                description=f"```{self.voice_state.current.source.title}```\nVotes to skip - {self.votes}",
            ),
            view=self,
        )
        return await interaction.followup.send(
            embed=get_embed(title="Voted you to disagree", color=discord.Color.green()),
            ephemeral=True,
        )


class StopVoteView(discord.ui.View):
    def __init__(self, bot, voice_state, voting):
        self.bot = bot
        self.voice_state = voice_state
        self.voting = voting
        self.votes = 1
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.success,
        emoji="<:greenTick:874767321007276143>",
    )
    async def yes_btn(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        if interaction.user in self.voting["agree"]:
            return await interaction.followup.send(
                embed=get_embed(
                    title="You already voted for stop.", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        if interaction.user in self.voting["disagree"]:
            self.voting["disagree"].remove(interaction.user)

        self.voting["agree"].append(interaction.user)
        self.votes += 1

        await interaction.edit_original_response(
            embed=get_embed(
                title="Stop current queue?",
                description=f"Votes to stop - {self.votes}",
            ),
            view=self,
        )
        return await interaction.followup.send(
            embed=get_embed(title="Voted you to agree", color=discord.Color.green()),
            ephemeral=True,
        )

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.danger,
        emoji="<:redThick:874767320915005471>",
    )
    async def no_btn(self, button, interaction):
        if interaction.user not in self.voice_state.voice.channel.members:
            return await interaction.response.send(
                embed=get_embed(
                    title="You are not in the same voice channel.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        await interaction.response.defer()

        if interaction.user in self.voting["disagree"]:
            return await interaction.response.send_message(
                embed=get_embed(
                    title="You already voted against stop.", color=discord.Color.red()
                ),
                ephemeral=True,
            )

        if interaction.user in self.voting["agree"]:
            self.voting["agree"].remove(interaction.user)

        self.voting["disagree"].append(interaction.user)
        self.votes -= 1

        await interaction.edit_original_response(
            embed=get_embed(
                title="Stop current queue?",
                description=f"Votes to stop - {self.votes}",
            ),
            view=self,
        )
        return await interaction.followup.send(
            embed=get_embed(title="Voted you to disagree", color=discord.Color.green()),
            ephemeral=True,
        )


class PlayerControlView(discord.ui.View):
    def __init__(self, bot, voice_state):
        self.bot = bot
        self.voice_state = voice_state
        super().__init__(timeout=None)
        set_loop_btns(self)

    @discord.ui.button(
        label="Pause",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="0",
        emoji="⏸",
        disabled=False,
    )
    async def pause(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()
        if self.voice_state.is_playing and self.voice_state.voice.is_playing():
            self.voice_state.voice.pause()
            # Sets the pause time
            self.voice_state.current.pause_time = time.time()
            self.voice_state.current.paused = True
            get_children_by_id(self.children, "0").emoji = "▶"
            get_children_by_id(self.children, "0").label = ("Resume",)
        elif self.voice_state.is_playing and self.voice_state.voice.is_paused():
            self.voice_state.voice.resume()
            # Updates internal data for handling song progress that was paused
            self.voice_state.current.pause_duration += (
                time.time() - self.voice_state.current.pause_time
            )
            self.voice_state.current.pause_time = 0
            self.voice_state.current.paused = False
            get_children_by_id(self.children, "0").emoji = "⏸"
            get_children_by_id(self.children, "0").label = "Pause"
        await interaction.edit_original_response(view=self)

    @discord.ui.button(
        label="Skip",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="1",
        emoji="⏭",
        disabled=False,
    )
    async def skip(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        vote_view = SkipVoteView(
            self.bot,
            self.voice_state,
            {"agree": [interaction.user], "disagree": []},
        )
        msg = await interaction.channel.send(
            embed=get_embed(
                title="Skip current song?",
                description=f"```{self.voice_state.current.source.title}```\nVotes to skip - 1",
            ),
            view=vote_view,
        )
        await asyncio.sleep(10)
        if vote_view.votes > 0:
            await msg.edit(
                embed=get_embed(title="Skip approved", color=discord.Color.green()),
                view=None,
            )
            self.voice_state.skip()
            await asyncio.sleep(3)
            await interaction.edit_original_response(
                embed=self.voice_state.current.create_embed("now"), view=self
            )
        else:
            await msg.edit(
                embed=get_embed(title="Skip canceled", color=discord.Color.red()),
                view=None,
            )

    @discord.ui.button(
        label="Stop",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="2",
        emoji="⏹",
        disabled=False,
    )
    async def stop(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()

        vote_view = StopVoteView(
            self.bot,
            self.voice_state,
            {"agree": [interaction.user], "disagree": []},
        )
        msg = await interaction.channel.send(
            embed=get_embed(
                title="Stop current queue?",
                description=f"Votes to stop - 1",
            ),
            view=vote_view,
        )
        await asyncio.sleep(10)
        if vote_view.votes > 0:
            await msg.edit(
                embed=get_embed(title="Stop approved", color=discord.Color.green()),
                view=None,
            )
            self.voice_state.songs.clear()

            if self.voice_state.is_playing:
                await self.voice_state.stop()
                self.voice_state.stopped = True
        else:
            await msg.edit(
                embed=get_embed(title="Stop canceled", color=discord.Color.red()),
                view=None,
            )

    @discord.ui.button(
        label="Loop",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="3",
        emoji="🔂",
        disabled=False,
    )
    async def loop(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()
        self.voice_state.loop = not self.voice_state.loop
        set_loop_btns(self)
        await interaction.edit_original_response(view=self)

    @discord.ui.button(
        label="Queue",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="5",
        emoji="📜",
        disabled=False,
    )
    async def queue(self, button, interaction):
        # Shows the queue, add page number to view different pages
        page = 1
        if len(self.voice_state.songs) == 0 and self.voice_state.current is None:
            if useEmbed:
                return interaction.response.send_message(
                    embed=get_embed(title="Empty queue.", color=0xFF0000),
                    ephemeral=True,
                )
            return await interaction.response.send_message(
                embed=get_embed(title="Empty queue.", color=discord.Color.red()),
                ephemeral=True,
            )

        # Invoking queue while the bot is retrieving another song will cause error, wait for 1 second
        while self.voice_state.current is None or isinstance(
            self.voice_state.current, dict
        ):
            await asyncio.sleep(1)
        return await interaction.response.send_message(
            embed=create_music_embed(Music, self, page),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Loop Queue",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="4",
        emoji="🔂",
        disabled=False,
    )
    async def loopqueue(self, button, interaction):
        user_in_voice = await check_user_in_voice_interaction(self, interaction)
        if not user_in_voice:
            return
        await interaction.response.defer()
        self.voice_state.loop_queue = not self.voice_state.loop_queue
        try:
            if self.voice_state.loop_queue:
                await self.voice_state.songs.put(
                    {
                        "url": self.voice_state.current.source.url,
                        "title": self.voice_state.current.source.title,
                        "user": self.voice_state.current.source.requester,
                        "duration": self.voice_state.current.source.duration_int,
                    }
                )
        except AttributeError:
            pass
        set_loop_btns(self)
        await interaction.edit_original_response(view=self)


class Music(commands.Cog):
    @staticmethod
    # Return a discord.Embed() object, provides 5 songs from the queue/playlist depending on the page requested
    # Parameter "page" greater than the pages that the queue has will set the page to the last page
    # Invalid parameter "page" will display the first page
    def queue_embed(data, page, header, description, song_id):
        # Get the total duration from the queue or playlist
        def get_total_duration(songs_data):
            total_duration = 0
            for song_data in songs_data:
                total_duration += song_data["duration"]
            return total_duration

        items_per_page = 5
        pages = math.ceil(len(data) / items_per_page)
        if page < 1:
            page = 1
        page = min(pages, page)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        queue = ""
        url = "https://youtu.be/" if song_id == "id" else ""
        # If data has children, iterates through all children and create the body
        if len(data):
            for i, song in enumerate(data[start:end], start=start):
                if "local@" in song[song_id]:
                    title = song["title"].replace("_", "\\_")
                    try:
                        duration = parse_duration(song["duration"])
                    except Exception as e:
                        print(f"ERROR 15- {e}")
                        duration = "Unknown"
                    queue += (f"`{i + 1}.` **{title}** ({duration})\n",)
                else:
                    try:
                        duration = parse_duration_raw(song["duration"])
                    except Exception as e:
                        print(f"ERROR 16- {e}")
                        duration = "Unknown"
                    queue += (
                        f"`{i + 1}.` [**{song['title']}**]({url}{song[song_id]}) ({duration})\n",
                    )
        else:
            queue = ("No songs in queue...",)
        embed = (
            get_embed(title=header, description=description)
            .add_field(
                name=f"**{len(data)} tracks** - {parse_duration(get_total_duration(data))}",
                value=queue,
            )
            .set_footer(text=f"Viewing page {page}/{pages}")
        )
        return embed

    # Function for responding to the user
    # reply=True will cause the bot to reply to the user (discord function)
    # async def respond(
    #     self,
    #     ctx,
    #     message: str = None,
    #     color=discord.Embed.Empty,
    #     embed=None,
    #     reply: bool = True,
    #     view=None,
    # ):
    #     if useEmbed:
    #         if embed is None:
    #             embed = discord.Embed(title=message, color=color)
    #         message = None
    #     if isinstance(ctx, dict):
    #         if reply:
    #             if isinstance(
    #                 ctx["ctx"], discord.ext.bridge.context.BridgeExtContext
    #             ):  # Prefix
    #                 return await ctx["ctx"].reply(
    #                     message, embed=embed, mention_author=False, view=view
    #                 )
    #             else:
    #                 return await ctx["ctx"].respond(message, embed=embed, view=view)
    #
    #         else:
    #             return await ctx["channel"].send(message, embed=embed, view=view)

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
        voice_states = self.voice_states.keys()
        # Remove all voice states from the memory
        for voice_state in voice_states:
            del self.voice_states[voice_state]
        try:
            shutil.rmtree("./tempMusic")
        except Exception as e:
            print(f"ERROR 17- {e}")
            pass

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
        required=True,
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
                print(f"ERROR - 19{e}")
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
            self.voice_state,
            {"agree": [ctx.user], "disagree": []},
        )
        msg = await ctx.send(
            embed=get_embed(
                title="Stop current queue?",
                description=f"Votes to Stop - 1",
            ),
            view=vote_view,
        )
        await asyncio.sleep(10)
        if vote_view.votes > 0:
            await msg.edit(
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
            await msg.edit(
                embed=get_embed(title="Stop canceled", color=discord.Color.red()),
                view=None,
            )

    @music.command(
        name="skip",
        description="Skip current song",
    )
    async def skips(self, ctx):
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
            self.voice_state,
            {"agree": [ctx.user], "disagree": []},
        )
        msg = await ctx.send(
            embed=get_embed(
                title="Skip current song?",
                description=f"```{self.voice_state.current.source.title}```\nVotes to skip - 1",
            ),
            view=vote_view,
        )
        await asyncio.sleep(10)
        if vote_view.votes > 0:
            await msg.edit(
                embed=get_embed(title="Skip approved", color=discord.Color.green()),
                view=None,
            )
            self.voice_state.skip()
        else:
            await msg.edit(
                embed=get_embed(title="Skip canceled", color=discord.Color.red()),
                view=None,
            )

    @music.command(name="queue", description="Show song queue")
    @discord.commands.option(
        name="page",
        description="Choose page of queue.",
        required=True,
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
            embed=create_music_embed(self, ctx, page),
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
        required=True,
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
                title=f"Song `{name}` removed.",
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
        required=True,
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
                                    "duration": int(
                                        float(
                                            subprocess.check_output(
                                                f"ffprobe -v error -show_entries format=duration -of "
                                                f'default=noprint_wrappers=1:nokey=1 "{link}"',
                                                shell=True,
                                            )
                                            .decode("ascii")
                                            .replace("\r", "")
                                            .replace("\n", "")
                                        )
                                    ),
                                    "realurl": data["url"],
                                }
                            )
                    except Exception as e:
                        print(f"ERROR 22- {e}")
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
                        print(f"ERROR 23- {e}")
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
        required=True,
    )
    async def search(self, ctx, keyword: str):
        # Search from YouTube and returns 10 songs
        original_keyword = keyword
        keyword = "ytsearch10:" + keyword
        data = YTDLSource.ytdl_playlist.extract_info(keyword, download=False)
        result = []
        # Get 10 songs from the result
        for index, entry in enumerate(data["entries"]):
            try:
                duration = parse_duration(int(entry.get("duration")))
            except Exception as e:
                print(f"ERROR 24- {e}")
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
                name=f'{count + 1}. {entry["title"]}',
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
            print(f"ERROR 25- {e}")
        try:
            await ctx.voice_client.disconnect()
        except Exception as e:
            print(f"ERROR 26- {e}")
        try:
            await ctx.voice_client.clean_up()
        except Exception as e:
            print(f"ERROR 27- {e}")
        del self.voice_states[ctx.guild.id]
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
            print(f"ERROR 28- {e}")
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
        required=True,
    )
    async def seek(self, ctx, seconds: str):
        user_in_voice = await check_user_in_voice(ctx)
        if not user_in_voice:
            return

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.seeking = True
            try:
                # Google this regular expression by yourself
                # It will parse which hour, minute, second to seek to
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
                print(f"ERROR 29- {e}")
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
                print(f"ERROR 30- {e}")
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

    @music.command(name="player")
    async def get_song_player(self, ctx):
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

        await ctx.respond(
            embed=ctx.voice_state.current.create_embed("now"),
            view=PlayerControlView(self.bot, self.voice_states[ctx.guild.id]),
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(Music(bot))
