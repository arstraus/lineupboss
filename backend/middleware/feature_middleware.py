"""
Feature gating middleware for LineupBoss API.

This module provides feature gating middleware components
to centralize feature access logic across the application.
"""

from functools import wraps
from flask import g, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from shared.database import db_session
from backend.utils import standardize_error_response

class FeatureMiddleware:
    """Feature gating middleware for applying feature checks to routes."""
    
    @staticmethod
    def check_feature(feature_name, user=None, user_id=None, session=None):
        """
        Check if a user has access to a feature.
        
        This method checks if a user's subscription tier includes a specific feature.
        Admin users are automatically granted access to all features.
        
        Args:
            feature_name: Name of the feature to check
            user: User object (optional, will be fetched if not provided)
            user_id: User ID (optional, will be used if user not provided)
            session: Database session (optional, will be created if not provided)
            
        Returns:
            (True, None) if user has access to the feature,
            (False, error_response) if user doesn't have access to the feature
        """
        from shared.subscription_tiers import has_feature
        
        # If we don't have a user object, fetch it from the database
        if not user and user_id:
            # Create a session if one wasn't provided
            session_created = False
            if not session:
                session = db_session(read_only=True).__enter__()
                session_created = True
            
            try:
                # Import here to avoid circular imports
                from shared.models import User
                user = session.query(User).filter(User.id == user_id).first()
            finally:
                # Close the session if we created it
                if session_created:
                    session.__exit__(None, None, None)
        
        # If we still don't have a user, return error
        if not user:
            return False, standardize_error_response('User not found', 404)
        
        # Admin users have access to all features
        if user.role == 'admin':
            return True, None
        
        # Check if the user's subscription tier includes the feature
        if not has_feature(user.subscription_tier, feature_name):
            return False, standardize_error_response(
                'Subscription required',
                403,
                {
                    'message': f'This feature requires a higher subscription tier',
                    'current_tier': user.subscription_tier,
                    'required_feature': feature_name,
                    'upgrade_url': '/account/billing'
                }
            )
        
        return True, None
    
    @staticmethod
    def feature_required(feature_name):
        """
        Middleware to restrict routes based on features available in subscription tier.
        
        This middleware verifies the JWT token, extracts the user from the database,
        and checks if they have access to the specified feature.
        
        Args:
            feature_name: Feature name required to access the route
            
        Returns:
            Function that checks feature access and calls the original function
        """
        def decorator(f):
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
                    
                    # Check feature access
                    with db_session(read_only=True) as session:
                        # Import here to avoid circular imports
                        from shared.models import User
                        
                        user = session.query(User).filter(User.id == user_id).first()
                        
                        if not user:
                            return standardize_error_response('User not found', 404)
                        
                        # Store user and user_id in Flask's g object for convenience
                        g.user_id = user_id
                        g.user = user
                        
                        # Check feature access
                        has_access, error_response = FeatureMiddleware.check_feature(
                            feature_name, 
                            user=user
                        )
                        
                        if not has_access:
                            return error_response
                        
                        # Call the original function
                        return f(*args, **kwargs)
                except Exception as e:
                    print(f"Feature check error: {str(e)}")
                    return standardize_error_response('Authentication required', 401, str(e))
            
            return decorated_function
        
        return decorator
    
    @staticmethod
    def check_team_limit(user=None, user_id=None, session=None):
        """
        Check if a user has reached their team limit.
        
        This method checks if a user has reached the maximum number of teams
        allowed by their subscription tier. Admin users have no team limit.
        
        Args:
            user: User object (optional, will be fetched if not provided)
            user_id: User ID (optional, will be used if user not provided)
            session: Database session (optional, will be created if not provided)
            
        Returns:
            (True, None, team_count, team_limit) if user hasn't reached their team limit,
            (False, error_response, team_count, team_limit) if user has reached their team limit
        """
        from shared.subscription_tiers import get_team_limit
        
        # If we don't have a user object, fetch it from the database
        if not user and user_id:
            # Create a session if one wasn't provided
            session_created = False
            if not session:
                session = db_session(read_only=True).__enter__()
                session_created = True
            
            try:
                # Import here to avoid circular imports
                from shared.models import User
                user = session.query(User).filter(User.id == user_id).first()
            finally:
                # Close the session if we created it
                if session_created:
                    session.__exit__(None, None, None)
        
        # If we still don't have a user, return error
        if not user:
            return False, standardize_error_response('User not found', 404), 0, 0
        
        # Admin users have no team limit
        if user.role == 'admin':
            return True, None, 0, float('inf')
        
        # Get the user's team limit based on their subscription tier
        team_limit = get_team_limit(user.subscription_tier)
        
        # Count the number of teams the user has
        # Create a session if one wasn't provided
        session_created = False
        if not session:
            session = db_session(read_only=True).__enter__()
            session_created = True
        
        try:
            # Import here to avoid circular imports
            from shared.models import Team
            team_count = session.query(Team).filter(Team.user_id == user.id).count()
        finally:
            # Close the session if we created it
            if session_created:
                session.__exit__(None, None, None)
        
        # Check if user has reached their team limit
        if team_count >= team_limit:
            return False, standardize_error_response(
                'Team limit reached',
                403,
                {
                    'message': f'You have reached the maximum number of teams ({team_limit}) for your subscription tier.',
                    'current_tier': user.subscription_tier,
                    'team_limit': team_limit,
                    'team_count': team_count,
                    'upgrade_url': '/account/billing'
                }
            ), team_count, team_limit
        
        return True, None, team_count, team_limit