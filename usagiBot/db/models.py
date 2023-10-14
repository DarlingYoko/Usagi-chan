from usagiBot.db.base import Base, async_session, engine
from sqlalchemy import Text, BigInteger, Boolean, Column, Integer, DateTime, ForeignKey, and_, or_
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
    started_at = Column(DateTime)


class UsagiHoyolab(Base, ModelAdmin):
    __tablename__ = "usagi_hoyolab"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    ltuid = Column(Text)
    ltoken = Column(Text)
    cookie_token = Column(Text)
    genshin_resin_sub = Column(Boolean)
    genshin_resin_sub_notified = Column(Boolean)
    genshin_daily_sub = Column(Boolean)
    daily_notify_sub = Column(Boolean)
    starrail_daily_sub = Column(Boolean)
    starrail_resin_sub = Column(Boolean)
    starrail_resin_sub_notified = Column(Boolean)


class UsagiSaveRoles(Base, ModelAdmin):
    __tablename__ = "usagi_save_roles"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    saving_roles = Column(Boolean)


class UsagiMemberRoles(Base, ModelAdmin):
    __tablename__ = "usagi_member_roles"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    roles = Column(Text)


class UsagiAutoRoles(Base, ModelAdmin):
    __tablename__ = "usagi_auto_roles"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    message_id = Column(Text, unique=True)
    name = Column(Text)


class UsagiAutoRolesData(Base, ModelAdmin):
    __tablename__ = "usagi_auto_roles_data"
    id = Column(Integer, primary_key=True)
    message_id = Column(Text, ForeignKey('usagi_auto_roles.message_id'))
    role_id = Column(BigInteger)
    emoji_id = Column(BigInteger)
    description = Column(Text)


class UsagiTimer(Base, ModelAdmin):
    __tablename__ = "usagi_timer"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    date = Column(DateTime)


class UsagiBackup(Base, ModelAdmin):
    __tablename__ = "usagi_backup"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    user_id = Column(BigInteger)
    messages = Column(BigInteger)
    images = Column(BigInteger)
    gifs = Column(BigInteger)
    emojis = Column(BigInteger)
    stickers = Column(BigInteger)
    voice_min = Column(BigInteger)


class UsagiLanguage(Base, ModelAdmin):
    __tablename__ = "usagi_language"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    lang = Column(Text)


class UsagiBirthday(Base, ModelAdmin):
    __tablename__ = "usagi_birthday"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    date = Column(DateTime)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
