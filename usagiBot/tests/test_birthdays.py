import sys
import pytest

from datetime import datetime, timedelta
from sqlalchemy.ext import asyncio
from unittest import IsolatedAsyncioTestCase, mock
from freezegun import freeze_time

from usagiBot.tests.utils import *


@pytest.fixture(autouse=True)
def clear_imports():
    from usagiBot.db.base import Base
    Base.metadata.clear()
    initial_modules = dict(sys.modules)
    yield
    for module in list(sys.modules.keys()):
        if module not in initial_modules:
            del sys.modules[module]


class TestBirthdayCommands(IsolatedAsyncioTestCase):
    @mock.patch("usagiBot.cogs.Main.schemas.UsagiConfig", new_callable=mock.AsyncMock)
    @mock.patch(
        "usagiBot.cogs.Birthdays.schemas.UsagiBirthdayTimer",
        new_callable=mock.AsyncMock,
    )
    @mock.patch(
        "usagiBot.cogs.Birthdays.schemas.UsagiBirthday", new_callable=mock.AsyncMock
    )
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(
        self, mock_engine, mock_Birthday, mock_BirthdayTimer, mock_Config
    ) -> None:
        from usagiBot.cogs.Birthdays.index import Birthday

        self.Birthday = Birthday
        self.mock_UsagiBirthday = mock_Birthday
        self.mock_UsagiBirthdayTimer = mock_BirthdayTimer
        self.mock_UsagiConfig = mock_Config

        self.Birthday.bot = mock.MagicMock()
        self.Birthday.bot.fetch_channel = mock.AsyncMock()
        self.Birthday.bot.i18n = init_i18n()
        self.Birthday.bot.language = {}

        self.ctx = mock.AsyncMock()
        self.ctx.guild.id = "g1"

    async def test_birthday_add_invalid_date_responds(self) -> None:
        self.mock_UsagiBirthday.get.return_value = None
        await self.Birthday.birthday_add.callback(
            self.Birthday, self.ctx, mock.MagicMock(id=7), day=31, month=2
        )
        self.ctx.respond.assert_awaited()
        self.mock_UsagiBirthday.create.assert_not_called()

    async def test_birthday_remove_not_in_list_responds(self) -> None:
        self.mock_UsagiBirthday.get.return_value = None
        await self.Birthday.birthday_remove.callback(self.Birthday, self.ctx, "123")
        self.ctx.respond.assert_awaited()

    async def test_add_birthday_timer_uses_channel_id_column(self) -> None:
        self.mock_UsagiBirthdayTimer.get.return_value = mock.MagicMock(id=5)
        channel = mock.MagicMock(id=99)
        await self.Birthday.add_birthday_timer.callback(
            self.Birthday, self.ctx, channel
        )
        self.mock_UsagiBirthdayTimer.update.assert_awaited_with(id=5, channel_id=99)

    async def test_update_timer_continues_past_guild_without_birthday(self) -> None:
        self.mock_UsagiBirthdayTimer.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", channel_id="c1"),
            mock.MagicMock(guild_id="g2", channel_id="c2"),
        ]
        self.mock_UsagiBirthday.get_all_by.return_value = []

        await self.Birthday.update_birthday_timer.coro(self.Birthday)

        self.assertEqual(self.mock_UsagiBirthday.get_all_by.call_count, 2)

    async def test_update_timer_does_not_sleep(self) -> None:
        future = datetime.now() + timedelta(days=2)
        bday = mock.MagicMock(date=future)
        bday.name = "Alice"
        self.mock_UsagiBirthdayTimer.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", channel_id="c1")
        ]
        self.mock_UsagiBirthday.get_all_by.return_value = [bday]

        channel = mock.AsyncMock()
        channel.category_id = "cat1"
        category = mock.AsyncMock()
        category.name = "different"
        self.Birthday.bot.get_channel = mock.MagicMock(side_effect=[channel, category])

        with mock.patch("asyncio.sleep", new_callable=mock.AsyncMock) as mock_sleep:
            await self.Birthday.update_birthday_timer.coro(self.Birthday)

        mock_sleep.assert_not_called()
        channel.edit.assert_awaited()

    @freeze_time("2026-06-13 09:00:00")  # 12:00 Europe/Moscow, when the loop runs
    async def test_check_birthday_skips_when_config_none(self) -> None:
        user = mock.MagicMock(guild_id="g1", user_id="u1", date=datetime(2026, 6, 13))
        self.mock_UsagiBirthday.get_all_by.return_value = [user]
        self.mock_UsagiConfig.get.return_value = None
        guild = mock.AsyncMock()
        self.Birthday.bot.fetch_guild = mock.AsyncMock(return_value=guild)

        await self.Birthday.check_birthday.coro(self.Birthday)

        guild.fetch_channel.assert_not_called()
        self.mock_UsagiBirthday.update.assert_not_called()

    @freeze_time("2026-06-13 09:00:00")
    async def test_check_birthday_survives_db_error(self) -> None:
        self.mock_UsagiBirthday.get_all_by.side_effect = Exception("db down")

        await self.Birthday.check_birthday.coro(self.Birthday)

        self.Birthday.bot.logger.exception.assert_called()

    async def test_update_birthday_timer_survives_deleted_channel(self) -> None:
        self.mock_UsagiBirthdayTimer.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", channel_id="dead")
        ]
        self.Birthday.bot.get_channel = mock.MagicMock(return_value=None)
        self.Birthday.bot.fetch_channel = mock.AsyncMock(
            side_effect=Exception("gone")
        )

        await self.Birthday.update_birthday_timer.coro(self.Birthday)

        self.Birthday.bot.logger.exception.assert_called()
