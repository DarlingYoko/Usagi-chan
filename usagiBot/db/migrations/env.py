import asyncio
from logging.config import fileConfig
from typing import Any, Literal

from alembic import context
from alembic.autogenerate.api import AutogenContext
from pgvector.sqlalchemy import Vector
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from usagiBot.db.base import DATABASE_URL, Base
from usagiBot.db.migrate import load_all_models
from usagiBot.db.types import EncryptedText

config = context.config

# Only the CLI has an ini file; when the bot runs migrations in-process its
# own logging setup must not be replaced.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

load_all_models()
target_metadata = Base.metadata


def include_object(
    obj: Any, name: str | None, type_: str, reflected: bool, compare_to: Any
) -> bool:
    # Never autogenerate a DROP for a table no model describes (manual or
    # leftover tables): removing data must be a hand-written decision.
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def render_item(
    type_: str, obj: Any, autogen_context: AutogenContext
) -> str | Literal[False]:
    # Keep revisions free of app imports: encryption is an ORM-level concern,
    # the column is plain TEXT in the database.
    if type_ == "type" and isinstance(obj, EncryptedText):
        return "sa.Text()"
    if type_ == "type" and isinstance(obj, Vector):
        autogen_context.imports.add("from pgvector.sqlalchemy import Vector")
        return f"Vector({obj.dim})"
    return False


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        render_item=render_item,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
        await connection.commit()
    await engine.dispose()


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
elif (connection := config.attributes.get("connection")) is not None:
    # In-process: usagiBot.db.migrate.upgrade_database hands over its
    # connection; the caller owns the transaction.
    do_run_migrations(connection)
else:
    asyncio.run(run_async_migrations())
