from usagiBot.db.base import Base, async_session
from sqlalchemy import Text, BigInteger
from sqlalchemy import Column, Integer
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy.future import select


class ModelAdmin:
    @classmethod
    async def create(cls, **kwargs):
        async with async_session() as session:
            async with session.begin():
                session.add(cls(**kwargs))
                await session.commit()

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
    async def get(cls, guild_id, command_tag):
        query = select(cls).where(
            cls.guild_id == guild_id, cls.command_tag == command_tag
        )
        async with async_session() as session:
            async with session.begin():
                results = await session.execute(query)
                config = results.scalars().first()
                return config

    @classmethod
    async def delete(cls, guild_id, command_tag):
        query = (
            sqlalchemy_delete(cls)
            .where(cls.guild_id == guild_id, cls.command_tag == command_tag)
            .execution_options(synchronize_session="fetch")
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)
                await session.commit()


class UsagiConfig(Base, ModelAdmin):
    __tablename__ = "usagi_config"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    command_tag = Column(Text)
    generic_id = Column(BigInteger)
