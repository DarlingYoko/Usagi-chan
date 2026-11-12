from unittest import IsolatedAsyncioTestCase
from unittest import mock

from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *
from usagiBot.tests.music_helpers import (
    embed_title,
    make_bot,
    make_current,
    make_interaction,
    make_state,
)


class VotingTestCase(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Music import voting

        self.voting = voting
        self.channel = mock.MagicMock(name="voice_channel")
        self.initiator = mock.MagicMock(name="initiator")
        self.voter = mock.MagicMock(name="voter")
        self.channel.members = [self.initiator, self.voter]
        self.state = make_state(self.channel, make_current(title="Song"))

    def view(self, kind: str = "SkipVoteView"):
        return getattr(self.voting, kind)(make_bot(), self.state, self.initiator)

    async def press(self, view, button: str, user) -> mock.MagicMock:
        interaction = make_interaction(user)
        item = next(child for child in view.children if child.label == button)
        await item.callback(interaction)
        return interaction


class TestVoteView(VotingTestCase):
    async def test_initiator_counts_as_first_vote(self) -> None:
        view = self.view()

        self.assertEqual(view.votes, 1)
        self.assertEqual(view.voting, {"agree": [self.initiator], "disagree": []})

    async def test_skip_prompt(self) -> None:
        embed = self.view().prompt_embed()

        self.assertEqual(embed.title, "Skip current song?")
        self.assertEqual(embed.description, "```Song```\nVotes to skip - 1")

    async def test_stop_prompt(self) -> None:
        embed = self.view("StopVoteView").prompt_embed()

        self.assertEqual(embed.title, "Stop current queue?")
        self.assertEqual(embed.description, "Votes to stop - 1")

    async def test_agree(self) -> None:
        view = self.view()

        interaction = await self.press(view, "Yes", self.voter)

        self.assertEqual(view.votes, 2)
        self.assertIn(self.voter, view.voting["agree"])
        self.assertIn(
            "Votes to skip - 2",
            interaction.edit_original_response.call_args.kwargs["embed"].description,
        )
        self.assertEqual(embed_title(interaction.followup.send), "Voted you to agree")

    async def test_disagree(self) -> None:
        view = self.view("StopVoteView")

        interaction = await self.press(view, "No", self.voter)

        self.assertEqual(view.votes, 0)
        self.assertIn(self.voter, view.voting["disagree"])
        self.assertEqual(embed_title(interaction.followup.send), "Voted you to disagree")

    async def test_changing_mind_moves_the_vote(self) -> None:
        view = self.view()

        await self.press(view, "No", self.initiator)

        self.assertEqual(view.voting, {"agree": [], "disagree": [self.initiator]})
        self.assertEqual(view.votes, 0)

    async def test_double_vote_is_rejected(self) -> None:
        view = self.view("StopVoteView")

        interaction = await self.press(view, "Yes", self.initiator)

        self.assertEqual(view.votes, 1)
        self.assertEqual(
            embed_title(interaction.followup.send), "You already voted for stop."
        )

    async def test_double_vote_against_is_rejected(self) -> None:
        view = self.view()
        await self.press(view, "No", self.voter)

        interaction = await self.press(view, "No", self.voter)

        self.assertEqual(view.votes, 0)
        self.assertEqual(
            embed_title(interaction.followup.send), "You already voted against skip."
        )

    async def test_outsiders_cannot_vote(self) -> None:
        view = self.view()
        outsider = mock.MagicMock(name="outsider")

        interaction = await self.press(view, "Yes", outsider)

        self.assertEqual(view.votes, 1)
        interaction.response.defer.assert_not_called()
        self.assertEqual(
            embed_title(interaction.response.send_message),
            "You are not in the same voice channel.",
        )


class TestRunVote(VotingTestCase):
    def sleeping_with(self, view, votes: int) -> mock.AsyncMock:
        async def fake_sleep(_seconds):
            view.votes = votes

        return mock.AsyncMock(side_effect=fake_sleep)

    async def run_vote(self, view, votes: int):
        send = mock.AsyncMock()
        on_approved = mock.AsyncMock()
        with mock.patch("asyncio.sleep", self.sleeping_with(view, votes)) as sleep:
            approved = await self.voting.run_vote(view, send, on_approved)
        return approved, send, on_approved, sleep

    async def test_approved(self) -> None:
        view = self.view()

        approved, send, on_approved, sleep = await self.run_vote(view, 1)

        self.assertTrue(approved)
        self.assertIs(send.call_args.kwargs["view"], view)
        self.assertEqual(send.call_args.kwargs["embed"].title, "Skip current song?")
        sleep.assert_awaited_with(self.voting.VOTE_SECONDS)
        message = send.return_value
        self.assertEqual(message.edit.call_args.kwargs["embed"].title, "Skip approved")
        self.assertIsNone(message.edit.call_args.kwargs["view"])
        on_approved.assert_awaited_once()
        message.delete.assert_awaited_with(delay=self.voting.VOTE_SECONDS)

    async def test_tie_is_rejected(self) -> None:
        view = self.view("StopVoteView")

        approved, send, on_approved, _ = await self.run_vote(view, 0)

        self.assertFalse(approved)
        self.assertEqual(
            send.return_value.edit.call_args.kwargs["embed"].title, "Stop canceled"
        )
        on_approved.assert_not_called()
        send.return_value.delete.assert_awaited_once()
