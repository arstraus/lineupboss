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

# Enhanced context manager for database sessions
class db_session:
    """Context manager for database sessions.
    
    Automatically handles session creation, cleanup, and error handling.
    
    This enhanced version provides:
    1. Automatic session creation and cleanup
    2. Automatic rollback on exceptions
    3. Optional commit on successful exit
    4. Error logging and handling
    5. Transaction isolation level control
    
    Example usage:
    
    with db_session(commit=True) as session:
        # use session for queries
        result = session.query(Model).all()
        # No need to manually commit - it happens automatically on exit
        return result
        
    # For read-only operations:
    with db_session(read_only=True) as session:
        result = session.query(Model).all()
        return result
    """
    def __init__(self, commit=False, read_only=False, log_errors=True):
        """Initialize the context manager.
        
        Args:
            commit: Whether to commit changes before exiting if no exceptions occurred
            read_only: Set session to read-only mode (prevents accidental writes)
            log_errors: Whether to log database errors automatically
        """
        self.commit_on_exit = commit
        self.read_only = read_only
        self.log_errors = log_errors
        self.session = None
        
    def __enter__(self):
        """Create and return a new database session."""
        self.session = SessionLocal()
        
        # For read-only operations, set isolation level to ensure no write locks
        if self.read_only:
            # Execute raw SQL to set transaction as read-only
            # Using text() to properly wrap the SQL statement
            self.session.execute(
                text("SET TRANSACTION READ ONLY")
            )
        
        return self.session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the session with improved error handling.
        
        If an exception occurred:
          - Roll back changes
          - Log the error if log_errors is True
        Otherwise:
          - Commit if commit_on_exit is True
        Finally:
          - Always close the session
        """
        if self.session is None:
            return
            
        try:
            if exc_type is not None:
                # An exception occurred, roll back changes
                self.session.rollback()
                
                # Log the error if requested
                if self.log_errors:
                    import logging
                    logger = logging.getLogger('lineupboss.database')
                    logger.error(f"Database error: {exc_type.__name__}: {str(exc_val)}")
                    
                    # For serious database errors, log more details
                    if hasattr(exc_val, 'orig') and exc_val.orig is not None:
                        logger.error(f"Original database error: {str(exc_val.orig)}")
                        
            elif self.commit_on_exit and not self.read_only:
                # No exception and commit_on_exit is True (and not read-only), commit changes
                self.session.commit()
        finally:
            # Always close the session
            self.session.close()
            
# Alias for backward compatibility
# 'commit_on_exit' parameter is maintained for compatibility
def db_session_legacy(commit_on_exit=False):
    """Legacy db_session function for backward compatibility."""
    return db_session(commit=commit_on_exit)

# Database operation utilities for standardized access patterns
def db_get_or_404(session, model, object_id, error_message=None):
    """Get an object by ID or return a 404 error.
    
    This utility simplifies the common pattern of getting an object by ID
    and returning a 404 error if it doesn't exist.
    
    Args:
        session: SQLAlchemy session
        model: SQLAlchemy model class
        object_id: ID of the object to get
        error_message: Optional custom error message (defaults to "{model.__name__} not found")
        
    Returns:
        The requested object
        
    Raises:
        HTTPException with 404 status if the object doesn't exist
    """
    from flask import abort
    
    obj = session.query(model).filter(model.id == object_id).first()
    if obj is None:
        if error_message is None:
            error_message = f"{model.__name__} not found"
        abort(404, description=error_message)
    return obj

def db_run_transaction(func, *args, log_errors=True, **kwargs):
    """Run a function within a database transaction.
    
    This utility provides a clean way to run operations within a transaction
    with proper error handling and automatic commit/rollback.
    
    Args:
        func: Function to run within the transaction
        *args: Arguments to pass to the function
        log_errors: Whether to log database errors
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function
        
    Example:
        def update_user(session, user_id, new_name):
            user = session.query(User).filter(User.id == user_id).first()
            user.name = new_name
            return user
            
        updated_user = db_run_transaction(update_user, user_id=123, new_name="New Name")
    """
    with db_session(commit=True, log_errors=log_errors) as session:
        return func(session, *args, **kwargs)

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

# Database error handling utilities
def db_error_response(error, default_message="A database error occurred"):
    """Create a standard error response for database errors.
    
    Args:
        error: The exception that was raised
        default_message: Default message to use if no more specific message is available
        
    Returns:
        A tuple (response_dict, status_code) ready to return from an API endpoint
    """
    from flask import jsonify
    import logging
    
    logger = logging.getLogger('lineupboss.database')
    
    # Log the error
    logger.error(f"Database error: {str(error)}")
    
    # Get a more specific error message if available
    if hasattr(error, 'orig') and error.orig is not None:
        logger.error(f"Original database error: {str(error.orig)}")
        
        # Check for specific error types
        if hasattr(error.orig, 'pgcode'):
            pgcode = error.orig.pgcode
            
            # Foreign key violation
            if pgcode == '23503':
                return jsonify({"error": "This operation would violate database constraints"}), 400
                
            # Unique violation (e.g., duplicate key)
            if pgcode == '23505':
                return jsonify({"error": "A record with this information already exists"}), 400
                
    # Default error response
    return jsonify({"error": default_message}), 500