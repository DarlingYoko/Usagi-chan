from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
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
    ltoken_v2 = Column(Text)
    cookie_token_v2 = Column(Text)
    genshin_resin_sub = Column(Boolean)
    genshin_resin_sub_notified = Column(Boolean)
    genshin_daily_sub = Column(Boolean)
    daily_notify_sub = Column(Boolean)
    starrail_daily_sub = Column(Boolean)
    starrail_resin_sub = Column(Boolean)
    starrail_resin_sub_notified = Column(Boolean)
    zzz_daily_sub = Column(Boolean)
    zzz_resin_sub = Column(Boolean)
    zzz_resin_sub_notified = Column(Boolean)