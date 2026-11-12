"""Static type of the ctx every /music command receives."""
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from usagiBot.cogs.Music.voice_state import VoiceState


class MusicContext(discord.ApplicationContext):
    """
    Annotation-only: never instantiated. Music.cog_check rejects DMs, so
    guild/author/me are always set, and Music.cog_before_invoke attaches
    the guild's player as voice_state plus the from_play/debug flags.
    """

    guild: discord.Guild
    author: discord.Member
    me: discord.Member
    voice_state: "VoiceState"
    from_play: bool
    debug: dict
