import sys
import pytest

from sqlalchemy.ext import asyncio
from unittest import IsolatedAsyncioTestCase, mock

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


class _FakeResult:
    def scalars(self):
        return self

    def all(self):
        return ["row"]


class _FakeSession:
    def __init__(self) -> None:
        self.query = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def execute(self, query):
        self.query = query
        return _FakeResult()


class TestGetTop(IsolatedAsyncioTestCase):
    @mock.patch.object(asyncio, "create_async_engine")
    def setUp(self, mock_engine) -> None:
        from usagiBot.cogs.Wordle.schemas import UsagiWordleResults

        self.Model = UsagiWordleResults

    async def test_get_top_orders_desc_with_limit_in_sql(self) -> None:
        session = _FakeSession()
        with mock.patch(
            "usagiBot.db.models.async_session", return_value=session
        ):
            rows = await self.Model.get_top(order_by="points", limit=5, guild_id=123)

        self.assertEqual(rows, ["row"])
        sql = str(session.query)
        self.assertIn("ORDER BY", sql)
        self.assertIn("points DESC", sql)
        self.assertIn("LIMIT", sql)

    async def test_get_top_unknown_column_raises(self) -> None:
        with self.assertRaises(AttributeError):
            await self.Model.get_top(order_by="does_not_exist")
