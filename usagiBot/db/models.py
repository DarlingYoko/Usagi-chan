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
    def generate_conditions(cls, kwargs):
        conditions = [getattr(cls, attr) == kwargs.get(attr) for attr in kwargs.keys()]
        return conditions

    @classmethod
    async def create(cls, **kwargs):
        async with async_session() as session:
            async with session.begin():
                session.add(cls(**kwargs))
                await session.commit()

    @classmethod
    async def insert_mappings(cls, mappings):
        async with async_session() as session:
            async with session.begin():
                session.add_all(mappings)
                return True

    @classmethod
    async def update(cls, id, **kwargs):
        query = (
            sqlalchemy_update(cls)
            .where(cls.id == id)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)
                await session.commit()

    @classmethod
    async def update_all(cls, conditions, new_values):
        conditions = cls.generate_conditions(conditions)
        query = (
            sqlalchemy_update(cls)
            .where(and_(*conditions))
            .values(**new_values)
            .execution_options(synchronize_session="fetch")
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)
                await session.commit()

    @classmethod
    async def delete(cls, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = (
            sqlalchemy_delete(cls)
            .where(and_(*conditions))
            .execution_options(synchronize_session="fetch")
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)
                await session.commit()

    @classmethod
    async def delete_all(cls, ids):
        query = (
            sqlalchemy_delete(cls)
            .where(cls.id.in_(ids))
            .execution_options(synchronize_session="fetch")
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)
                await session.commit()

    @classmethod
    async def get(cls, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = select(cls).where(and_(*conditions))
        async with async_session() as session:
            async with session.begin():
                results = await session.execute(query)
                response = results.scalars().first()
                return response

    @classmethod
    async def get_all_by(cls, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = select(cls).where(and_(*conditions))
        async with async_session() as session:
            async with session.begin():
                results = await session.execute(query)
                config = results.scalars().all()
                return config

    @classmethod
    async def get_all_by_or(cls, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = select(cls).where(or_(*conditions))
        async with async_session() as session:
            async with session.begin():
                results = await session.execute(query)
                config = results.scalars().all()
                return config

    @classmethod
    async def get_all(cls):
        query = select(cls)
        async with async_session() as session:
            async with session.begin():
                results = await session.execute(query)
                config = results.scalars().all()
                return config

    @classmethod
    async def get_last_obj(cls):
        query = select(cls).order_by(cls.id.desc())
        async with async_session() as session:
            async with session.begin():
                results = await session.execute(query)
                config = results.scalars().first()
                return config

    @classmethod
    async def get_last_n(cls, limit=10, **kwargs):
        conditions = cls.generate_conditions(kwargs)
        query = (
            select(cls).where(and_(*conditions)).order_by(cls.id.desc()).limit(limit)
        )
        async with async_session() as session:
            async with session.begin():
                results = await session.execute(query)
                objects = results.scalars().all()
                return objects

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
            async with session.begin():
                results = await session.execute(query)
                messages = results.scalars().all()
                return messages


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
