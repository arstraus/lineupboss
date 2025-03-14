
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

# For backward compatibility
def get_db():
    """
    Returns a database session.
    This function must be used within a try/finally block 
    with db.close() in the finally clause to ensure the session is properly closed.
    
    Example usage:
    
    db = get_db()
    try:
        # use db for queries
        result = db.query(Model).all()
        return result
    finally:
        db.close()
        
    Alternatively, use the db_session context manager for automatic cleanup:
    
    with db_session() as session:
        # use session for queries
        result = session.query(Model).all()
        return result
    """
    return get_db_session()
