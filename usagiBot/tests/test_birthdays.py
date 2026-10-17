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
        self.mock_UsagiConfig.get_all_by.return_value = []  # no guild configured

        await self.Birthday.check_birthday.coro(self.Birthday)

        self.mock_UsagiBirthday.update.assert_not_called()

    @freeze_time("2026-06-13 09:00:00")
    async def test_check_birthday_batches_config_lookup(self) -> None:
        user = mock.MagicMock(guild_id="g1", user_id="u1", date=datetime(2026, 6, 13))
        self.mock_UsagiBirthday.get_all_by.return_value = [user]
        self.mock_UsagiConfig.get_all_by.return_value = [
            mock.MagicMock(guild_id="g1", generic_id="ch")
        ]
        channel = mock.AsyncMock()
        self.Birthday.bot.get_channel = mock.MagicMock(return_value=channel)

        await self.Birthday.check_birthday.coro(self.Birthday)

        self.mock_UsagiConfig.get_all_by.assert_awaited_once_with(command_tag="birthday")
        self.mock_UsagiConfig.get.assert_not_called()
        channel.send.assert_awaited_once()
        self.mock_UsagiBirthday.update.assert_awaited_once()

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

    @freeze_time("2026-06-13 12:00:00")  # day=13, month=6 — same year, not past
    async def test_birthday_add_creates_row(self) -> None:
        self.mock_UsagiBirthday.get.return_value = None
        await self.Birthday.birthday_add.callback(
            self.Birthday, self.ctx, mock.MagicMock(id=7), day=25, month=12, name="Bob"
        )
        self.mock_UsagiBirthday.create.assert_awaited_once()
        kwargs = self.mock_UsagiBirthday.create.await_args.kwargs
        self.assertEqual(kwargs["user_id"], 7)
        self.assertEqual(kwargs["name"], "Bob")
        self.assertEqual(kwargs["date"], datetime(2026, 12, 25))

    @freeze_time("2026-06-13 12:00:00")
    async def test_birthday_add_rolls_to_next_year_when_past(self) -> None:
        self.mock_UsagiBirthday.get.return_value = None
        await self.Birthday.birthday_add.callback(
            self.Birthday, self.ctx, mock.MagicMock(id=7), day=1, month=1
        )
        kwargs = self.mock_UsagiBirthday.create.await_args.kwargs
        self.assertEqual(kwargs["date"], datetime(2027, 1, 1))

    async def test_birthday_add_day_out_of_range(self) -> None:
        await self.Birthday.birthday_add.callback(
            self.Birthday, self.ctx, mock.MagicMock(id=7), day=40, month=1
        )
        self.ctx.respond.assert_awaited()
        self.mock_UsagiBirthday.create.assert_not_called()

    async def test_birthday_add_existing_user(self) -> None:
        self.mock_UsagiBirthday.get.return_value = mock.MagicMock()
        await self.Birthday.birthday_add.callback(
            self.Birthday, self.ctx, mock.MagicMock(id=7), day=1, month=1
        )
        self.ctx.respond.assert_awaited()
        self.mock_UsagiBirthday.create.assert_not_called()

    async def test_birthday_remove_deletes_row(self) -> None:
        self.mock_UsagiBirthday.get.return_value = mock.MagicMock()
        await self.Birthday.birthday_remove.callback(self.Birthday, self.ctx, "123")
        self.mock_UsagiBirthday.delete.assert_awaited_once_with(
            guild_id="g1", user_id=123
        )

    async def test_toggle_timer_flips_enable(self) -> None:
        self.mock_UsagiBirthdayTimer.get.return_value = mock.MagicMock(
            id=3, enable=True
        )
        await self.Birthday.toggle_timer.callback(self.Birthday, self.ctx)
        self.mock_UsagiBirthdayTimer.update.assert_awaited_once_with(
            id=3, enable=False
        )

    async def test_toggle_timer_no_timer(self) -> None:
        self.mock_UsagiBirthdayTimer.get.return_value = None
        await self.Birthday.toggle_timer.callback(self.Birthday, self.ctx)
        self.mock_UsagiBirthdayTimer.update.assert_not_called()
        self.ctx.respond.assert_awaited()

    async def test_add_birthday_timer_creates_when_absent(self) -> None:
        self.mock_UsagiBirthdayTimer.get.return_value = None
        channel = mock.MagicMock(id=99)
        await self.Birthday.add_birthday_timer.callback(
            self.Birthday, self.ctx, channel
        )
        self.mock_UsagiBirthdayTimer.create.assert_awaited_once_with(
            guild_id="g1", channel_id=99, enable=True
        )

    @freeze_time("2026-06-13 08:00:00")  # 11:00 Europe/Moscow — loop is a no-op
    async def test_check_birthday_returns_off_hour(self) -> None:
        await self.Birthday.check_birthday.coro(self.Birthday)
        self.mock_UsagiBirthday.get_all_by.assert_not_called()

    @freeze_time("2026-06-13 09:00:00")
    async def test_check_birthday_returns_when_no_users(self) -> None:
        self.mock_UsagiBirthday.get_all_by.return_value = []
        await self.Birthday.check_birthday.coro(self.Birthday)
        self.mock_UsagiConfig.get_all_by.assert_not_called()


class TestBirthdayHelpers(IsolatedAsyncioTestCase):
    def test_get_days_lists_1_to_31(self) -> None:
        from usagiBot.cogs.Birthdays.index import get_days

        days = get_days(mock.MagicMock())
        self.assertEqual(days, [str(x) for x in range(1, 32)])

    @mock.patch(
        "usagiBot.cogs.Birthdays.schemas.UsagiBirthday", new_callable=mock.AsyncMock
    )
    @mock.patch.object(asyncio, "create_async_engine")
    async def test_get_birthdays_builds_choices(self, _engine, mock_Birthday) -> None:
        from usagiBot.cogs.Birthdays.index import get_birthdays

        mock_Birthday.get_all_by.return_value = [mock.MagicMock(user_id=5)]
        ctx = mock.MagicMock()
        ctx.interaction.guild_id = "g1"
        member = mock.MagicMock(id=5)
        member.name = "Alice"
        guild = mock.MagicMock()
        guild.get_member.return_value = member
        ctx.bot.get_guild.return_value = guild

        choices = await get_birthdays(ctx)

        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0].name, "Alice")
        self.assertEqual(choices[0].value, "5")

    @mock.patch.object(asyncio, "create_async_engine")
    def test_setup_adds_cog(self, _engine) -> None:
        from usagiBot.cogs.Birthdays.index import setup

        bot = mock.MagicMock()
        bot.wait_until_ready = mock.AsyncMock()
        setup(bot)
        bot.add_cog.assert_called_once()
