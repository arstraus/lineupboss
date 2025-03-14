"""
Utility functions for the LineupBoss backend.
"""
from functools import wraps
from flask import jsonify
from shared.database import db_session

def with_db_session(f):
    """Decorator to provide a database session to a route handler.
    
    Usage:
    @with_db_session
    def some_route(db=None):
        # Use db session here
        result = db.query(Model).all()
        return jsonify(result)
    
    The decorated function will receive a db session as a keyword argument.
    The session will be automatically closed when the function returns.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        with db_session() as session:
            try:
                # Add session to kwargs
                kwargs['db'] = session
                # Call the original function
                return f(*args, **kwargs)
            except Exception as e:
                session.rollback()
                return jsonify({'error': str(e)}), 500
    return decorated_function