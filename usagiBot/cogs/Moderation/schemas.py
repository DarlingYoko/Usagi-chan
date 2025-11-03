from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    Text,
    BigInteger,
    Column,
    Integer,
    Boolean,
)


class UsagiCogs(Base, ModelAdmin):
    __tablename__ = "usagi_cogs"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    module_name = Column(Text)
    access = Column(Boolean)


class UsagiModerRoles(Base, ModelAdmin):
    __tablename__ = "usagi_moder_roles"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    moder_role_id = Column(BigInteger)