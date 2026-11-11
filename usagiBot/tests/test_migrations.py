import re
import sys
import tempfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, TestCase, mock

from usagiBot.tests.utils import *  # noqa: F401,F403 — sets required env vars

COGS_PATH = Path("usagiBot/cogs")


def _forget_schema_modules() -> None:
    """Drop cached schema modules so importing them re-registers their tables
    (conftest clears Base.metadata around every test)."""
    for name in list(sys.modules):
        if name.startswith("usagiBot.cogs.") and name.endswith(".schemas"):
            del sys.modules[name]


def _declared_tablenames() -> set[str]:
    names: set[str] = set()
    for schema in COGS_PATH.glob("*/schemas.py"):
        names.update(
            re.findall(r'__tablename__\s*=\s*"([^"]+)"', schema.read_text("utf-8"))
        )
    return names


class TestLoadAllModels(TestCase):
    def setUp(self) -> None:
        _forget_schema_modules()

    def test_registers_every_cog_table(self) -> None:
        from usagiBot.db.base import Base
        from usagiBot.db.migrate import load_all_models

        load_all_models()

        expected = _declared_tablenames()
        self.assertTrue(expected, "no __tablename__ found — glob path wrong?")
        self.assertLessEqual(expected, set(Base.metadata.tables))

    def test_hot_path_indexes_are_declared_on_models(self) -> None:
        # These used to exist only in a hand-applied SQL file; autogenerate
        # would propose dropping them unless the models declare them.
        from usagiBot.db.base import Base
        from usagiBot.db.migrate import load_all_models

        load_all_models()

        declared = {
            index.name
            for table in Base.metadata.tables.values()
            for index in table.indexes
        }
        self.assertLessEqual(
            {
                "ix_usagi_hoyolab_guild_user",
                "ix_usagi_birthday_guild_user",
                "ix_usagi_twitch_notify_guild_user",
                "ix_usagi_wordle_results_guild_user",
                "ix_usagi_member_roles_guild_user",
                "ix_usagi_gryphline_guild_user",
                "ix_usagi_config_guild_tag",
                "ix_usagi_auto_roles_data_message",
                "ix_usagi_wordle_results_guild_points",
            },
            declared,
        )


class TestRevisionScripts(TestCase):
    def test_single_head_rooted_at_baseline(self) -> None:
        from alembic.script import ScriptDirectory

        from usagiBot.db.migrate import BASELINE_REVISION, alembic_config

        script = ScriptDirectory.from_config(alembic_config())

        self.assertEqual(len(script.get_heads()), 1, "branched migration history")
        self.assertEqual(script.get_bases(), [BASELINE_REVISION])


class TestRunMigrations(TestCase):
    def _run(self, existing_tables: list[str]) -> tuple[mock.MagicMock, mock.MagicMock]:
        from usagiBot.db import migrate

        connection = mock.MagicMock(name="sync_connection")
        inspector = mock.MagicMock()
        inspector.get_table_names.return_value = existing_tables
        with mock.patch.object(migrate, "inspect", return_value=inspector), \
                mock.patch.object(migrate.command, "stamp") as stamp, \
                mock.patch.object(migrate.command, "upgrade") as upgrade:
            migrate.run_migrations(connection)

        upgrade.assert_called_once()
        config, target = upgrade.call_args.args
        self.assertEqual(target, "head")
        self.assertIs(config.attributes["connection"], connection)
        return stamp, upgrade

    def test_fresh_database_only_upgrades(self) -> None:
        stamp, _ = self._run([])
        stamp.assert_not_called()

    def test_versioned_database_only_upgrades(self) -> None:
        stamp, _ = self._run(["alembic_version", "usagi_config"])
        stamp.assert_not_called()

    def test_legacy_database_is_stamped_at_baseline_before_upgrade(self) -> None:
        from usagiBot.db.migrate import BASELINE_REVISION

        calls = mock.MagicMock()
        from usagiBot.db import migrate

        connection = mock.MagicMock()
        inspector = mock.MagicMock()
        inspector.get_table_names.return_value = ["usagi_config", "usagi_hoyolab"]
        with mock.patch.object(migrate, "inspect", return_value=inspector), \
                mock.patch.object(migrate.command, "stamp", calls.stamp), \
                mock.patch.object(migrate.command, "upgrade", calls.upgrade):
            migrate.run_migrations(connection)

        self.assertEqual(
            [c[0] for c in calls.mock_calls], ["stamp", "upgrade"]
        )
        self.assertEqual(calls.stamp.call_args.args[1], BASELINE_REVISION)


class TestBeforeIdentifyHook(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._cogs_dir = tempfile.TemporaryDirectory()
        patcher = mock.patch("usagiBot.env.COGS_DIR", self._cogs_dir.name)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._cogs_dir.cleanup)
        # Fresh import so usagi.py binds the patched upgrade/init functions;
        # drop it afterwards so the mocks don't leak into later tests.
        sys.modules.pop("usagiBot.usagi", None)
        self.addCleanup(sys.modules.pop, "usagiBot.usagi", None)

    @mock.patch("usagiBot.src.UsagiUtils.init_language", new_callable=mock.AsyncMock)
    @mock.patch("usagiBot.db.migrate.upgrade_database", new_callable=mock.AsyncMock)
    async def test_first_connect_runs_migrations(self, upgrade, language) -> None:
        from usagiBot.usagi import bot

        await bot.before_identify_hook(0, initial=True)

        upgrade.assert_awaited_once()
        language.assert_awaited_once()

    @mock.patch("usagiBot.src.UsagiUtils.init_language", new_callable=mock.AsyncMock)
    @mock.patch("usagiBot.db.migrate.upgrade_database", new_callable=mock.AsyncMock)
    async def test_reconnect_skips_migrations(self, upgrade, language) -> None:
        from usagiBot.usagi import bot

        await bot.before_identify_hook(0, initial=False)

        upgrade.assert_not_awaited()
        language.assert_not_awaited()
