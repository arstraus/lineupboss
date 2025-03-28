"""
Simplified analytics blueprint for debugging route registration issues.
"""
from flask import Blueprint, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

# Create a simple blueprint for testing
simple_analytics_bp = Blueprint('simple_analytics', __name__)

@simple_analytics_bp.route('/status', methods=['GET'])
def analytics_status():
    """Simple endpoint to verify the analytics module is loaded."""
    return jsonify({"status": "ok", "module": "analytics"})

@simple_analytics_bp.route('/test', methods=['GET'])
def analytics_test():
    """Test endpoint for analytics."""
    return jsonify({"message": "Analytics test endpoint is working"})

@simple_analytics_bp.route('/teams/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team_analytics(team_id):
    """Simple team analytics endpoint."""
    user_id = get_jwt_identity()
    
    return jsonify({
        "team_id": team_id,
        "user_id": user_id,
        "status": "ok",
        "message": "Simple team analytics endpoint",
        "data": {
            "team_stats": {
                "total_games": 0,
                "games_with_data": 0
            }
        }
    })

@simple_analytics_bp.route('/teams/<int:team_id>/analytics', methods=['GET'])
@jwt_required()
def get_team_analytics_legacy(team_id):
    """Legacy team analytics endpoint."""
    return get_team_analytics(team_id)

@simple_analytics_bp.route('/teams/<int:team_id>/players/batting', methods=['GET'])
@jwt_required()
def get_player_batting_analytics(team_id):
    """Player batting analytics endpoint."""
    return jsonify({
        "team_id": team_id,
        "status": "ok",
        "message": "Player batting analytics endpoint",
        "data": {
            "players": []
        }
    })

@simple_analytics_bp.route('/teams/<int:team_id>/batting-analytics', methods=['GET'])
@jwt_required()
def get_batting_analytics_legacy(team_id):
    """Legacy batting analytics endpoint."""
    return get_player_batting_analytics(team_id)

@simple_analytics_bp.route('/teams/<int:team_id>/players/fielding', methods=['GET'])
@jwt_required()
def get_player_fielding_analytics(team_id):
    """Player fielding analytics endpoint."""
    return jsonify({
        "team_id": team_id,
        "status": "ok",
        "message": "Player fielding analytics endpoint",
        "data": {
            "players": []
        }
    })

@simple_analytics_bp.route('/teams/<int:team_id>/fielding-analytics', methods=['GET'])
@jwt_required()
def get_fielding_analytics_legacy(team_id):
    """Legacy fielding analytics endpoint."""
    return get_player_fielding_analytics(team_id)

@simple_analytics_bp.route('/teams/<int:team_id>/debug', methods=['GET'])
@jwt_required()
def debug_analytics_data(team_id):
    """Debug endpoint for analytics."""
    return jsonify({
        "team_id": team_id,
        "status": "ok",
        "message": "Debug analytics endpoint",
        "data": {
            "debug_info": {
                "timestamp": "2025-03-28T23:30:00Z",
                "routes_active": True
            }
        }
    })