from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    guesses = relationship("Guess", back_populates="user")

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    room_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    status = Column(String, default="in_progress")
    tries = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    rounds = relationship("Round", back_populates="game")

class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    result = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    game = relationship("Game", back_populates="rounds")
    guesses = relationship("Guess", back_populates="round")

class Guess(Base):
    __tablename__ = "guesses"
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    word = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    round = relationship("Round", back_populates="guesses")
    user = relationship("User", back_populates="guesses")
