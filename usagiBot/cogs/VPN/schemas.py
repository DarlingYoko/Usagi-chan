from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    Text,
    BigInteger,
    Column,
    Integer,
    Boolean,
    DateTime
)


class UsagiVpnUsers(Base, ModelAdmin):
    __tablename__ = "usagi_vpn_users"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    uid = Column(Text)
    sub_name = Column(Text)
    expiration_date = Column(DateTime)
    active = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    notify_enabled = Column(Boolean)
    notified = Column(Boolean)

class UsagiVpnHistoryLogs(Base, ModelAdmin):
    __tablename__ = "usagi_vpn_history_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    uid = Column(Text)
    action = Column(Text)
    months = Column(BigInteger)
    previous_exp_date = Column(DateTime)
    new_expiry = Column(DateTime)
    admin_discord = Column(BigInteger)
    timestamp = Column(DateTime)

class UsagiVpnRenewalRequests(Base, ModelAdmin):
    __tablename__ = "usagi_vpn_renewal_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    sub_name = Column(Text)
    uid = Column(Text)
    months = Column(BigInteger)
    new_expiry = Column(BigInteger)
    previous_exp_date = Column(DateTime)
    created_at = Column(DateTime)
    active = Column(Boolean)
    status = Column(Text)


