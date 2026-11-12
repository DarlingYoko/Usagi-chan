"""Select menu that turns /music search results into a queued song."""
from typing import Any, Awaitable, Callable, List, Optional, Union

import discord

from usagiBot.cogs.Music.enqueue import enqueue_link
from usagiBot.cogs.Music.music_utils import join_voice_channel
from usagiBot.src.UsagiUtils import get_embed

CANCEL_VALUE = "11"
NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
NOT_IN_VOICE = "You are not connected to any voice channel or the same voice channel."
BOT_ELSEWHERE = "Bot is already in a voice channel."


class SearchMenu(discord.ui.Select):
    def __init__(self, bot: discord.Bot, results: List[dict], ctx: Any) -> None:
        self.bot = bot
        self.ctx = ctx
        self.data = results
        self.completed = False
        options = [
            discord.SelectOption(
                label=result["title"],
                description=f"Duration: {result['duration']}",
                value=str(result["index"]),
                emoji=NUMBER_EMOJIS[result["index"]],
            )
            for result in results
        ]
        options.append(
            discord.SelectOption(
                label="Cancel",
                description="Cancel the search",
                value=CANCEL_VALUE,
                emoji="❌",
            )
        )
        super().__init__(
            placeholder="Select the desired song...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        value = (self.values or [CANCEL_VALUE])[0]
        if value == CANCEL_VALUE:
            self.completed = True
            await interaction.response.edit_message(
                embed=get_embed(title="Cancelled", color=discord.Color.green()),
                view=None,
            )
            return

        choice = self.data[int(value)]
        # Shrink the results message down to the pick
        await interaction.response.edit_message(
            embed=get_embed(
                title="Selected:",
                description=choice["title"],
                color=discord.Color.green(),
            ),
            view=None,
        )
        message = await interaction.original_response()

        async def show(title: str, ok: bool) -> None:
            await interaction.followup.edit_message(
                message_id=message.id,
                embed=get_embed(
                    title=title,
                    color=discord.Color.green() if ok else discord.Color.red(),
                ),
            )

        await self._enqueue(choice["url"], show)
        self.completed = True

    async def _enqueue(self, url: str, show: Callable[..., Awaitable[None]]) -> None:
        ctx = self.ctx
        author_voice = ctx.author.voice
        if not author_voice or not author_voice.channel:
            return await show(NOT_IN_VOICE, ok=False)

        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.channel != author_voice.channel:
            return await show(BOT_ELSEWHERE, ok=False)

        if not ctx.voice_state.voice:
            ctx.from_play = True
            await join_voice_channel(ctx)
        # Joining may have failed (missing permission) — it already said why
        if not ctx.voice_state.voice:
            return
        if author_voice.channel != ctx.voice_state.voice.channel:
            return await show(NOT_IN_VOICE, ok=False)

        await show(f"Searching for: **<{url}>**", ok=True)
        result = await enqueue_link(self.bot.loop, ctx.voice_state, url, ctx.author)
        await show(result.message, ok=result.ok)


class SearchView(discord.ui.View):
    def __init__(self, bot: discord.Bot, results: List[dict], ctx: Any) -> None:
        self.bot = bot
        self.ctx = ctx
        self.message: Optional[
            Union[discord.InteractionMessage, discord.WebhookMessage]
        ] = None
        super().__init__(timeout=60)
        self.menu = SearchMenu(bot, results, ctx)
        self.add_item(self.menu)

    async def on_timeout(self) -> None:
        if not self.menu.completed and self.message is not None:
            await self.message.edit(
                embed=get_embed(title="Timed out", color=discord.Color.red()),
                view=None,
            )
