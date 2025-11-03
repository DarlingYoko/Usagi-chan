from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    Text,
    BigInteger,
    Column,
    Integer,
    DateTime
)


class UsagiTwitchNotify(Base, ModelAdmin):
    __tablename__ = "usagi_twitch_notify"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    twitch_username = Column(Text)
    started_at = Column(DateTime)