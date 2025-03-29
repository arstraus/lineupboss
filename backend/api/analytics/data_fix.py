"""
Data fix utilities for analytics.

This module provides endpoints for fixing missing data required for analytics.
These endpoints should only be accessible to admin users.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db_session
from models.models import Game, Team, User
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint for data fix utilities
data_fix_bp = Blueprint('data_fix', __name__)

@data_fix_bp.route('/fix-game-dates/<int:team_id>', methods=['POST'])
@jwt_required()
def fix_game_dates(team_id):
    """
    Fix missing game dates for a team.
    
    This endpoint adds dates to games that don't have them,
    which is required for analytics to work properly.
    
    Args:
        team_id: Team ID to fix games for
    
    Returns:
        JSON response with fix results
    """
    user_id = get_jwt_identity()
    
    # Only allow admins to perform this operation
    with db_session(read_only=True) as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user or user.role != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        # Check if team exists
        team = session.query(Team).get(team_id)
        if not team:
            return jsonify({"error": f"Team with ID {team_id} not found"}), 404
    
    # Fix the dates
    with db_session(commit=True) as session:
        games = session.query(Game).filter_by(team_id=team_id).all()
        logger.info(f"Found {len(games)} games for team {team_id}")
        
        # Base date - start from a month ago
        base_date = datetime.now() - timedelta(days=30)
        
        updated_count = 0
        games_info = []
        
        for i, game in enumerate(games):
            game_info = {
                "id": game.id,
                "opponent": game.opponent,
                "old_date": game.game_date.strftime("%Y-%m-%d") if hasattr(game, 'game_date') and game.game_date else None
            }
            
            if not hasattr(game, 'game_date') or game.game_date is None:
                # Assign a date starting from base_date, spread 3 days apart
                game_date = base_date + timedelta(days=i*3)
                game.game_date = game_date
                game_info["new_date"] = game_date.strftime("%Y-%m-%d")
                updated_count += 1
            
            games_info.append(game_info)
    
    return jsonify({
        "success": True,
        "team_id": team_id,
        "total_games": len(games),
        "updated_games": updated_count,
        "games": games_info
    })

@data_fix_bp.route('/check-game-dates/<int:team_id>', methods=['GET'])
@jwt_required()
def check_game_dates(team_id):
    """
    Check game dates for a team.
    
    Args:
        team_id: Team ID to check games for
    
    Returns:
        JSON response with game date information
    """
    user_id = get_jwt_identity()
    
    # Only allow admins or team owners to view this information
    with db_session(read_only=True) as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check if team exists
        team = session.query(Team).get(team_id)
        if not team:
            return jsonify({"error": f"Team with ID {team_id} not found"}), 404
        
        # Check if user is admin or team owner
        is_admin = user.role == 'admin'
        is_owner = team.user_id == int(user_id)
        
        if not (is_admin or is_owner):
            return jsonify({"error": "You don't have permission to view this information"}), 403
        
        # Get game information
        games = session.query(Game).filter_by(team_id=team_id).all()
        
        games_with_dates = [g for g in games if hasattr(g, 'game_date') and g.game_date is not None]
        games_info = [
            {
                "id": game.id,
                "opponent": game.opponent,
                "date": game.game_date.strftime("%Y-%m-%d") if hasattr(game, 'game_date') and game.game_date else None
            }
            for game in games
        ]
    
    return jsonify({
        "team_id": team_id,
        "total_games": len(games),
        "games_with_dates": len(games_with_dates),
        "games_missing_dates": len(games) - len(games_with_dates),
        "games": games_info
    })