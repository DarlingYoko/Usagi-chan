from usagiBot.db.base import Base, async_session, engine
from sqlalchemy import Text, BigInteger, Boolean, Column, Integer, DateTime, and_
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy.future import select


class ModelAdmin:

    @classmethod
    def generate_conditions(cls, kwargs):
        conditions = [
            getattr(cls, attr) == kwargs.get(attr)
            for attr in kwargs.keys()
        ]
        return conditions

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


class UsagiModerRoles(Base, ModelAdmin):
    __tablename__ = "usagi_moder_roles"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    moder_role_id = Column(BigInteger)


class UsagiWordleGames(Base, ModelAdmin):
    __tablename__ = "usagi_wordle_games"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    word = Column(Text)
    owner_id = Column(BigInteger)
    thread_id = Column(BigInteger)


class UsagiWordleResults(Base, ModelAdmin):
    __tablename__ = "usagi_wordle_results"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    points = Column(BigInteger)
    count_of_games = Column(BigInteger)


class UsagiUnicRoles(Base, ModelAdmin):
    __tablename__ = "usagi_unic_roles"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    role_id = Column(BigInteger)


class UsagiTwitchNotify(Base, ModelAdmin):
    __tablename__ = "usagi_twitch_notify"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    twitch_username = Column(Text)
    last_time_start = Column(DateTime)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
