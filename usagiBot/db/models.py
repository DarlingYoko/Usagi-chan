from usagiBot.db.base import Base, async_session, engine
from sqlalchemy import Text, BigInteger, Boolean
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

    # @classmethod
    # async def update(cls, id, **kwargs):
    #     query = (
    #         sqlalchemy_update(cls)
    #         .where(cls.id == id)
    #         .values(**kwargs)
    #         .execution_options(synchronize_session="fetch")
    #     )
    #     async with async_session() as session:
    #         async with session.begin():
    #             await session.execute(query)
    #             await session.commit()

    @classmethod
    async def get_command_tag(cls, guild_id, command_tag):
        query = select(cls).where(
            cls.guild_id == guild_id, cls.command_tag == command_tag
        )
        async with async_session() as session:
            async with session.begin():
                results = await session.execute(query)
                config = results.scalars().first()
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
    async def delete_command_tag(cls, guild_id, command_tag):
        query = (
            sqlalchemy_delete(cls)
            .where(cls.guild_id == guild_id, cls.command_tag == command_tag)
            .execution_options(synchronize_session="fetch")
        )
        async with async_session() as session:
            async with session.begin():
                await session.execute(query)
                await session.commit()

    @classmethod
    async def delete_module_name(cls, guild_id, module_name):
        query = (
            sqlalchemy_delete(cls)
            .where(cls.guild_id == guild_id, cls.module_name == module_name)
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


class UsagiCogs(Base, ModelAdmin):
    __tablename__ = "usagi_cogs"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    module_name = Column(Text)
    access = Column(Boolean)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
