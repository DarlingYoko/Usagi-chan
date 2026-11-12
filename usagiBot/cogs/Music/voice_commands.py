"""/music join, summon, leave, musicreload — the bot's voice connection."""
import logging
from typing import Optional, cast

import discord

from usagiBot.cogs.Music.context import MusicContext
from usagiBot.cogs.Music.group import music
from usagiBot.cogs.Music.music_utils import (
    check_user_in_voice,
    defer_if_needed,
    join_voice_channel,
    unmute_self,
)
from usagiBot.env import BOT_OWNER
from usagiBot.src.UsagiUtils import get_embed

logger = logging.getLogger(__name__)

# Users allowed to summon without the "Move Members" permission
authors = (BOT_OWNER,)


async def respond_error(ctx: discord.ApplicationContext, title: str) -> None:
    await ctx.respond(
        embed=get_embed(title=title, color=discord.Color.red()), ephemeral=True
    )


class VoiceCommands:
    """Mixin for the Music cog; expects self.voice_states."""

    voice_states: dict

    async def connect_author_channel(self, ctx: MusicContext) -> bool:
        """
        Join the author's voice channel. True when the bot ends up there;
        from /music play an existing connection to that channel is fine.
        """
        if not ctx.author.voice or not ctx.author.voice.channel:
            await respond_error(
                ctx,
                "You are not connected to any voice channel or the same voice channel.",
            )
            return False

        if ctx.voice_client:
            if ctx.voice_client.channel.id != ctx.author.voice.channel.id:
                await respond_error(ctx, "Bot is already in a voice channel.")
                return False
            if not ctx.from_play:
                await respond_error(ctx, "Bot is already in your voice channel.")
                return False
            return True

        return await join_voice_channel(ctx)

    @music.command(
        name="join",
        invoke_without_subcommand=True,
        description="Joins the current voice channel",
    )
    async def join(self, ctx: MusicContext) -> bool:
        return await self.connect_author_channel(ctx)

    @music.command(
        name="summon",
        description="Summon the bot to current voice channel (Requires Move Member permission)",
    )
    @discord.commands.option(
        name="channel",
        description="Choose channel to summon Usagi",
    )
    async def summon(
        self, ctx: MusicContext, channel: discord.VoiceChannel
    ) -> None:
        if (
            not ctx.author.guild_permissions.move_members
            and ctx.author.id not in authors
        ):
            return await respond_error(
                ctx,
                'Only members with "Move Member" permission are allowed to use this command.',
            )

        if not channel.permissions_for(ctx.me).connect:
            return await respond_error(ctx, "No permission to join the voice channel!")

        voice = ctx.voice_state.voice
        if voice:
            previous = voice.channel
            await voice.move_to(channel)
            await ctx.respond(
                embed=get_embed(
                    title=f"Switched from **{previous}** to **{channel}**.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
            ctx.voice_state.voice = cast(
                Optional[discord.VoiceClient], ctx.guild.voice_client
            )
        else:
            await defer_if_needed(ctx)
            ctx.voice_state.voice = await channel.connect()
            await ctx.respond(
                embed=get_embed(
                    title=f"Joined **{channel}**.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )

        if isinstance(channel, discord.StageChannel):
            await unmute_self(ctx)

    @music.command(
        name="leave",
        description="Leave the voice channel",
    )
    async def leave(self, ctx: MusicContext) -> None:
        if not await check_user_in_voice(ctx):
            return

        if not ctx.voice_state.voice:
            return await respond_error(ctx, "Bot is not connected to any voice channel.")

        await ctx.respond(
            embed=get_embed(
                title="Bot left the voice channel.", color=discord.Color.green()
            ),
            ephemeral=True,
        )
        await ctx.voice_state.stop(leave=True)
        self.voice_states.pop(ctx.guild.id, None)

    @music.command(
        name="musicreload",
        description="Reload the music bot",
    )
    async def musicreload(self, ctx: MusicContext) -> None:
        # Best-effort teardown for when the player got stuck; each step may
        # fail on a half-dead connection, the state is dropped regardless.
        try:
            await ctx.voice_state.stop(leave=True)
        except Exception as e:
            logger.error("musicreload stop failed: %s", e)
        voice_client = ctx.voice_client
        if voice_client is not None:
            try:
                await voice_client.disconnect()
            except Exception as e:
                logger.error("musicreload disconnect failed: %s", e)
            try:
                voice_client.cleanup()
            except Exception as e:
                logger.error("musicreload clean_up failed: %s", e)
        self.voice_states.pop(ctx.guild.id, None)
        await ctx.respond(
            embed=get_embed(title="Music bot reloaded.", color=discord.Color.green()),
            ephemeral=True,
        )
