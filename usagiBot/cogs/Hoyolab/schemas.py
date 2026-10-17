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


class UsagiHoyolab(Base, ModelAdmin):
    __tablename__ = "usagi_hoyolab"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    ltuid_v2 = Column(Text)
    ltmid_v2 = Column(Text)
    account_id_v2 = Column(Text)
    ltoken_v2 = Column(EncryptedText)
    cookie_token_v2 = Column(EncryptedText)
    genshin_resin_sub = Column(Boolean, nullable=False, default=False, server_default="false")
    genshin_resin_sub_notified = Column(Boolean, nullable=False, default=False, server_default="false")
    genshin_daily_sub = Column(Boolean, nullable=False, default=False, server_default="false")
    daily_notify_sub = Column(Boolean, nullable=False, default=False, server_default="false")
    starrail_daily_sub = Column(Boolean, nullable=False, default=False, server_default="false")
    starrail_resin_sub = Column(Boolean, nullable=False, default=False, server_default="false")
    starrail_resin_sub_notified = Column(Boolean, nullable=False, default=False, server_default="false")
    zzz_daily_sub = Column(Boolean, nullable=False, default=False, server_default="false")
    zzz_resin_sub = Column(Boolean, nullable=False, default=False, server_default="false")
    zzz_resin_sub_notified = Column(Boolean, nullable=False, default=False, server_default="false")