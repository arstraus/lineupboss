"""
Simplified analytics blueprint for debugging route registration issues.
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

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
    return jsonify({
        "team_id": team_id,
        "status": "ok",
        "message": "Simple team analytics endpoint",
        "data": {
            "team_stats": {
                "total_games": 0,
                "games_with_data": 0
            }
        }
    })