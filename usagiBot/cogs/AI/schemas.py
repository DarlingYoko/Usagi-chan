from pgvector.sqlalchemy import Vector

from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    Text,
    BigInteger,
    Column,
    Integer,
    DateTime
)


class UsagiAIFacts(Base, ModelAdmin):
    __tablename__ = "usagi_ai_facts"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    facts = Column(Text)


class UsagiAIPromt(Base, ModelAdmin):
    __tablename__ = "usagi_ai_promt"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    prompt = Column(Text)


class UsagiAIMemory(Base, ModelAdmin):
    __tablename__ = "usagi_ai_memory"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    message = Column(Text)
    thread_id = Column(BigInteger)
    embedding = Column(Vector(1536))


class UsagiAIReminder(Base, ModelAdmin):
    __tablename__ = "usagi_ai_reminder"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    user_id = Column(BigInteger)
    text = Column(Text)
    date = Column(DateTime)