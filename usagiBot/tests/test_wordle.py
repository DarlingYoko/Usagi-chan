from unittest import mock
from unittest import IsolatedAsyncioTestCase
from sqlalchemy.ext import asyncio


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
        self.assertEqual(self.wordle_utils.get_word(length=5), "АББАТ")

