"""
API endpoints for analytics.
"""
from flask import Blueprint, jsonify, request, g
import logging
import traceback
from sqlalchemy import func
from shared.database import db_session
from services.analytics_service import AnalyticsService
from middleware.auth import jwt_required
from shared.models import Team, Game, BattingOrder, FieldingRotation, User
from backend.utils import standardize_error_response
from shared.subscription_tiers import has_feature

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/teams/<int:team_id>/players/batting', methods=['GET'])
@jwt_required
def get_player_batting_analytics(team_id):
    """
    Get batting analytics for all players in a team using RESTful pattern.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with player batting analytics
    """
    # Check feature access inside the function
    user_id = g.user_id
    
    # Check if user has the advanced analytics feature
    with db_session(read_only=True) as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return standardize_error_response(
                'User not found',
                404
            )
        
        # Skip feature check for admins
        if user.role != 'admin':
            if not has_feature(user.subscription_tier, 'advanced_analytics'):
                return standardize_error_response(
                    'Subscription required',
                    403,
                    {
                        'message': 'Advanced analytics requires a Pro subscription',
                        'current_tier': user.subscription_tier,
                        'required_feature': 'advanced_analytics',
                        'upgrade_url': '/account/billing'
                    }
                )
    
    return get_team_batting_analytics(team_id)

