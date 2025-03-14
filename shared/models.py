"""
Shared database models for LineupBoss.

This module contains SQLAlchemy models used by both the Streamlit frontend
and the Flask API backend.
"""
import hashlib
import secrets
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Boolean, Date, Time, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

# Create base class for declarative models
Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    created_at = Column(sa.DateTime, server_default=sa.func.now())
    
    # Relationships
    teams = relationship("Team", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Hash password with salt"""
        self.salt = secrets.token_hex(16)
        self.password_hash = hashlib.sha256((password + self.salt).encode()).hexdigest()
    
    def check_password(self, password):
        """Verify password"""
        return self.password_hash == hashlib.sha256((password + self.salt).encode()).hexdigest()


class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    league = Column(String)
    head_coach = Column(String)
    assistant_coach1 = Column(String)
    assistant_coach2 = Column(String)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="teams")
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")
    games = relationship("Game", back_populates="team", cascade="all, delete-orphan")

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='CASCADE'))
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    jersey_number = Column(String, nullable=False)
    
    # Relationships
    team = relationship("Team", back_populates="players")
    player_availability = relationship("PlayerAvailability", back_populates="player", cascade="all, delete-orphan")
    
    def full_name(self):
        return f"{self.first_name} {self.last_name} (#{self.jersey_number})"

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='CASCADE'))
    game_number = Column(Integer, nullable=False)
    date = Column(Date)
    time = Column(Time)
    opponent = Column(String)
    innings = Column(Integer, default=6)
    
    # Relationships
    team = relationship("Team", back_populates="games")
    batting_order = relationship("BattingOrder", back_populates="game", uselist=False, cascade="all, delete-orphan")
    fielding_rotations = relationship("FieldingRotation", back_populates="game", cascade="all, delete-orphan")
    player_availability = relationship("PlayerAvailability", back_populates="game", cascade="all, delete-orphan")

class BattingOrder(Base):
    __tablename__ = 'batting_orders'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), unique=True)
    order_data = Column(JSONB)  # Store the list of jersey numbers as JSON
    
    # Relationships
    game = relationship("Game", back_populates="batting_order")

class FieldingRotation(Base):
    __tablename__ = 'fielding_rotations'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'))
    inning = Column(Integer, nullable=False)
    positions = Column(JSONB)  # Store the positions dictionary as JSON
    
    # Relationships
    game = relationship("Game", back_populates="fielding_rotations")
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('game_id', 'inning', name='uq_fielding_rotation_game_inning'),
    )

class PlayerAvailability(Base):
    __tablename__ = 'player_availability'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'))
    player_id = Column(Integer, ForeignKey('players.id', ondelete='CASCADE'))
    available = Column(Boolean, default=True)
    can_play_catcher = Column(Boolean, default=False)
    
    # Relationships
    game = relationship("Game", back_populates="player_availability")
    player = relationship("Player", back_populates="player_availability")
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('game_id', 'player_id', name='uq_player_availability_game_player'),
    )