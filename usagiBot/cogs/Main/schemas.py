from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    Text,
    BigInteger,
    Column,
    Integer,
    Boolean,
    ForeignKey,
    DateTime
)


class UsagiConfig(Base, ModelAdmin):
    __tablename__ = "usagi_config"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    command_tag = Column(Text)
    generic_id = Column(BigInteger)

class UsagiSaveRoles(Base, ModelAdmin):
    __tablename__ = "usagi_save_roles"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    saving_roles = Column(Boolean)

class UsagiMemberRoles(Base, ModelAdmin):
    __tablename__ = "usagi_member_roles"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    roles = Column(Text)

class UsagiAutoRolesData(Base, ModelAdmin):
    __tablename__ = "usagi_auto_roles_data"
    id = Column(Integer, primary_key=True)
    message_id = Column(Text, ForeignKey("usagi_auto_roles.message_id"))
    role_id = Column(BigInteger)
    emoji_id = Column(BigInteger)
    description = Column(Text)

class UsagiBackup(Base, ModelAdmin):
    __tablename__ = "usagi_backup"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    user_id = Column(BigInteger)
    messages = Column(BigInteger)
    images = Column(BigInteger)
    gifs = Column(BigInteger)
    emojis = Column(BigInteger)
    stickers = Column(BigInteger)
    voice_min = Column(BigInteger)

class UsagiAutoRoles(Base, ModelAdmin):
    __tablename__ = "usagi_auto_roles"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    message_id = Column(Text, unique=True)
    name = Column(Text)

class UsagiTimer(Base, ModelAdmin):
    __tablename__ = "usagi_timer"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    date = Column(DateTime)

class UsagiLanguage(Base, ModelAdmin):
    __tablename__ = "usagi_language"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    lang = Column(Text)