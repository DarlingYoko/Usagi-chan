import datetime
import sys
from unittest import IsolatedAsyncioTestCase, mock

import pytest
from sqlalchemy.ext import asyncio as sa_asyncio

from usagiBot.tests.utils import *


@pytest.fixture(autouse=True)
def clear_imports():
    # Same isolation as test_genshin.py: other Hoyolab tests patch these
    # modules at import time, so don't leave ours cached.
    from usagiBot.db.base import Base

    Base.metadata.clear()
    initial_modules = dict(sys.modules)
    yield
    for module in list(sys.modules.keys()):
        if module not in initial_modules:
            del sys.modules[module]


GENSHIN_LABEL = "Resin count:"
STARRAIL_LABEL = "Trailblaze power count:"
ZZZ_LABEL = "Energy count:"


def make_user(user_id: int, **overrides) -> mock.MagicMock:
    flags = {"show_genshin": True, "show_starrail": True, "show_zzz": True}
    flags.update(overrides)
    return mock.MagicMock(id=user_id, user_id=1, **flags)


def make_notes() -> dict:
    return {
        "genshin": mock.MagicMock(
            remaining_resin_recovery_time=datetime.timedelta(hours=2),
            remaining_realm_currency_recovery_time=datetime.timedelta(hours=10),
            current_resin=100,
            current_realm_currency=1400,
            max_realm_currency=1600,
            claimed_commission_reward=True,
            completed_commissions=4,
        ),
        "starrail": mock.MagicMock(
            current_stamina=100,
            stamina_recover_time=datetime.timedelta(hours=1),
            accepted_expedition_num=1,
            total_expedition_num=4,
        ),
        "zzz": mock.MagicMock(
            battery_charge=mock.MagicMock(current=100, max=240, seconds_till_full=3600),
            engagement=mock.MagicMock(current=1, max=400),
            scratch_card_completed=True,
        ),
    }


def make_data(nickname: str = "Monopolia") -> dict:
    return {"nickname": nickname, "icon": None, "geetest_error": None, **make_notes()}


