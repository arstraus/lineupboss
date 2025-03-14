"""
Shared database utilities for LineupBoss.

This module provides common database connection and session handling
for the application backend.
"""
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.models import Base, Player, Game
from shared.config import config

def create_engine_from_url(database_url=None):
    """Create SQLAlchemy engine from database URL."""
    if not database_url:
        database_url = config.get_database_url()
        
    if database_url:
        return create_engine(database_url)
    else:
        print("WARNING: DATABASE_URL not found in environment variables.")
        print("Please set DATABASE_URL in your .env file.")
        print("Using in-memory SQLite database as fallback. Most operations will fail.")
        return create_engine('sqlite:///:memory:')

# Create SQLAlchemy engine
engine = create_engine_from_url()

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in the database
def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(engine)

# Get database session
def get_db_session():
    """Returns a database session.
    
    This function must be used within a try/finally block 
    with session.close() in the finally clause to ensure the session is properly closed.
    
    Example usage:
    
    session = get_db_session()
    try:
        # use session for queries
        result = session.query(Model).all()
        return result
    finally:
        session.close()
        
    Alternatively, use the db_session context manager for automatic cleanup:
    
    with db_session() as session:
        # use session for queries
        result = session.query(Model).all()
        return result
    """
    return SessionLocal()

# Context manager for database sessions
class db_session:
    """Context manager for database sessions.
    
    Automatically handles session creation and cleanup.
    
    Example usage:
    
    with db_session() as session:
        # use session for queries
        result = session.query(Model).all()
        return result
    """
    def __init__(self, commit_on_exit=False):
        """Initialize the context manager.
        
        Args:
            commit_on_exit: Whether to commit changes before exiting
        """
        self.commit_on_exit = commit_on_exit
        
    def __enter__(self):
        """Create and return a new database session."""
        self.session = SessionLocal()
        return self.session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the session.
        
        If an exception occurred, roll back changes.
        Otherwise, commit if commit_on_exit is True.
        """
        if exc_type is not None:
            # An exception occurred, roll back changes
            self.session.rollback()
        elif self.commit_on_exit:
            # No exception and commit_on_exit is True, commit changes
            self.session.commit()
            
        # Always close the session
        self.session.close()

# Helper functions to convert between dataframes and database models
def roster_df_to_db(team_id, roster_df):
    """Convert roster dataframe to Player objects"""
    players = []
    for _, row in roster_df.iterrows():
        player = Player(
            team_id=team_id,
            first_name=row['First Name'],
            last_name=row['Last Name'],
            jersey_number=str(row['Jersey Number'])
        )
        players.append(player)
    return players

def roster_db_to_df(players):
    """Convert Player objects to roster dataframe"""
    data = {
        "First Name": [],
        "Last Name": [],
        "Jersey Number": []
    }
    
    for player in players:
        data["First Name"].append(player.first_name)
        data["Last Name"].append(player.last_name)
        data["Jersey Number"].append(player.jersey_number)
    
    return pd.DataFrame(data)

def schedule_df_to_db(team_id, schedule_df):
    """Convert schedule dataframe to Game objects"""
    games = []
    for _, row in schedule_df.iterrows():
        game = Game(
            team_id=team_id,
            game_number=row['Game #'],
            date=row['Date'] if pd.notna(row['Date']) else None,
            time=row['Time'] if 'Time' in row and pd.notna(row['Time']) else None,
            opponent=row['Opponent'],
            innings=row['Innings']
        )
        games.append(game)
    return games

def schedule_db_to_df(games):
    """Convert Game objects to schedule dataframe"""
    data = {
        "Game #": [],
        "Date": [],
        "Time": [],
        "Opponent": [],
        "Innings": []
    }
    
    for game in games:
        data["Game #"].append(game.game_number)
        data["Date"].append(game.date)
        data["Time"].append(game.time)
        data["Opponent"].append(game.opponent)
        data["Innings"].append(game.innings)
    
    df = pd.DataFrame(data)
    # Ensure Date column is datetime type
    df["Date"] = pd.to_datetime(df["Date"])
    return df