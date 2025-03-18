
"""
Database utilities for LineupBoss backend.

This file re-exports the shared database utilities to maintain compatibility with existing imports.
"""
from shared.database import get_db_session, db_session
from shared.models import Base

# Create all tables
def init_db():
    """Create all database tables."""
    from shared.database import engine
    Base.metadata.create_all(bind=engine)

# For backward compatibility - DEPRECATED
def get_db():
    """
    DEPRECATED: Use db_session context manager instead.
    
    Returns a database session.
    This function must be used within a try/finally block 
    with db.close() in the finally clause to ensure the session is properly closed.
    
    Example usage (DEPRECATED):
    
    db = get_db()
    try:
        # use db for queries
        result = db.query(Model).all()
        return result
    finally:
        db.close()
        
    RECOMMENDED USAGE - Use the db_session context manager for automatic cleanup:
    
    with db_session(read_only=True) as session:  # For read operations
        # use session for queries
        result = session.query(Model).all()
        return result
        
    with db_session(commit=True) as session:  # For write operations
        # use session for modifications
        entity = session.query(Model).get(id)
        entity.attribute = new_value
        # No need to commit - handled automatically
        return entity
    """
    import warnings
    warnings.warn(
        "get_db() is deprecated. Use db_session context manager instead for better error handling and automatic cleanup.",
        DeprecationWarning, 
        stacklevel=2
    )
    return get_db_session()
