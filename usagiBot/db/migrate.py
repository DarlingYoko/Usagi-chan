"""Alembic wiring: run schema migrations at startup and expose the full
model metadata for autogenerate.

The bot applies migrations itself on first connect (``upgrade_database``),
so a deploy needs no manual SQL step. The ``alembic`` CLI (``alembic.ini``
at the repo root) is for authoring revisions and for manual stamp/downgrade.
"""
import importlib
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, inspect

ALEMBIC_DIR = Path(__file__).resolve().parent / "migrations"
COGS_DIR = Path(__file__).resolve().parents[1] / "cogs"

# First revision: the schema as it stood when Alembic was introduced
# (create_all output + the four hand-applied SQL files in old migrations/).
BASELINE_REVISION = "0001_baseline"
VERSION_TABLE = "alembic_version"
# Present in every database the bot ever booted against with create_all.
LEGACY_MARKER_TABLE = "usagi_config"

logger = logging.getLogger("usagi")


def load_all_models() -> None:
    """Import every cog's ``schemas`` module so ``Base.metadata`` describes
    the whole schema, even when the cogs themselves aren't loaded (CLI)."""
    for schema in sorted(COGS_DIR.glob("*/schemas.py")):
        importlib.import_module(f"usagiBot.cogs.{schema.parent.name}.schemas")


def alembic_config(connection: Connection | None = None) -> Config:
    """Config for programmatic use; independent of the working directory."""
    config = Config()
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def run_migrations(connection: Connection) -> None:
    """Bring the database to the latest revision (sync; run via run_sync).

    A pre-Alembic database (tables exist, no version table) already matches
    the baseline, so it is stamped there instead of re-creating its tables.
    """
    config = alembic_config(connection)
    tables = set(inspect(connection).get_table_names())
    if VERSION_TABLE not in tables and LEGACY_MARKER_TABLE in tables:
        logger.warning(
            "Pre-Alembic database detected; stamping it at %s", BASELINE_REVISION
        )
        command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, "head")


async def upgrade_database() -> None:
    from usagiBot.db.base import engine

    async with engine.begin() as connection:
        await connection.run_sync(run_migrations)
