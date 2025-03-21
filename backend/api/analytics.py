"""
API endpoints for analytics.
"""
from flask import Blueprint, jsonify, request
from shared.db import db_error_response
from services.analytics_service import AnalyticsService
from middleware.auth import jwt_required

# Create blueprint
analytics_bp = Blueprint('analytics', __name__)

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
    try:
        analytics = AnalyticsService.get_player_batting_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return db_error_response(e, "Failed to get batting analytics")

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
    try:
        analytics = AnalyticsService.get_player_fielding_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return db_error_response(e, "Failed to get fielding analytics")

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
    try:
        analytics = AnalyticsService.get_team_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        return db_error_response(e, "Failed to get team analytics")