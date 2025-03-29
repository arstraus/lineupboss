"""
Production analytics blueprint connecting endpoints to the AnalyticsService.

This module implements the analytics endpoints using the real AnalyticsService
to provide actual analytics data.
"""
from flask import Blueprint, jsonify, g, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.analytics_service import AnalyticsService
from database import db_session
from models.models import User
from utils import standardize_error_response

# Create a production blueprint
analytics_production_bp = Blueprint('analytics_production', __name__)

# Helper function to check if user has access to analytics
def check_analytics_access(team_id):
    """
    Check if the user has access to analytics features.
    
    Args:
        team_id: Team ID to check access for
        
    Returns:
        tuple: (has_access, response_or_None)
    """
    user_id = get_jwt_identity()
    
    # Check if user has the advanced analytics feature
    with db_session(read_only=True) as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False, standardize_error_response(
                'User not found',
                404
            )
        
        # Skip feature check for admins
        if user.role == 'admin':
            return True, None
        
        # Simple check for non-Pro users
        if user.subscription_tier not in ['pro', 'team']:
            return False, standardize_error_response(
                'Subscription required',
                403,
                {
                    'message': 'Advanced analytics requires a Pro subscription',
                    'current_tier': user.subscription_tier,
                    'required_feature': 'advanced_analytics',
                    'upgrade_url': '/account/billing'
                }
            )
    
    return True, None

@analytics_production_bp.route('/status', methods=['GET'])
def analytics_status():
    """Simple endpoint to verify the analytics module is loaded."""
    return jsonify({"status": "ok", "module": "analytics"})

@analytics_production_bp.route('/test', methods=['GET'])
def analytics_test():
    """Test endpoint for analytics."""
    return jsonify({"message": "Analytics test endpoint is working"})

@analytics_production_bp.route('/teams/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team_analytics_restful(team_id):
    """
    Get team analytics endpoint using RESTful pattern.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with team analytics
    """
    # Check feature access
    has_access, error_response = check_analytics_access(team_id)
    if not has_access:
        return error_response
    
    try:
        analytics = AnalyticsService.get_team_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return standardize_error_response("Failed to get team analytics", 500, str(e))

@analytics_production_bp.route('/teams/<int:team_id>/analytics', methods=['GET'])
@jwt_required()
def get_team_analytics(team_id):
    """
    Legacy team analytics endpoint.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with team analytics
    """
    return get_team_analytics_restful(team_id)

@analytics_production_bp.route('/teams/<int:team_id>/players/batting', methods=['GET'])
@jwt_required()
def get_player_batting_analytics_restful(team_id):
    """
    Get player batting analytics endpoint using RESTful pattern.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with player batting analytics
    """
    # Check feature access
    has_access, error_response = check_analytics_access(team_id)
    if not has_access:
        return error_response
    
    try:
        analytics = AnalyticsService.get_player_batting_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return standardize_error_response("Failed to get player batting analytics", 500, str(e))

@analytics_production_bp.route('/teams/<int:team_id>/batting-analytics', methods=['GET'])
@jwt_required()
def get_player_batting_analytics(team_id):
    """
    Legacy player batting analytics endpoint.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with player batting analytics
    """
    return get_player_batting_analytics_restful(team_id)

@analytics_production_bp.route('/teams/<int:team_id>/players/fielding', methods=['GET'])
@jwt_required()
def get_player_fielding_analytics_restful(team_id):
    """
    Get player fielding analytics endpoint using RESTful pattern.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with player fielding analytics
    """
    # Check feature access
    has_access, error_response = check_analytics_access(team_id)
    if not has_access:
        return error_response
    
    try:
        analytics = AnalyticsService.get_player_fielding_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return standardize_error_response("Failed to get player fielding analytics", 500, str(e))

@analytics_production_bp.route('/teams/<int:team_id>/fielding-analytics', methods=['GET'])
@jwt_required()
def get_player_fielding_analytics(team_id):
    """
    Legacy player fielding analytics endpoint.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with player fielding analytics
    """
    return get_player_fielding_analytics_restful(team_id)

@analytics_production_bp.route('/teams/<int:team_id>/debug', methods=['GET'])
@jwt_required()
def debug_analytics_data(team_id):
    """
    Debug endpoint for analytics data.
    
    This endpoint provides detailed information about the data available for analytics,
    helping diagnose issues with analytics data generation.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with detailed diagnostic data
    """
    # Check feature access
    has_access, error_response = check_analytics_access(team_id)
    if not has_access:
        return error_response
    
    try:
        # Use the regular session (not read_only) to avoid parameter errors
        with db_session() as session:
            # Simple check if team exists
            from models.models import Team
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                return jsonify({'status': 'error', 'message': 'Team not found'}), 404
            
            # Return simplified debug info
            return jsonify({
                'status': 'success',
                'team_id': team_id,
                'user_id': get_jwt_identity(),
                'analytics_service_available': hasattr(AnalyticsService, 'get_team_analytics'),
                'subscription_check_active': True,
                'timestamp': request.environ.get('REQUEST_TIME', 0)
            })
    except Exception as e:
        return standardize_error_response("Failed to get debug data", 500, str(e))