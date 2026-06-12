import asyncio
import functools
import itertools
import logging
import random
import time

import discord
import yt_dlp as youtube_dl

from usagiBot.cogs.Music.music_utils import (
    YTDL_OPTIONS,
    YTDL_OPTIONS_PLAYLIST,
    get_source,
    parse_duration,
    parse_duration_raw,
)
from usagiBot.src.UsagiUtils import get_embed

logger = logging.getLogger(__name__)

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ""

# Error messages for returning meaningfully error message to user
error_messages = {
    "ERROR: Sign in to confirm your age\nThis video may be inappropriate for some users.": "This video is "
    "age-restricted",
    "Video unavailable": "Video Unavailable",
    "ERROR: Private video\nSign in if you've been granted access to this video": "This video is private video",
}


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
            logger.error("FFMPEGSource duration parse failed: %s", e)
            self.duration = "Unknown"
        try:
            self.duration_raw = parse_duration_raw(int(data.get("duration")))
        except Exception as e:
            logger.error("FFMPEGSource raw duration parse failed: %s", e)
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
        loop: asyncio.AbstractEventLoop = None,
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
            logger.error("YTDLSource duration parse failed: %s", e)
            self.duration = "Unknown"
        try:
            self.duration_raw = parse_duration_raw(int(data.get("duration")))
        except Exception as e:
            logger.error("YTDLSource raw duration parse failed: %s", e)
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
        loop: asyncio.AbstractEventLoop = None,
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
