from usagiBot.db.base import Base
from usagiBot.db.models import ModelAdmin
from sqlalchemy import (
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
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    points = Column(BigInteger)
    count_of_games = Column(BigInteger)