class TestResinFieldsFilter(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        import usagiBot.cogs.Hoyolab.genshin_utils as genshin_utils

        init_i18n()
        self.generate_fields = genshin_utils.generate_fields

    def _names(self, fields) -> list[str]:
        return [field.name for field in fields]

    def test_all_games_when_no_filter(self) -> None:
        names = self._names(self.generate_fields(make_data()))

        self.assertIn(GENSHIN_LABEL, names)
        self.assertIn(STARRAIL_LABEL, names)
        self.assertIn(ZZZ_LABEL, names)

    def test_only_requested_games_are_rendered(self) -> None:
        names = self._names(self.generate_fields(make_data(), games=["genshin", "zzz"]))

        self.assertIn(GENSHIN_LABEL, names)
        self.assertIn(ZZZ_LABEL, names)
        self.assertNotIn(STARRAIL_LABEL, names)


class TestGetUserDataGames(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        import usagiBot.cogs.Hoyolab.genshin_utils as genshin_utils

        self.genshin_utils = genshin_utils
        self.api = genshin_utils.HoyolabAPI()
        self.api.client = mock.MagicMock()
        self.api.client.get_hoyolab_user = mock.AsyncMock(
            return_value=mock.MagicMock(nickname="Monopolia", icon="i")
        )
        for game in ("genshin", "starrail", "zzz"):
            setattr(self.api.client, f"get_{game}_notes", mock.AsyncMock())

    async def _get(self, **kwargs) -> dict:
        with mock.patch.object(
            self.genshin_utils, "UsagiHoyolab", new_callable=mock.AsyncMock
        ) as mock_hoyolab:
            mock_hoyolab.get.return_value = mock.MagicMock(
                ltuid_v2="1", ltmid_v2="2", ltoken_v2="3", cookie_token_v2="4"
            )
            return await self.api.get_user_data(db_id=1, **kwargs)

    async def test_fetches_every_game_by_default(self) -> None:
        data = await self._get()

        self.assertTrue({"genshin", "starrail", "zzz"} <= set(data))

    async def test_skips_games_that_are_not_requested(self) -> None:
        # Fewer API calls, and no geetest/AccountNotFound noise from a game
        # the user switched off for this account.
        data = await self._get(games=["genshin"])

        self.api.client.get_genshin_notes.assert_awaited_once()
        self.api.client.get_starrail_notes.assert_not_called()
        self.api.client.get_zzz_notes.assert_not_called()
        self.assertIn("genshin", data)
        self.assertNotIn("starrail", data)


class TestResinView(IsolatedAsyncioTestCase):
    @mock.patch.object(sa_asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        import usagiBot.cogs.Hoyolab.resin_view as resin_view

        init_i18n()
        self.resin_view = resin_view
        self.update_patch = mock.patch.object(
            resin_view, "UsagiHoyolab", new_callable=mock.AsyncMock
        )
        self.mock_UsagiHoyolab = self.update_patch.start()
        self.addCleanup(self.update_patch.stop)

    def _account(self, user_id: int, nickname="Monopolia", data=None, **flags):
        user = make_user(user_id, **flags)
        if data is None:
            data = make_data(nickname)
        return self.resin_view.ResinAccount(user=user, data=data)

    def _view(self, accounts, loader=None, editable=True):
        return self.resin_view.ResinView(
            accounts, loader or mock.AsyncMock(), editable=editable
        )

    @staticmethod
    def _pick(select, *values) -> None:
        select._interaction = mock.MagicMock()
        select._selected_values = list(values)

    def _interaction(self) -> mock.MagicMock:
        interaction = mock.MagicMock()
        interaction.response.edit_message = mock.AsyncMock()
        interaction.response.defer = mock.AsyncMock()
        interaction.edit_original_response = mock.AsyncMock()
        return interaction

    async def test_accounts_with_same_nickname_get_unique_values(self) -> None:
        # Discord rejects a select whose options share a value, which used to
        # blow up the whole command once a second account had the same name.
        view = self._view([self._account(1, "Same"), self._account(2, "Same")])

        values = [option.value for option in view.account_select.options]

        self.assertEqual(values, ["1", "2"])

    async def test_dead_account_stays_listed_with_placeholder(self) -> None:
        view = self._view([self._account(1, data={}), self._account(2, "Monopolia")])

        labels = [option.label for option in view.account_select.options]

        self.assertEqual(len(labels), 2)
        self.assertIn("#1", labels[0])
        self.assertEqual(labels[1], "Monopolia")

    async def test_first_account_with_data_is_shown_first(self) -> None:
        view = self._view([self._account(1, data={}), self._account(2)])

        self.assertEqual(view.current.user.id, 2)
        self.assertTrue(view.account_select.options[1].default)

    async def test_dead_account_renders_relogin_hint(self) -> None:
        view = self._view([self._account(1, data={})])

        embed = view.render()["embed"]

        self.assertIn("out of date", embed.description)

    async def test_games_row_reflects_account_flags(self) -> None:
        view = self._view([self._account(1, show_starrail=False)])

        defaults = {o.value: o.default for o in view.games_select.options}

        self.assertEqual(defaults, {"genshin": True, "starrail": False, "zzz": True})

    async def test_embed_hides_disabled_games(self) -> None:
        view = self._view([self._account(1, show_starrail=False)])

        names = [field.name for field in view.render()["embed"].fields]

        self.assertIn(GENSHIN_LABEL, names)
        self.assertNotIn(STARRAIL_LABEL, names)

    async def test_non_owner_gets_no_games_row(self) -> None:
        view = self._view([self._account(1)], editable=False)

        self.assertIsNone(view.games_select)
        self.assertEqual(len(view.children), 1)

    async def test_disabling_a_game_updates_the_message_right_away(self) -> None:
        loader = mock.AsyncMock()
        account = self._account(7)
        view = self._view([account], loader)
        interaction = self._interaction()
        self._pick(view.games_select, "genshin", "zzz")

        await view.games_select.callback(interaction)

        self.mock_UsagiHoyolab.update.assert_awaited_once_with(
            id=7, show_genshin=True, show_starrail=False, show_zzz=True
        )
        self.assertFalse(account.user.show_starrail)
        # The data is already loaded: no slow refetch, one plain message edit.
        loader.assert_not_called()
        interaction.response.defer.assert_not_called()
        interaction.edit_original_response.assert_not_called()
        kwargs = interaction.response.edit_message.call_args.kwargs
        names = [f.name for f in kwargs["embed"].fields]
        self.assertNotIn(STARRAIL_LABEL, names)
        self.assertIn(GENSHIN_LABEL, names)
        self.assertIs(kwargs["view"], view)
        defaults = {o.value: o.default for o in view.games_select.options}
        self.assertFalse(defaults["starrail"])

    async def test_enabling_a_game_without_data_fetches_it(self) -> None:
        data = make_data()
        del data["starrail"]
        loader = mock.AsyncMock(return_value=make_data())
        account = self._account(7, data=data, show_starrail=False)
        view = self._view([account], loader)
        interaction = self._interaction()
        self._pick(view.games_select, "genshin", "starrail", "zzz")

        await view.games_select.callback(interaction)

        # Acknowledge with the old data first, then swap in the fetched one.
        interaction.response.edit_message.assert_awaited_once()
        loader.assert_awaited_once_with(account.user)
        interaction.edit_original_response.assert_awaited_once()
        names = [
            f.name
            for f in interaction.edit_original_response.call_args.kwargs["embed"].fields
        ]
        self.assertIn(STARRAIL_LABEL, names)

    async def test_switching_account_updates_games_defaults(self) -> None:
        view = self._view(
            [self._account(1, "A"), self._account(2, "B", show_zzz=False)]
        )
        interaction = self._interaction()
        self._pick(view.account_select, "2")

        await view.account_select.callback(interaction)

        self.assertEqual(view.current.user.id, 2)
        defaults = {o.value: o.default for o in view.games_select.options}
        self.assertFalse(defaults["zzz"])
        embed = interaction.response.edit_message.call_args.kwargs["embed"]
        self.assertEqual(embed.author.name, "B")

    async def test_geetest_warning_is_part_of_the_message(self) -> None:
        data = make_data()
        data["geetest_error"] = "starrail"
        view = self._view([self._account(1, data=data)])

        content = view.render()["content"]

        self.assertIn("starrail", content)
