"""
API endpoints for analytics.
"""
from flask import Blueprint, jsonify, request
import logging
import traceback
from shared.db import db_error_response
from services.analytics_service import AnalyticsService
from middleware.auth import jwt_required

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/status', methods=['GET'])
def analytics_status():
    """
    Simple endpoint to verify the analytics module is loaded.
    """
    logger.info("Analytics status check requested")
    return jsonify({"status": "ok", "module": "analytics"}), 200

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
    logger.info(f"API request: get_team_batting_analytics for team_id: {team_id}")
    try:
        analytics = AnalyticsService.get_player_batting_analytics(team_id)
        logger.info(f"Successfully retrieved batting analytics for team_id: {team_id}")
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error getting batting analytics for team_id {team_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return db_error_response(e, "Failed to get batting analytics")

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
    logger.info(f"API request: get_player_batting_analytics (RESTful) for team_id: {team_id}")
    return get_team_batting_analytics(team_id)

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
    logger.info(f"API request: get_team_fielding_analytics for team_id: {team_id}")
    try:
        analytics = AnalyticsService.get_player_fielding_analytics(team_id)
        logger.info(f"Successfully retrieved fielding analytics for team_id: {team_id}")
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error getting fielding analytics for team_id {team_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return db_error_response(e, "Failed to get fielding analytics")

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
    logger.info(f"API request: get_player_fielding_analytics (RESTful) for team_id: {team_id}")
    return get_team_fielding_analytics(team_id)

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
    logger.info(f"API request: get_team_analytics for team_id: {team_id}")
    try:
        analytics = AnalyticsService.get_team_analytics(team_id)
        logger.info(f"Successfully retrieved team analytics for team_id: {team_id}")
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error getting team analytics for team_id {team_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return db_error_response(e, "Failed to get team analytics")

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
    logger.info(f"API request: get_team_analytics_restful for team_id: {team_id}")
    return get_team_analytics(team_id)