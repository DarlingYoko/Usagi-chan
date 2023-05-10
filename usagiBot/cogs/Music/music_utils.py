import asyncio
import os
import shutil

import discord
import time

from discord.ext import commands

from usagiBot.src.UsagiUtils import get_embed

# Commandline options for youtube-dl and ffmpeg
YTDL_OPTIONS_PLAYLIST = {
    "format": "bestaudio/best",
    "extractaudio": True,
    "audioformat": "mp3",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "extract_flat": "in_playlist",
}
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "extractaudio": True,
    "audioformat": "mp3",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


def parse_duration(duration: int):
    """
    Parse the duration to xx days xx hours xx minutes xx seconds
    """
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    duration = []
    if days > 0:
        duration.append(f"{days} days")
    if hours > 0:
        duration.append(f"{hours} hours")
    if minutes > 0:
        duration.append(f"{minutes} minutes")
    if seconds > 0:
        duration.append(f"{seconds} seconds")

    return " ".join(duration)


# Parse the duration to 00:00:00:00
def parse_duration_raw(duration: int):
    """
    Parse the duration to 00:00:00:00
    """
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    durations = []
    if days > 0:
        durations.append(str(days))
    if hours > 0:
        durations.append(("0" if days and hours < 10 else "") + f"{hours}")
    durations.append(("0" if hours and minutes < 10 else "") + f"{minutes}")
    durations.append(("0" if seconds < 10 else "") + f"{seconds}")

    return ":".join(durations)


def get_source(cls, ctx, seek, info):
    """
    If seeking, ask ffmpeg to start from a specific position, else simply return the object
    """
    if seek is not None:
        seek_option = FFMPEG_OPTIONS.copy()
        seek_option["before_options"] += " -ss " + parse_duration_raw(seek)
        return cls(ctx, discord.FFmpegPCMAudio(info["url"], **seek_option), data=info)
    else:
        return cls(
            ctx, discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS), data=info
        )


async def generate_source(self, domain, song_url, song_title, song_requester):
    if "youtube" in domain or "youtu.be" in domain:
        return await self.create_song_source(
            self._ctx,
            song_url,
            requester=song_requester,
        )
    else:
        return await self.create_song_source(
            self._ctx,
            song_url,
            title=song_title,
            requester=song_requester,
        )


async def join_voice_channel(ctx):
    destination = ctx.author.voice.channel

    # Check permission
    if not destination.permissions_for(ctx.me).connect:
        await ctx.respond(
            embed=get_embed(
                title="No permission to join the voice channel!",
                color=discord.Color.red(),
            ),
            ephemeral=True,
        )
        return False
    # Connect to the channel
    ctx.voice_state.voice = await destination.connect()
    await ctx.respond(
        embed=get_embed(
            title=f"Joined {destination.mention}", color=discord.Color.green()
        ),
        ephemeral=True,
    )

    if isinstance(ctx.voice_state.voice.channel, discord.StageChannel):
        await unmute_self(ctx)
    # Clear all music files
    if os.path.isdir(f"./tempMusic/{ctx.guild.id}"):
        shutil.rmtree(f"./tempMusic/{ctx.guild.id}")
    await ctx.me.edit(deafen=True)

    return True


async def parse_songs(ctx, data):
    entries = data["entries"]
    playlist = []
    for pos, song in enumerate(entries):
        # YouTube only, guess no one would play other than YouTube
        url = "https://youtu.be/" + song["id"]
        title = song["title"]
        duration = 0 if song["duration"] is None else int(song["duration"])
        playlist.append(
            {
                "pos": pos,
                "url": url,
                "title": title,
                "duration": duration,
            }
        )
    # Sort the playlist variable to match with the order in YouTube
    playlist.sort(key=lambda x: x["pos"])
    # Add all songs to the pending list
    for entry in playlist:
        await ctx.voice_state.songs.put(
            {
                "url": entry["url"],
                "title": entry["title"],
                "user": ctx.author,
                "duration": entry["duration"],
            }
        )
    return playlist


def set_loop_btns(self):
    get_children_by_id(self.children, "3").label = (
        "Disable Looping" if self.voice_state._loop else "Enable Looping"
    )
    get_children_by_id(self.children, "4").label = (
        "Disable Loop Queue" if self.voice_state.loop_queue else "Enable Loop Queue"
    )


def get_children_by_id(children, custom_id):
    for child in children:
        if child.custom_id == custom_id:
            return child
    return None


def create_music_embed(Music, ctx, page) -> discord.Embed:
    return Music.queue_embed(
        ctx.voice_state.songs,
        page,
        "Currently Playing",
        "[**{0}**]({1}) ({2} Left)".format(
            ctx.voice_state.current.source.title,
            ctx.voice_state.current.source.url,
            parse_duration(
                ctx.voice_state.current.source.duration_int
                - int(
                    time.time()
                    - ctx.voice_state.current.start_time
                    - ctx.voice_state.current.pause_duration
                )
            ),
        ),
        "url",
    )


async def check_user_in_voice(ctx) -> bool:
    # If the user invoking this command is not in the same channel, return error
    if (
        not ctx.author.voice
        or not ctx.author.voice.channel
        or (
            ctx.voice_state.voice
            and ctx.author.voice.channel != ctx.voice_state.voice.channel
        )
    ):
        await ctx.respond(
            embed=get_embed(
                title="You are not connected to any voice channel or the same voice channel.",
                color=discord.Color.red(),
            ),
            ephemeral=True,
        )
        return False

    return True


async def check_user_in_voice_interaction(self, interaction):
    if interaction.user not in self.voice_state.voice.channel.members:
        await interaction.response.send_message(
            embed=get_embed(
                title="You are not in the same voice channel.",
                color=discord.Color.red(),
            ),
            ephemeral=True,
        )
        return False
    return True


async def unmute_self(ctx):
    try:
        await asyncio.sleep(1)
        await ctx.me.edit(suppress=False)
    except Exception as e:
        print(f"ERROR 18- {e}")
        # Unable to unmute itself, ask admin to invite the bot to speak (auto)
        await ctx.respond(
            embed=get_embed(
                title="I have no permission to speak! Please invite me to speak.",
                color=discord.Color.red(),
            ),
            ephemeral=True,
        )


def cog_check(ctx):
    if not ctx.guild:
        raise commands.NoPrivateMessage("This command can't be used in DM channels.")
    return True