@analytics_bp.route('/teams/<int:team_id>/batting-analytics', methods=['GET'])
@jwt_required
def get_team_batting_analytics(team_id):
    """
    Get batting analytics for all players in a team.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with player batting analytics
    """
    user_id = g.user_id
    
    # Check if user has the advanced analytics feature
    with db_session(read_only=True) as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return standardize_error_response(
                'User not found',
                404
            )
        
        # Skip feature check for admins
        if user.role != 'admin':
            if not has_feature(user.subscription_tier, 'advanced_analytics'):
                return standardize_error_response(
                    'Subscription required',
                    403,
                    {
                        'message': 'Advanced analytics requires a Pro subscription',
                        'current_tier': user.subscription_tier,
                        'required_feature': 'advanced_analytics',
                        'upgrade_url': '/account/billing'
                    }
                )
    
    logger.info(f"API request: get_team_batting_analytics for team_id: {team_id}")
    try:
        analytics = AnalyticsService.get_player_batting_analytics(team_id)
        logger.info(f"Successfully retrieved batting analytics for team_id: {team_id}")
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error getting batting analytics for team_id {team_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return standardize_error_response("Failed to get batting analytics", 500, str(e))

@analytics_bp.route('/teams/<int:team_id>/players/fielding', methods=['GET'])
@jwt_required
def get_player_fielding_analytics(team_id):
    """
    Get fielding analytics for all players in a team using RESTful pattern.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with player fielding analytics
    """
    # Check feature access inside the function
    user_id = g.user_id
    
    # Check if user has the advanced analytics feature
    with db_session(read_only=True) as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return standardize_error_response(
                'User not found',
                404
            )
        
        # Skip feature check for admins
        if user.role != 'admin':
            if not has_feature(user.subscription_tier, 'advanced_analytics'):
                return standardize_error_response(
                    'Subscription required',
                    403,
                    {
                        'message': 'Advanced analytics requires a Pro subscription',
                        'current_tier': user.subscription_tier,
                        'required_feature': 'advanced_analytics',
                        'upgrade_url': '/account/billing'
                    }
                )
    
    return get_team_fielding_analytics(team_id)

@analytics_bp.route('/teams/<int:team_id>/fielding-analytics', methods=['GET'])
@jwt_required
def get_team_fielding_analytics(team_id):
    """
    Get fielding analytics for all players in a team.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with player fielding analytics
    """
    user_id = g.user_id
    
    # Check if user has the advanced analytics feature
    with db_session(read_only=True) as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return standardize_error_response(
                'User not found',
                404
            )
        
        # Skip feature check for admins
        if user.role != 'admin':
            if not has_feature(user.subscription_tier, 'advanced_analytics'):
                return standardize_error_response(
                    'Subscription required',
                    403,
                    {
                        'message': 'Advanced analytics requires a Pro subscription',
                        'current_tier': user.subscription_tier,
                        'required_feature': 'advanced_analytics',
                        'upgrade_url': '/account/billing'
                    }
                )
    
    logger.info(f"API request: get_team_fielding_analytics for team_id: {team_id}")
    try:
        analytics = AnalyticsService.get_player_fielding_analytics(team_id)
        logger.info(f"Successfully retrieved fielding analytics for team_id: {team_id}")
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error getting fielding analytics for team_id {team_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return standardize_error_response("Failed to get fielding analytics", 500, str(e))

@analytics_bp.route('/status', methods=['GET'])
def analytics_status():
    """
    Simple endpoint to verify the analytics module is loaded.
    """
    logger.info("Analytics status check requested")
    return jsonify({"status": "ok", "module": "analytics"}), 200

@analytics_bp.route('/teams/<int:team_id>', methods=['GET'])
@jwt_required
def get_team_analytics_restful(team_id):
    """
    Get team analytics across all games using RESTful pattern.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with team analytics
    """
    # Check feature access inside the function
    user_id = g.user_id
    
    # Check if user has the advanced analytics feature
    with db_session(read_only=True) as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return standardize_error_response(
                'User not found',
                404
            )
        
        # Skip feature check for admins
        if user.role != 'admin':
            if not has_feature(user.subscription_tier, 'advanced_analytics'):
                return standardize_error_response(
                    'Subscription required',
                    403,
                    {
                        'message': 'Advanced analytics requires a Pro subscription',
                        'current_tier': user.subscription_tier,
                        'required_feature': 'advanced_analytics',
                        'upgrade_url': '/account/billing'
                    }
                )
    
    return get_team_analytics(team_id)

@analytics_bp.route('/teams/<int:team_id>/analytics', methods=['GET'])
@jwt_required
def get_team_analytics(team_id):
    """
    Get team analytics across all games.
    
    Args:
        team_id: Team ID
        
    Returns:
        JSON response with team analytics
    """
    user_id = g.user_id
    
    # Check if user has the advanced analytics feature
    with db_session(read_only=True) as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return standardize_error_response(
                'User not found',
                404
            )
        
        # Skip feature check for admins
        if user.role != 'admin':
            if not has_feature(user.subscription_tier, 'advanced_analytics'):
                return standardize_error_response(
                    'Subscription required',
                    403,
                    {
                        'message': 'Advanced analytics requires a Pro subscription',
                        'current_tier': user.subscription_tier,
                        'required_feature': 'advanced_analytics',
                        'upgrade_url': '/account/billing'
                    }
                )
    
    logger.info(f"API request: get_team_analytics for team_id: {team_id}")
    try:
        analytics = AnalyticsService.get_team_analytics(team_id)
        logger.info(f"Successfully retrieved team analytics for team_id: {team_id}")
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error getting team analytics for team_id {team_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return standardize_error_response("Failed to get team analytics", 500, str(e))

@analytics_bp.route('/teams/<int:team_id>/debug', methods=['GET'])
@jwt_required
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
    logger.info(f"API request: debug_analytics_data for team_id: {team_id}")
    try:
        # Use regular session (not read_only) to avoid parameter errors
        with db_session() as session:
            # Get team
            team = session.query(Team).get(team_id)
            if not team:
                return jsonify({'status': 'error', 'message': 'Team not found'}), 404
            
            # Get games
            games = session.query(Game).filter_by(team_id=team_id).all()
            games_data = [{
                'id': g.id,
                'date': str(g.game_date) if hasattr(g, 'game_date') and g.game_date else None,
                'opponent': g.opponent
            } for g in games]
            
            # Get batting orders
            batting_orders = session.query(BattingOrder).filter(
                BattingOrder.game_id.in_([g.id for g in games])
            ).all()
            
            batting_data = []
            for bo in batting_orders:
                format_type = 'unknown'
                sample = None
                has_data = False
                
                if bo.order_data:
                    has_data = True
                    if isinstance(bo.order_data, list):
                        format_type = 'list'
                        sample = str(bo.order_data)[:100]
                    elif isinstance(bo.order_data, dict) and 'order_data' in bo.order_data:
                        format_type = 'dict_with_order_data'
                        sample = str(bo.order_data['order_data'])[:100]
                    else:
                        format_type = f'other: {type(bo.order_data)}'
                        sample = str(bo.order_data)[:100]
                
                batting_data.append({
                    'game_id': bo.game_id,
                    'format': format_type,
                    'has_data': has_data,
                    'sample': sample
                })
            
            # Get fielding rotations
            fielding_query = session.query(
                FieldingRotation.game_id, 
                func.count(FieldingRotation.id).label('count')
            ).filter(
                FieldingRotation.game_id.in_([g.id for g in games])
            ).group_by(FieldingRotation.game_id).all()
            
            fielding_data = {game_id: count for game_id, count in fielding_query}
            
            # Get games with both types of data
            games_with_batting = [bo.game_id for bo in batting_orders if bo.order_data]
            games_with_fielding = list(fielding_data.keys())
            games_with_both = [gid for gid in games_with_batting if gid in games_with_fielding]
            
            # Return diagnostic data
            return jsonify({
                'status': 'success',
                'team_id': team_id,
                'team_name': team.name,
                'games_count': len(games),
                'games_with_dates': len([g for g in games if hasattr(g, 'game_date') and g.game_date]),
                'batting_orders_count': len(batting_orders),
                'games_with_batting_data': len(games_with_batting),
                'games_with_fielding_data': len(games_with_fielding),
                'games_with_both_count': len(games_with_both),
                'games_with_both': games_with_both,
                'data_checks': {
                    'has_games': len(games) > 0,
                    'has_games_with_dates': len([g for g in games if hasattr(g, 'game_date') and g.game_date]) > 0,
                    'has_batting_data': len(games_with_batting) > 0,
                    'has_fielding_data': len(games_with_fielding) > 0,
                    'has_complete_games': len(games_with_both) > 0
                },
                'games': games_data,
                'batting_orders': batting_data,
                'fielding_games': fielding_data
            })
    except Exception as e:
        logger.error(f"Error in debug_analytics_data for team_id {team_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'team_id': team_id,
            'error': str(e)
        }), 500