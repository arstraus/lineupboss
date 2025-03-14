
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from services.team_service import TeamService
from services.player_service import PlayerService

players = Blueprint("players", __name__)

@players.route('/team/<int:team_id>', methods=['GET'])
@jwt_required()
def get_players(team_id):
    user_id = get_jwt_identity()
    db = next(get_db())
    
    # Verify team belongs to user
    team = TeamService.get_team(db, team_id, user_id)
    if not team:
        return jsonify({'error': 'Team not found or unauthorized'}), 404
    
    # Get all players for this team via service
    players_list = PlayerService.get_players_by_team(db, team_id)
    
    # Serialize player objects
    result = [PlayerService.serialize_player(player) for player in players_list]
    
    return jsonify(result), 200

@players.route('/<int:player_id>', methods=['GET'])
@jwt_required()
def get_player(player_id):
    user_id = get_jwt_identity()
    db = next(get_db())
    
    # Get player with verification that it belongs to user's team via service
    player = PlayerService.get_player(db, player_id, user_id)
    
    if not player:
        return jsonify({'error': 'Player not found or unauthorized'}), 404
    
    # Serialize player object
    result = PlayerService.serialize_player(player)
    
    return jsonify(result), 200

@players.route('/team/<int:team_id>', methods=['POST'])
@jwt_required()
def create_player(team_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('first_name') or not data.get('last_name') or not data.get('jersey_number'):
        return jsonify({'error': 'First name, last name and jersey number are required'}), 400
    
    db = next(get_db())
    
    # Verify team belongs to user
    team = TeamService.get_team(db, team_id, user_id)
    if not team:
        return jsonify({'error': 'Team not found or unauthorized'}), 404
    
    # Create new player via service
    player = PlayerService.create_player(db, data, team_id)
    
    # Return serialized player with success message
    result = PlayerService.serialize_player(player)
    result['message'] = 'Player created successfully'
    
    return jsonify(result), 201

@players.route('/<int:player_id>', methods=['PUT'])
@jwt_required()
def update_player(player_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    db = next(get_db())
    
    # Verify player belongs to user's team via service
    player = PlayerService.get_player(db, player_id, user_id)
    
    if not player:
        return jsonify({'error': 'Player not found or unauthorized'}), 404
    
    # Update player details via service
    updated_player = PlayerService.update_player(db, player, data)
    
    # Return serialized player with success message
    result = PlayerService.serialize_player(updated_player)
    result['message'] = 'Player updated successfully'
    
    return jsonify(result), 200

@players.route('/<int:player_id>', methods=['DELETE'])
@jwt_required()
def delete_player(player_id):
    user_id = get_jwt_identity()
    db = next(get_db())
    
    # Verify player belongs to user's team via service
    player = PlayerService.get_player(db, player_id, user_id)
    
    if not player:
        return jsonify({'error': 'Player not found or unauthorized'}), 404
    
    # Delete player via service
    PlayerService.delete_player(db, player)
    
    return jsonify({
        'message': 'Player deleted successfully'
    }), 200
