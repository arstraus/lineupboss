"""
Utility functions for the LineupBoss backend.
"""
from functools import wraps
from flask import jsonify, g
from shared.database import db_session
from shared.subscription_tiers import has_feature, TIER_FEATURES

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

def subscription_required(tier):
    """Decorator to restrict route access based on subscription tier.
    
    Usage:
    @subscription_required('pro')
    @token_required
    def premium_route():
        # This will only be accessible to users with 'pro' subscription
        
    The decorator assumes token_required has already set g.user_id
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify user_id is in global context
            if not hasattr(g, 'user_id'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in first'
                }), 401
                
            # Check user's subscription tier
            with db_session(read_only=True) as session:
                from shared.models import User
                from shared.subscription_tiers import compare_tiers
                
                user = session.query(User).filter(User.id == g.user_id).first()
                
                if not user:
                    return jsonify({
                        'error': 'User not found',
                        'message': 'Could not verify subscription tier'
                    }), 404
                    
                if user.role == 'admin':
                    # Admins bypass subscription checks
                    return f(*args, **kwargs)
                    
                # Check if user's tier is sufficient using our tier helper
                if not compare_tiers(user.subscription_tier, tier):
                    return jsonify({
                        'error': 'Subscription required',
                        'message': f'This feature requires a {tier} subscription',
                        'current_tier': user.subscription_tier,
                        'required_tier': tier,
                        'upgrade_url': '/account/billing'
                    }), 403
                
                # If we get here, the user has adequate permissions
                return f(*args, **kwargs)
        return decorated_function
    return decorator

def feature_required(feature_name):
    """Decorator to restrict route access based on user's subscription features.
    
    Usage:
    @feature_required('ai_lineup_generation')
    @token_required
    def generate_ai_lineup():
        # This will only be accessible to users with the ai_lineup_generation feature
        
    The decorator assumes token_required has already set g.user_id
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify user_id is in global context
            if not hasattr(g, 'user_id'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in first'
                }), 401
                
            # Check user's subscription tier
            with db_session(read_only=True) as session:
                from shared.models import User
                user = session.query(User).filter(User.id == g.user_id).first()
                
                if not user:
                    return jsonify({
                        'error': 'User not found',
                        'message': 'Could not verify subscription features'
                    }), 404
                    
                if user.role == 'admin':
                    # Admins bypass feature checks
                    return f(*args, **kwargs)
                    
                # Check if user's tier has the required feature
                if not has_feature(user.subscription_tier, feature_name):
                    return jsonify({
                        'error': 'Subscription required',
                        'message': f'This feature requires a Pro subscription',
                        'current_tier': user.subscription_tier,
                        'required_feature': feature_name,
                        'upgrade_url': '/account/billing'
                    }), 403
                
                # If we get here, the user has the required feature
                return f(*args, **kwargs)
        return decorated_function
    return decorator

def team_limit_check(f):
    """Decorator to check if a user has reached their team limit based on subscription tier.
    
    Usage:
    @team_limit_check
    @jwt_required()
    def create_team_route():
        # This will check if user is allowed to create more teams
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user ID directly from JWT instead of relying on g.user_id
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        # Convert to integer if string
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                return jsonify({"error": "Invalid user ID format"}), 400
                
        # Store in g for compatibility with the rest of the function
        from flask import g
        g.user_id = user_id
        
        print(f"Team limit check for user_id: {user_id}")
            
        # Check user's team count against their subscription limit
        with db_session(read_only=True) as session:
            from shared.models import User, Team
            
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"User not found: {user_id}")
                return jsonify({
                    'error': 'User not found'
                }), 404
                
            # Admins bypass team limits
            if user.role == 'admin':
                print(f"Admin user {user_id} bypassing team limit check")
                return f(*args, **kwargs)
                
            # Get the user's team count
            team_count = session.query(Team).filter(Team.user_id == user_id).count()
            
            # Get the user's tier limit from the tier features
            tier = user.subscription_tier
            if tier not in TIER_FEATURES:
                tier = "rookie"  # Default to rookie for unknown tiers
                
            user_limit = TIER_FEATURES[tier].get("max_teams", 2)  # Default to 2 teams
            
            print(f"User {user_id} has {team_count} teams out of {user_limit} allowed for tier {tier}")
            
            # Check if user is at or over their limit
            if team_count >= user_limit and user_limit != float('inf'):
                return jsonify({
                    'error': 'Team limit reached',
                    'message': f'Your {user.subscription_tier} plan allows {user_limit} teams. Upgrade to create more teams.',
                    'current_count': team_count,
                    'limit': user_limit,
                    'upgrade_url': '/account/billing'
                }), 403
                
            # User is within their limits
            return f(*args, **kwargs)
    return decorated_function