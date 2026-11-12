"""Skip/stop votes: a Yes/No view plus the timed vote flow around it."""
import asyncio
from typing import Any, Awaitable, Callable

import discord

from usagiBot.cogs.Music.music_utils import check_user_in_voice_interaction
from usagiBot.src.UsagiUtils import get_embed

# How long a vote stays open, and how long its result stays visible
VOTE_SECONDS = 10


class VoteView(discord.ui.View):
    """
    Yes/No buttons for listeners in the bot's channel. The initiator counts as
    the first "yes"; the vote passes when yes outnumbers no.
    """

    # "skip" / "stop" — used in the prompt and the verdict texts
    noun = ""

    def __init__(self, bot: discord.Bot, voice_state: Any, initiator: Any) -> None:
        self.bot = bot
        self.voice_state = voice_state
        self.voting = {"agree": [initiator], "disagree": []}
        self.votes = 1
        super().__init__(timeout=None)

    def prompt_embed(self) -> discord.Embed:
        raise NotImplementedError

    async def _cast(self, interaction: discord.Interaction, agree: bool) -> None:
        if not await check_user_in_voice_interaction(self, interaction):
            return
        await interaction.response.defer()

        side, other = ("agree", "disagree") if agree else ("disagree", "agree")
        if interaction.user in self.voting[side]:
            title = (
                f"You already voted for {self.noun}."
                if agree
                else f"You already voted against {self.noun}."
            )
            await interaction.followup.send(
                embed=get_embed(title=title, color=discord.Color.red()),
                ephemeral=True,
            )
            return
        if interaction.user in self.voting[other]:
            self.voting[other].remove(interaction.user)
        self.voting[side].append(interaction.user)
        self.votes += 1 if agree else -1

        await interaction.edit_original_response(embed=self.prompt_embed(), view=self)
        await interaction.followup.send(
            embed=get_embed(
                title=f"Voted you to {side}", color=discord.Color.green()
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.success,
        emoji="<:greenTick:874767321007276143>",
    )
    async def yes_btn(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._cast(interaction, agree=True)

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.danger,
        emoji="<:redThick:874767320915005471>",
    )
    async def no_btn(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._cast(interaction, agree=False)


class SkipVoteView(VoteView):
    noun = "skip"

    def prompt_embed(self) -> discord.Embed:
        return get_embed(
            title="Skip current song?",
            description=f"```{self.voice_state.current.source.title}```\nVotes to skip - {self.votes}",
        )


class StopVoteView(VoteView):
    noun = "stop"

    def prompt_embed(self) -> discord.Embed:
        return get_embed(
            title="Stop current queue?",
            description=f"Votes to stop - {self.votes}",
        )


async def run_vote(
    view: VoteView,
    send: Callable[..., Awaitable[Any]],
    on_approved: Callable[[], Awaitable[Any]],
) -> bool:
    """
    Post the vote with `send`, wait VOTE_SECONDS, show the verdict, run
    `on_approved` if it passed, then remove the vote message.
    """
    message = await send(embed=view.prompt_embed(), view=view)
    await asyncio.sleep(VOTE_SECONDS)

    approved = view.votes > 0
    noun = view.noun.capitalize()
    await message.edit(
        embed=get_embed(
            title=f"{noun} approved" if approved else f"{noun} canceled",
            color=discord.Color.green() if approved else discord.Color.red(),
        ),
        view=None,
    )
    if approved:
        await on_approved()
    await message.delete(delay=VOTE_SECONDS)
    return approved
