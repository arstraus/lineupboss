"""
System API endpoints for LineupBoss.

This module provides system-wide API endpoints and utilities.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from shared.database import db_session, db_error_response
from shared.models import User

system = Blueprint('system', __name__)

@system.route('/', methods=['GET'])
def hello():
    """Root endpoint for the API."""
    return jsonify({'message': 'Welcome to Lineup API'})

@system.route('/test-jwt', methods=['GET'])
@jwt_required()
def test_jwt():
    """Test JWT validation."""
    current_user_id = get_jwt_identity()
    auth_header = request.headers.get('Authorization', 'None')
    print(f"Authorization header: {auth_header}")
    print(f"Current user ID from JWT: {current_user_id}")
    return jsonify({
        'message': 'JWT is valid', 
        'user_id': current_user_id
    })

@system.route('/test-db', methods=['GET'])
def test_db():
    """Test database connection."""
    try:
        with db_session(read_only=True) as session:
            user_count = session.query(User).count()
            return jsonify({
                'message': 'Database connection successful', 
                'user_count': user_count
            })
    except Exception as e:
        return db_error_response(e, "Database connection failed")

@system.route('/health', methods=['GET'])
def health_check():
    """System health check endpoint."""
    try:
        # First check database
        db_status = "healthy"
        db_message = "Database is connected"
        
        try:
            with db_session(read_only=True) as session:
                # Just run a simple query to verify database connection
                session.execute("SELECT 1").scalar()
        except Exception as e:
            db_status = "unhealthy"
            db_message = f"Database error: {str(e)}"
        
        # Add other health checks as needed (cache, external services, etc.)
        
        status_code = 200 if db_status == "healthy" else 503
        
        return jsonify({
            'status': db_status,
            'timestamp': request.date,
            'components': {
                'database': {
                    'status': db_status,
                    'message': db_message
                }
                # Add other components here
            }
        }), status_code
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Health check error: {str(e)}"
        }), 500