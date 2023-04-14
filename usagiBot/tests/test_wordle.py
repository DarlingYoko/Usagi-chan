from unittest import IsolatedAsyncioTestCase
from unittest import mock

import discord
import os
from sqlalchemy.ext import asyncio

os.environ["BOT_OWNER"] = "11111"
os.environ["BOT_ID"] = "1234567890"


class TestWordleMethods(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        self.bot = mock.AsyncMock()

        import usagiBot.cogs.Wordle.wordle_utils as wordle_utils

        self.wordle_utils = wordle_utils

    def test_check_word_for_reality_in_dict(self):
        self.assertTrue(self.wordle_utils.check_word_for_reality("папка"))

    def test_check_word_for_reality_not_in_dict(self):
        self.assertFalse(self.wordle_utils.check_word_for_reality("ksdngksdjfnkg"))

    @mock.patch("random.randint")
    def test_get_word(self, mock_randint):
        mock_randint.return_value = 0
        self.assertEqual(self.wordle_utils.get_word(length=5), "АБЗАЦ")

    async def test_create_finish_game_embed(self) -> None:
        game_author = mock.MagicMock()
        game_author.name = "test_game_author"
        game_author.discriminator = "test_game_author_discriminator"

        winner = mock.MagicMock()
        winner.name = "test_winner"
        winner.discriminator = "test_winner_discriminator"

        interaction = mock.AsyncMock()
        interaction.guild.fetch_member.return_value = game_author
        interaction.user = winner

        title = "Wordle Game #123 finished."
        description = f"""```ansi
[0;2m[0m[0;2mWinner — test_winner#test_winner_discriminator[0m[2;32m[0m
[0;2mWord — [0;32m[0;34m[0;36m[0;34m[0;32m[0;35mЖОПАС[0m[0;32m[0m[0;34m[0m[0;36m[0m[0;34m[0m[0;32m[0m
Created by test_game_author#test_game_author_discriminator[0m[2;32m[4;32m[4;32m[0;32m[0m[4;32m[0m[4;32m[0m[2;32m[0m
```"""
        response_embed = await self.wordle_utils.create_finish_game_embed(
            interaction=interaction,
            result="win",
            word="жопас",
            game_author_id=12345,
            game_id=123,
        )

        interaction.guild.fetch_member.assert_called_with(12345)
        self.assertEqual(response_embed.title, title)
        self.assertEqual(response_embed.description, description)

    async def test_WordleGame(self) -> None:
        wordle_game = self.wordle_utils.WordleGame(
            embed=mock.MagicMock(),
            word="test_word",
            owner_id=12345,
            word_language="russian",
            lives_count=10,
            game_id=123,
            timeout=180,
        )

        interaction = mock.AsyncMock()
        interaction.user.id = 12345
        await wordle_game.guess_button.callback(interaction=interaction)

        interaction.response.send_message.assert_called_with(
            "You guessed a word, you can't guess!", ephemeral=True
        )

    @mock.patch("usagiBot.cogs.Wordle.wordle_utils.end_game")
    @mock.patch("usagiBot.cogs.Wordle.wordle_utils.create_full_wordle_pic")
    async def test_WordleAnswer_continue_play(
        self, mock_create_full_wordle_pic, mock_end_game
    ) -> None:
        wordle_game = self.wordle_utils.WordleGame(
            embed=mock.MagicMock(),
            word="ВЬЮГА",
            owner_id=1111,
            word_language="russian",
            lives_count=10,
            game_id=123,
            timeout=180,
        )
        wordle_answer = self.wordle_utils.WordleAnswer(
            game=wordle_game, title="Your answer!"
        )
        wordle_answer.children = [
            discord.ui.InputText(
                label="Answer",
                max_length=len(wordle_game.word),
                min_length=len(wordle_game.word),
                value="ванга",
            )
        ]
        interaction = mock.AsyncMock()
        await wordle_answer.callback(interaction)

        letter_blocks = [
            "green_block",
            "black_block",
            "black_block",
            "green_block",
            "green_block",
        ]
        green_letters = ["В", "А", "Г"]
        yellow_letters = []
        black_letters = ["А", "Н"]
        self.assertListEqual(letter_blocks, wordle_answer.letter_blocks)
        self.assertSetEqual(set(green_letters), set(wordle_game.green_letters))
        self.assertSetEqual(set(yellow_letters), set(wordle_game.yellow_letters))
        self.assertSetEqual(set(black_letters), set(wordle_game.black_letters))
        mock_end_game.assert_not_called()

    async def test_WordleAnswer_fake_word(self) -> None:
        wordle_game = self.wordle_utils.WordleGame(
            embed=mock.MagicMock(),
            word="test_word",
            owner_id=1234567890,
            word_language="russian",
            lives_count=10,
            game_id=123,
            timeout=180,
        )
        wordle_answer = self.wordle_utils.WordleAnswer(
            game=wordle_game, title="Your answer!"
        )
        wordle_answer.children = [
            discord.ui.InputText(
                label="Answer",
                max_length=len(wordle_game.word),
                min_length=len(wordle_game.word),
                value="ABOBA",
            )
        ]
        interaction = mock.AsyncMock()
        await wordle_answer.callback(interaction)

        interaction.response.send_message.assert_called_with(
            "This word is not in the dictionary <a:Tssk:883736146578915338>",
            ephemeral=True,
        )

    async def test_WordleAnswer_symbols_in_word(self) -> None:
        wordle_game = self.wordle_utils.WordleGame(
            embed=mock.MagicMock(),
            word="test_word",
            owner_id=1111,
            word_language="russian",
            lives_count=10,
            game_id=123,
            timeout=180,
        )
        wordle_answer = self.wordle_utils.WordleAnswer(
            game=wordle_game, title="Your answer!"
        )
        wordle_answer.children = [
            discord.ui.InputText(
                label="Answer",
                max_length=len(wordle_game.word),
                min_length=len(wordle_game.word),
                value="AB%BA",
            )
        ]
        interaction = mock.AsyncMock()
        await wordle_answer.callback(interaction)

        interaction.response.send_message.assert_called_with(
            "Your word contains symbols, pls guess real word.", ephemeral=True
        )

    @mock.patch("usagiBot.cogs.Wordle.wordle_utils.end_game")
    async def test_WordleAnswer_win_game(self, mock_end_game) -> None:
        wordle_game = self.wordle_utils.WordleGame(
            embed=mock.MagicMock(),
            word="РУЧКА",
            owner_id=3333,
            word_language="russian",
            lives_count=10,
            game_id=213123,
            timeout=180,
        )
        wordle_answer = self.wordle_utils.WordleAnswer(
            game=wordle_game, title="Your answer!"
        )
        wordle_answer.children = [
            discord.ui.InputText(
                label="Answer",
                max_length=len(wordle_game.word),
                min_length=len(wordle_game.word),
                value="ручка",
            )
        ]
        interaction = mock.AsyncMock()
        await wordle_answer.callback(interaction)

        mock_end_game.assert_called_with(
            interaction=interaction,
            result="win",
            word="РУЧКА",
            game_author_id=3333,
            lives_count=9,
            game_id=213123,
        )

    @mock.patch("usagiBot.cogs.Wordle.wordle_utils.end_game")
    async def test_WordleAnswer_lose_game(self, mock_end_game) -> None:
        wordle_game = self.wordle_utils.WordleGame(
            embed=mock.MagicMock(),
            word="ЗАЙЧИК",
            owner_id=2222,
            word_language="russian",
            lives_count=1,
            game_id=321,
            timeout=180,
        )
        wordle_answer = self.wordle_utils.WordleAnswer(
            game=wordle_game, title="Your answer!"
        )
        wordle_answer.children = [
            discord.ui.InputText(
                label="Answer",
                max_length=len(wordle_game.word),
                min_length=len(wordle_game.word),
                value="зайчиф",
            )
        ]
        interaction = mock.AsyncMock()
        await wordle_answer.callback(interaction)

        mock_end_game.assert_called_with(
            interaction=interaction,
            result="lose",
            word="ЗАЙЧИК",
            game_author_id=2222,
            game_id=321,
        )
