"""
Authentication middleware for LineupBoss API.

This module provides authentication-related middleware components
to centralize authentication logic across the application.
"""

from functools import wraps
from flask import g, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from shared.database import db_session
from backend.utils import standardize_error_response

class AuthMiddleware:
    """Authentication middleware for applying auth checks to routes."""

    @staticmethod
    def authenticate(f):
        """
        Middleware to verify JWT token and set user_id in Flask g object.
        
        This is a simpler version of jwt_required() that also sets g.user_id for convenience.
        
        Returns:
            Function that verifies JWT and calls the original function
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Verify JWT token
                verify_jwt_in_request()
                
                # Get user ID from token
                user_id = get_jwt_identity()
                
                # Convert to int if it's a string
                try:
                    if isinstance(user_id, str):
                        user_id = int(user_id)
                except ValueError:
                    return standardize_error_response('Invalid user ID format', 400)
                
                # Store user_id in g for use in the route function
                g.user_id = user_id
                
                # Call the original function
                return f(*args, **kwargs)
            except Exception as e:
                print(f"Authentication error: {str(e)}")
                return standardize_error_response('Authentication required', 401, str(e))
        
        return decorated_function
    
    @staticmethod
    def admin_required(f):
        """
        Middleware to verify the user has admin role.
        
        This middleware verifies the JWT token, extracts the user from the database,
        and checks if they have the admin role.
        
        Returns:
            Function that checks admin role and calls the original function
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # First verify JWT is present and valid
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                # Convert user_id to int if it's a string
                try:
                    if isinstance(user_id, str):
                        user_id = int(user_id)
                except ValueError:
                    return standardize_error_response('Invalid user ID format', 400)
                
                # Get user from database
                with db_session(read_only=True) as session:
                    # Avoid circular imports
                    from services.auth_service import AuthService
                    
                    user = AuthService.get_user_by_id(session, user_id)
                    
                    if not user:
                        return standardize_error_response('User not found', 404)
                    
                    if user.role != 'admin':
                        return standardize_error_response(
                            'Admin access required', 
                            403,
                            {'required_role': 'admin', 'current_role': user.role}
                        )
                    
                    # Store user and user_id in Flask's g object for convenience
                    g.user_id = user_id
                    g.user = user
                    
                    # Call the original function
                    return f(*args, **kwargs)
            except Exception as e:
                print(f"Admin authentication error: {str(e)}")
                return standardize_error_response('Authentication required', 401, str(e))
        
        return decorated_function
    
    @staticmethod
    def get_auth_header():
        """
        Get the Authorization header from various sources.
        
        Tries multiple sources for the auth token in this order:
        1. Standard Authorization header
        2. Custom X-Authorization header
        3. JWT cookie
        4. token URL parameter
        
        Returns:
            Full authorization header string if found, None otherwise
        """
        # Try standard Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            return auth_header
        
        # Try custom X-Authorization header
        x_auth = request.headers.get('X-Authorization')
        if x_auth:
            return x_auth
        
        # Try cookie
        jwt_cookie = request.cookies.get('jwt')
        if jwt_cookie:
            return f"Bearer {jwt_cookie}"
        
        # Try URL parameter
        token_param = request.args.get('token')
        if token_param:
            return f"Bearer {token_param}"
        
        return None
    
    @staticmethod
    def validate_user_owns_resource(resource_type, resource_id, user_id):
        """
        Validate that a user owns a resource.
        
        Args:
            resource_type: Type of resource (e.g., 'team', 'game', 'player')
            resource_id: ID of the resource
            user_id: ID of the user to check
            
        Returns:
            (resource, None) if user owns the resource,
            (None, error_response) if user doesn't own the resource
        """
        with db_session(read_only=True) as session:
            # Use the appropriate service based on resource type
            if resource_type == 'team':
                from services.team_service import TeamService
                resource = TeamService.get_team(session, resource_id, user_id)
            elif resource_type == 'game':
                from services.game_service import GameService
                resource = GameService.get_game(session, resource_id, user_id)
            elif resource_type == 'player':
                from services.player_service import PlayerService
                resource = PlayerService.get_player(session, resource_id, user_id)
            else:
                return None, standardize_error_response(
                    f'Invalid resource type: {resource_type}',
                    400
                )
            
            if not resource:
                return None, standardize_error_response(
                    f'{resource_type.capitalize()} not found or unauthorized',
                    404
                )
            
            return resource, None