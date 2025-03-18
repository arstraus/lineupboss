
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from shared.database import db_session, db_error_response, db_get_or_404
from services.team_service import TeamService
from services.player_service import PlayerService
from shared.models import Player, Team

# Main players blueprint
players = Blueprint("players", __name__)

# Nested routes blueprint for team-specific player operations
players_nested = Blueprint("players_nested", __name__)

# Keep the original route for backward compatibility
@players.route('/team/<int:team_id>', methods=['GET'])
@jwt_required()
def get_players_legacy(team_id):
    return get_players(team_id)

# Add a properly nested route
@players_nested.route('/<int:team_id>/players', methods=['GET'])
@jwt_required()
def get_players(team_id):
    """Get all players for a specific team.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Structured error handling
    """
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
    
    try:
        # Using read_only mode since this is just a query operation
        with db_session(read_only=True) as session:
            # Verify team belongs to user
            team = TeamService.get_team(session, team_id, user_id)
            if not team:
                return jsonify({'error': 'Team not found or unauthorized'}), 404
            
            # Get all players for this team via service
            players_list = PlayerService.get_players_by_team(session, team_id)
            
            # Serialize player objects
            result = [PlayerService.serialize_player(player) for player in players_list]
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error getting players: {str(e)}")
        # Use standardized error response
        return db_error_response(e, "Failed to retrieve players")

@players.route('/<int:player_id>', methods=['GET'])
@jwt_required()
def get_player(player_id):
    """Get a specific player by ID.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Attempt to use db_get_or_404 utility
    """
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
    
    try:
        # Using read_only mode since this is just a query operation
        with db_session(read_only=True) as session:
            # Get player with verification that it belongs to user's team via service
            player = PlayerService.get_player(session, player_id, user_id)
            
            if not player:
                return jsonify({'error': 'Player not found or unauthorized'}), 404
            
            # Serialize player object
            result = PlayerService.serialize_player(player)
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error getting player {player_id}: {str(e)}")
        # Use standardized error response
        return db_error_response(e, "Failed to retrieve player")

@players.route('/team/<int:team_id>', methods=['POST'])
@jwt_required()
def create_player(team_id):
    """Create a new player.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling
    - Two-phase operation: verify team ownership, then create player
    """
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    data = request.get_json()
    
    if not data or not data.get('first_name') or not data.get('last_name') or not data.get('jersey_number'):
        return jsonify({'error': 'First name, last name and jersey number are required'}), 400
    
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Verify team belongs to user
            team = TeamService.get_team(session, team_id, user_id)
            if not team:
                return jsonify({'error': 'Team not found or unauthorized'}), 404
            
            # Create new player via service
            player = PlayerService.create_player(session, data, team_id)
            
            # Return serialized player with success message
            result = PlayerService.serialize_player(player)
            result['message'] = 'Player created successfully'
            
            return jsonify(result), 201
    except Exception as e:
        print(f"Error creating player: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to create player")

@players.route('/<int:player_id>', methods=['PUT'])
@jwt_required()
def update_player(player_id):
    """Update an existing player.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling
    - Two-phase operation: verify ownership, then update
    """
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Verify player belongs to user's team via service
            player = PlayerService.get_player(session, player_id, user_id)
            
            if not player:
                return jsonify({'error': 'Player not found or unauthorized'}), 404
            
            # Update player details via service
            updated_player = PlayerService.update_player(session, player, data)
            
            # Return serialized player with success message
            result = PlayerService.serialize_player(updated_player)
            result['message'] = 'Player updated successfully'
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error updating player {player_id}: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to update player")

@players.route('/<int:player_id>', methods=['DELETE'])
@jwt_required()
def delete_player(player_id):
    """Delete an existing player.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling
    - Two-phase operation: verify ownership, then delete
    """
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
    
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Verify player belongs to user's team via service
            player = PlayerService.get_player(session, player_id, user_id)
            
            if not player:
                return jsonify({'error': 'Player not found or unauthorized'}), 404
            
            # Delete player via service
            PlayerService.delete_player(session, player)
            
            return jsonify({
                'message': 'Player deleted successfully'
            }), 200
    except Exception as e:
        print(f"Error deleting player {player_id}: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to delete player")
