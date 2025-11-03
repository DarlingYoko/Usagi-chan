from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
)


class UsagiUnicRoles(Base, ModelAdmin):
    __tablename__ = "usagi_unic_roles"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    role_id = Column(BigInteger)