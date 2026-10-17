import pytest


@pytest.fixture(autouse=True)
def _reset_sqlalchemy_metadata():
    """Isolate the shared declarative MetaData between tests.

    Many tests re-import cog modules (often under mock.patch) so the
    mocked model classes bind into the index namespace. Re-importing a
    module whose tables are still registered raises
    "Table '<x>' is already defined for this MetaData instance". The
    suite previously avoided this by luck of import order; clearing the
    metadata around every test makes it order-independent.
    """
    from usagiBot.db.base import Base

    Base.metadata.clear()
    yield
    Base.metadata.clear()
