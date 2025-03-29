#!/usr/bin/env python3
"""
Script to fix game dates in the Neon database.
"""
import os
import sys
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta

# Database connection
DB_URL = "postgresql://neondb_owner@ep-round-bonus-a6xbhya3-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require"

# Define models
Base = declarative_base()

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    opponent = Column(String)
    game_date = Column(DateTime)
    location = Column(String)
    
    def __repr__(self):
        return f"<Game(id={self.id}, team={self.team_id}, opponent='{self.opponent}', date={self.game_date})>"

class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    league = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    games = relationship("Game", backref="team")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', league='{self.league}')>"

def connect_to_db():
    """Connect to the database."""
    password = os.environ.get("DB_PASSWORD")
    if not password:
        password = input("Enter the database password: ")
    
    connection_string = DB_URL.replace("neondb_owner", f"neondb_owner:{password}")
    
    try:
        engine = create_engine(connection_string)
        Session = sessionmaker(bind=engine)
        session = Session()
        return session
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def check_games(session, team_id):
    """Check games for the specified team."""
    games = session.query(Game).filter_by(team_id=team_id).all()
    print(f"Found {len(games)} games for team {team_id}")
    
    for i, game in enumerate(games):
        date_str = game.game_date.strftime("%Y-%m-%d") if game.game_date else "None"
        print(f"Game {game.id}: {game.opponent}, Date: {date_str}")
    
    # Check how many games have dates
    games_with_dates = [g for g in games if g.game_date is not None]
    print(f"\nGames with dates: {len(games_with_dates)} out of {len(games)}")
    
    return games

def fix_game_dates(session, team_id):
    """Add missing dates to games."""
    games = session.query(Game).filter_by(team_id=team_id).all()
    
    # Base date - start from a month ago
    base_date = datetime.now() - timedelta(days=30)
    
    updated_count = 0
    for i, game in enumerate(games):
        if game.game_date is None:
            # Assign a date starting from base_date, spread 3 days apart
            game_date = base_date + timedelta(days=i*3)
            game.game_date = game_date
            print(f"Updated Game {game.id}: {game.opponent} with date {game_date.strftime('%Y-%m-%d')}")
            updated_count += 1
    
    if updated_count > 0:
        confirm = input(f"\nReady to update {updated_count} games. Confirm? (y/n): ")
        if confirm.lower() == 'y':
            session.commit()
            print(f"Updated {updated_count} games with dates")
        else:
            print("Update cancelled")
    else:
        print("No games need updating")
    
    return updated_count

if __name__ == "__main__":
    team_id = 2  # Default team ID
    
    # Check for team ID override
    if len(sys.argv) > 2:
        try:
            team_id = int(sys.argv[2])
        except ValueError:
            print(f"Invalid team ID: {sys.argv[2]}")
            sys.exit(1)
    
    # Connect to the database
    session = connect_to_db()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            check_games(session, team_id)
        elif sys.argv[1] == "fix":
            fix_game_dates(session, team_id)
            check_games(session, team_id)  # Verify changes
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python fix_game_dates.py [check|fix] [team_id]")
    else:
        print("Checking games...")
        check_games(session, team_id)
        print("\nTo fix missing dates, run: python fix_game_dates.py fix [team_id]")