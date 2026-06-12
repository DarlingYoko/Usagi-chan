from usagiBot.db.base import Base, async_session, engine
from sqlalchemy import (
    and_,
    or_,
)
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy.future import select


class ModelAdmin:
    @classmethod
    def generate_conditions(cls, kwargs: dict) -> list:
        conditions = []
        for attr, value in kwargs.items():
            column = getattr(cls, attr, None)
            if column is None:
                raise AttributeError(f"{cls.__name__} has no column {attr!r}")
            conditions.append(column == value)
        return conditions

    @classmethod
    async def create(cls, **kwargs) -> None:
        async with async_session() as session:
            async with session.begin():
                session.add(cls(**kwargs))

    @classmethod
    async def insert_mappings(cls, mappings) -> bool:
        async with async_session() as session:
            async with session.begin():
                session.add_all(mappings)
                return True

    @classmethod
    async def update(cls, id, **kwargs) -> None:
        query = (
            sqlalchemy_update(cls)
            .where(cls.id == id)
            .values(**kwargs)
            .execution_options(synchronize_session=False)
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)

    @classmethod
    async def update_all(cls, conditions: dict, new_values: dict) -> None:
        conditions = cls.generate_conditions(conditions)
        query = (
            sqlalchemy_update(cls)
            .where(and_(*conditions))
            .values(**new_values)
            .execution_options(synchronize_session=False)
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)

    @classmethod
    async def update_by_ids(cls, ids: list, new_values: dict) -> None:
        query = (
            sqlalchemy_update(cls)
            .where(cls.id.in_(ids))
            .values(**new_values)
            .execution_options(synchronize_session=False)
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)

    @classmethod
    async def delete(cls, **kwargs) -> None:
        conditions = cls.generate_conditions(kwargs)
        query = (
            sqlalchemy_delete(cls)
            .where(and_(*conditions))
            .execution_options(synchronize_session=False)
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)

    @classmethod
    async def delete_all(cls, ids: list) -> None:
        query = (
            sqlalchemy_delete(cls)
            .where(cls.id.in_(ids))
            .execution_options(synchronize_session=False)
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)

    @classmethod
    async def get(cls, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = select(cls).where(and_(*conditions))
        async with async_session() as session:
            results = await session.execute(query)
            return results.scalars().first()

    @classmethod
    async def get_all_by(cls, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = select(cls).where(and_(*conditions))
        async with async_session() as session:
            results = await session.execute(query)
            return results.scalars().all()

    @classmethod
    async def get_all_by_or(cls, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = select(cls).where(or_(*conditions))
        async with async_session() as session:
            results = await session.execute(query)
            return results.scalars().all()

    @classmethod
    async def get_all(cls):
        query = select(cls)
        async with async_session() as session:
            results = await session.execute(query)
            return results.scalars().all()

    @classmethod
    async def get_due(cls, date):
        """Rows whose `date` column is at or before the given moment."""
        query = select(cls).where(cls.date <= date)
        async with async_session() as session:
            results = await session.execute(query)
            return results.scalars().all()

    @classmethod
    async def get_last_obj(cls):
        query = select(cls).order_by(cls.id.desc())
        async with async_session() as session:
            results = await session.execute(query)
            return results.scalars().first()

    @classmethod
    async def get_last_n(cls, limit: int = 10, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = (
            select(cls).where(and_(*conditions)).order_by(cls.id.desc()).limit(limit)
        )
        async with async_session() as session:
            results = await session.execute(query)
            return results.scalars().all()

    @classmethod
    async def get_embedding(cls, query_vec, limit: int = 10, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = (
            select(cls)
            .where(and_(*conditions))
            .order_by(cls.embedding.l2_distance(query_vec))
            .limit(limit)
        )
        async with async_session() as session:
            results = await session.execute(query)
            return results.scalars().all()


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
