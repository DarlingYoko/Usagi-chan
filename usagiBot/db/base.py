from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from usagiBot.env import (
    DATABASE_NAME,
    DATABASE_USER,
    DATABASE_PASS,
    DATABASE_HOST,
    DATABASE_PORT,
)

DATABASE_URL = f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASS}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=2,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_use_lifo=True,
)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
