"""The /music command group.

Subcommands are declared on this group from several mixin modules
(voice_commands, playback_commands, queue_commands); the Music cog in
index.py inherits them all and owns the group as its class attribute.
"""
from discord import SlashCommandGroup

music = SlashCommandGroup(
    name="music",
    description="Listen any music from YouTube!",
)
