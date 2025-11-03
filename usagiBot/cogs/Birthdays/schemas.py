from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    Text,
    BigInteger,
    Column,
    Integer,
    DateTime,
    Boolean
)


class UsagiBirthday(Base, ModelAdmin):
    __tablename__ = "usagi_birthday"
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
    enable = Column(Boolean)