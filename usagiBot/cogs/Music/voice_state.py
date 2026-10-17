import asyncio
import logging
import time

import discord
from async_timeout import timeout
from discord.ext import commands

from usagiBot.cogs.Music.music_utils import (
    generate_source,
    get_audio_duration,
    parse_duration_raw,
)
from usagiBot.cogs.Music.sources import FFMPEGSource, Song, SongQueue
from usagiBot.cogs.Music.views import PlayerControlView

logger = logging.getLogger(__name__)

# Seconds the bot stays alone in a voice channel before leaving
ALONE_TIMEOUT = 180


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx, cog):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.next_song = None
        self.songs = SongQueue()
        self.message = None

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

        self.alone_timer = None

        self.debug = {"debug": False, "channel": None, "debug_log": False}

        self.forbidden = False

        self.cog = cog

    def recreate_bg_task(self, ctx, cog):
        self.__init__(self.bot, ctx, cog)

    def __del__(self):
        audio_player = getattr(self, "audio_player", None)
        if audio_player:
            audio_player.cancel()

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
        # Apply directly — replaces the old 1s polling task
        if self.current and not isinstance(self.current, (dict, str)):
            self.current.source.volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    # ----- alone-in-channel handling (driven by on_voice_state_update) -----

    def start_alone_timer(self):
        if self.alone_timer is None or self.alone_timer.done():
            self.alone_timer = self.bot.loop.create_task(self._leave_when_alone())

    def cancel_alone_timer(self):
        if self.alone_timer and not self.alone_timer.done():
            self.alone_timer.cancel()
        self.alone_timer = None

    async def _leave_when_alone(self):
        await asyncio.sleep(ALONE_TIMEOUT)
        if self.voice and len(self.voice.channel.members) == 1:
            await self.stop(leave=True)
            self.cog.voice_states.pop(self.guild_id, None)

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

    async def create_song_source(self, ctx, url, title=None, requester=None, seek=None):
        try:
            domain = url.split("/")[2]
        except Exception as e:
            logger.error("Couldn't parse domain from %r: %s", url, e)
            domain = ""
        if "local@" in url:
            # It is a local file
            url = url[6:]
            try:
                # Try to get the duration of the uploaded file
                duration = str(await get_audio_duration(url))
            except Exception as e:
                logger.error("ffprobe failed for %r: %s", url, e)
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

    async def _send_now_playing(self):
        """Post the now-playing card; a Discord error must not stop playback."""
        try:
            return await self.current.source.channel.send(
                embed=self.current.create_embed("play"),
                view=PlayerControlView(self.bot, self),
            )
        except discord.HTTPException as e:
            logger.error("Couldn't send now-playing message: %s", e)
            return None

    async def audio_player_task(self):
        while True:
            self.next.clear()
            if self.forbidden:
                try:
                    domain = self.current["url"].split("/")[2]
                except Exception as e:
                    logger.error("Couldn't parse domain for forbidden retry: %s", e)
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
                                try:
                                    domain = self.current["url"].split("/")[2]
                                except Exception as e:
                                    logger.error("Couldn't parse domain: %s", e)
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
                        try:
                            domain = self.current.source.url.split("/")[2]
                        except Exception as e:
                            logger.error("Couldn't parse domain: %s", e)
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
                if not self.forbidden:
                    self.message = await self._send_now_playing()
                self.forbidden = False
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.next.wait()
                # Delete the message of the song playing
                if not self.forbidden:
                    try:
                        if self.message:
                            await self.message.delete()
                    except Exception as e:
                        logger.error("Couldn't delete now-playing message: %s", e)

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
            logger.error("Song finished with error: %s", error)
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
                try:
                    await self.voice.disconnect()
                except Exception as e:
                    logger.error("Couldn't disconnect voice: %s", e)
                self.voice = None
        if leave:
            self.cancel_alone_timer()
            if self.audio_player and not self.audio_player.done():
                self.audio_player.cancel()
