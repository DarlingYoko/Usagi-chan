from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from usagiBot.db.types import EncryptedText
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
    token = Column(EncryptedText)
    endfield_sanity_sub = Column(Boolean, nullable=False, default=False, server_default="false")
    endfield_sanity_sub_notified = Column(Boolean, nullable=False, default=False, server_default="false")
    endfield_daily_sub = Column(Boolean, nullable=False, default=False, server_default="false")

class UsagiEndfieldProfile(Base, ModelAdmin):
    __tablename__ = "usagi_endfield_profile"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    background_url = Column(Text)
    accent_color = Column(Text)
    theme = Column(Text)
