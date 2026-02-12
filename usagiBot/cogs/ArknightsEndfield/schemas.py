from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    Text,
    BigInteger,
    Column,
    Integer,
    Boolean,
)


class UsagiGryphline(Base, ModelAdmin):
    __tablename__ = "usagi_gryphline"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    uid = Column(BigInteger)
    token = Column(Text)
    endfield_sanity_sub = Column(Boolean)
    endfield_sanity_sub_notified = Column(Boolean)
    endfield_daily_sub = Column(Boolean)

class UsagiEndfieldProfile(Base, ModelAdmin):
    __tablename__ = "usagi_endfield_profile"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    background_url = Column(Text)
    accent_color = Column(Text)
    theme = Column(Text)
