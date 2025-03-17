"""
Shared database utilities for LineupBoss.

This module provides common database connection and session handling
for the application backend.
"""
import logging
import sys
import time
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DisconnectionError

from shared.models import Base, Player, Game
from shared.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('lineupboss.database')

def create_engine_from_url(database_url=None):
    """Create SQLAlchemy engine from database URL."""
    if not database_url:
        database_url = config.get_database_url()
        
    if database_url:
        connect_args = {}
        if database_url.startswith("postgresql"):
            # Use prefer mode to try SSL but fall back to non-SSL if needed
            # Also add retry and connection timeout parameters
            connect_args = {
                "sslmode": "prefer", 
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }
        return create_engine(
            database_url, 
            connect_args=connect_args,
            pool_pre_ping=True,  # Verify connections before using them
            pool_recycle=300,    # Recycle connections after 5 minutes
            pool_timeout=30,     # Wait up to 30 seconds for a connection
            pool_size=10,        # Maximum pool size
            max_overflow=2       # Allow 2 extra connections when pool is full
        )
    else:
        print("WARNING: DATABASE_URL not found in environment variables.")
        print("Please set DATABASE_URL in your .env file.")
        print("Using in-memory SQLite database as fallback. Most operations will fail.")
        return create_engine('sqlite:///:memory:')

# Create a simpler, more stable database engine
try:
    # Create database engine with proper configuration
    engine = create_engine_from_url()
    
    # Verify the connection works
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")
except Exception as e:
    logger.error(f"Fatal database connection error: {str(e)}")
    # Fall back to in-memory SQLite in case of fatal error
    logger.warning("Using in-memory SQLite as fallback. Most operations will fail.")
    engine = create_engine('sqlite:///:memory:')

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(engine)

# Simple and reliable database session function
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

# Simple context manager for database sessions
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
        self.session = None
        
    def __enter__(self):
        """Create and return a new database session."""
        self.session = SessionLocal()
        return self.session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the session.
        
        If an exception occurred, roll back changes.
        Otherwise, commit if commit_on_exit is True.
        """
        if self.session is None:
            return
            
        try:
            if exc_type is not None:
                # An exception occurred, roll back changes
                self.session.rollback()
            elif self.commit_on_exit:
                # No exception and commit_on_exit is True, commit changes
                self.session.commit()
        finally:
            # Always close the session
            self.session.close()

# Model serialization functions
def serialize_player(player):
    """Serialize a Player object to a dictionary"""
    return {
        "id": player.id,
        "team_id": player.team_id,
        "first_name": player.first_name,
        "last_name": player.last_name,
        "jersey_number": player.jersey_number
    }

def serialize_game(game):
    """Serialize a Game object to a dictionary"""
    return {
        "id": game.id,
        "team_id": game.team_id,
        "game_number": game.game_number,
        "date": game.date.isoformat() if game.date else None,
        "time": game.time.isoformat() if game.time else None,
        "opponent": game.opponent,
        "innings": game.innings
    }