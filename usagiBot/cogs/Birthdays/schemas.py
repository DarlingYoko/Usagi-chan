from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    Index,
    Text,
    BigInteger,
    Column,
    Integer,
    DateTime,
    Boolean
)


class UsagiBirthday(Base, ModelAdmin):
    __tablename__ = "usagi_birthday"
    __table_args__ = (
        Index("ix_usagi_birthday_guild_user", "guild_id", "user_id"),
    )
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    date = Column(DateTime)
    name = Column(Text)


class UsagiBirthdayTimer(Base, ModelAdmin):
    __tablename__ = "usagi_birthday_timer"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    enable = Column(Boolean, nullable=False, default=False, server_default="false")