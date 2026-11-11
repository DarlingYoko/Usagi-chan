from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
    Index,
    Text,
    BigInteger,
    Column,
    Integer,
)


class UsagiWordleGames(Base, ModelAdmin):
    __tablename__ = "usagi_wordle_games"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    word = Column(Text)
    owner_id = Column(BigInteger)
    thread_id = Column(BigInteger)


class UsagiWordleResults(Base, ModelAdmin):
    __tablename__ = "usagi_wordle_results"
    __table_args__ = (
        Index("ix_usagi_wordle_results_guild_user", "guild_id", "user_id"),
    )
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    points = Column(BigInteger, nullable=False, default=0, server_default="0")
    count_of_games = Column(BigInteger, nullable=False, default=0, server_default="0")


# Serves ModelAdmin.get_top (WHERE guild_id = ? ORDER BY points DESC LIMIT n)
# without a sort; declared outside the class because it needs .desc().
Index(
    "ix_usagi_wordle_results_guild_points",
    UsagiWordleResults.guild_id,
    UsagiWordleResults.points.desc(),
)