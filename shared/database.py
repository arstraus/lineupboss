"""
Shared database utilities for LineupBoss.

This module provides common database connection and session handling
for the application backend.
"""
import logging
import sys
import time
from sqlalchemy import create_engine, event
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

# Define engine retry mechanism
def get_engine_with_retry(max_retries=3, retry_interval=2):
    """
    Create database engine with retry logic
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Seconds to wait between retries
        
    Returns:
        SQLAlchemy engine
    """
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            engine = create_engine_from_url()
            
            # Test the connection
            connection = engine.connect()
            connection.close()
            
            logger.info("Database connection established successfully")
            
            # Set up event listeners for connection pool events
            @event.listens_for(engine, "connect")
            def connect(dbapi_connection, connection_record):
                logger.info("New database connection established")
            
            @event.listens_for(engine, "checkout")
            def checkout(dbapi_connection, connection_record, connection_proxy):
                logger.debug("Database connection checked out from pool")
            
            @event.listens_for(engine, "checkin")
            def checkin(dbapi_connection, connection_record):
                logger.debug("Database connection returned to pool")
                
            @event.listens_for(engine, "engine_connect")
            def ping_connection(connection, branch):
                if branch:
                    # Don't test connections for each "sub-connection" of a connection branch
                    return

                # Test the connection using a small query
                try:
                    connection.scalar("""SELECT 1""")
                except Exception as e:
                    logger.error(f"Connection test failed: {str(e)}")
                    # Reconnect on invalid connections
                    connection.invalidate()
                    raise
            
            return engine
            
        except (OperationalError, DisconnectionError) as e:
            retry_count += 1
            last_error = e
            logger.warning(f"Database connection failed (attempt {retry_count}/{max_retries}): {str(e)}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            
    # If we get here, all retries failed
    logger.error(f"Failed to connect to database after {max_retries} attempts: {str(last_error)}")
    raise last_error

# Create SQLAlchemy engine with retry mechanism
try:
    engine = get_engine_with_retry()
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

# Get database session with retry mechanism for transient errors
def get_db_session(max_retries=3, retry_interval=2):
    """Returns a database session with retry logic for transient errors.
    
    This function must be used within a try/finally block 
    with session.close() in the finally clause to ensure the session is properly closed.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Seconds to wait between retries
    
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
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            # Create a new session
            session = SessionLocal()
            
            # Test the connection with a simple query
            session.execute("SELECT 1")
            
            return session
            
        except (OperationalError, DisconnectionError) as e:
            # These are potentially transient errors
            if hasattr(session, 'close'):
                try:
                    session.close()
                except:
                    pass
                    
            retry_count += 1
            last_error = e
            logger.warning(f"Database session error (attempt {retry_count}/{max_retries}): {str(e)}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
    
    # If we get here, all retries failed
    logger.error(f"Failed to create database session after {max_retries} attempts: {str(last_error)}")
    raise last_error

# Context manager for database sessions with retry logic
class db_session:
    """Context manager for database sessions.
    
    Automatically handles session creation, cleanup, and retries for transient errors.
    
    Example usage:
    
    with db_session() as session:
        # use session for queries
        result = session.query(Model).all()
        return result
    """
    def __init__(self, commit_on_exit=False, max_retries=3, retry_interval=2):
        """Initialize the context manager.
        
        Args:
            commit_on_exit: Whether to commit changes before exiting
            max_retries: Maximum number of connection attempts
            retry_interval: Seconds to wait between retries
        """
        self.commit_on_exit = commit_on_exit
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.session = None
        
    def __enter__(self):
        """Create and return a new database session with retry logic."""
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                # Create a new session
                self.session = SessionLocal()
                
                # Test the connection with a simple query
                self.session.execute("SELECT 1")
                
                return self.session
                
            except (OperationalError, DisconnectionError) as e:
                # These are potentially transient errors
                if self.session is not None:
                    try:
                        self.session.close()
                    except:
                        pass
                        
                retry_count += 1
                last_error = e
                logger.warning(f"Database session error (attempt {retry_count}/{self.max_retries}): {str(e)}")
                
                if retry_count < self.max_retries:
                    logger.info(f"Retrying in {self.retry_interval} seconds...")
                    time.sleep(self.retry_interval)
        
        # If we get here, all retries failed
        logger.error(f"Failed to create database session after {self.max_retries} attempts: {str(last_error)}")
        raise last_error
        
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
                try:
                    self.session.rollback()
                except Exception as e:
                    logger.warning(f"Error during session rollback: {str(e)}")
            elif self.commit_on_exit:
                # No exception and commit_on_exit is True, commit changes
                try:
                    self.session.commit()
                except Exception as e:
                    logger.error(f"Error during session commit: {str(e)}")
                    # Try to rollback if commit fails
                    try:
                        self.session.rollback()
                    except:
                        pass
                    # Re-raise the original exception
                    raise
        finally:
            # Always try to close the session
            try:
                self.session.close()
            except Exception as e:
                logger.warning(f"Error during session close: {str(e)}")
                
            # Set session to None to avoid double-closing
            self.session = None

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