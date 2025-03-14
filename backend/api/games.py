
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from datetime import datetime
from services.team_service import TeamService
from services.game_service import GameService

games = Blueprint("games", __name__)

@games.route('/team/<int:team_id>', methods=['GET'])
@jwt_required()
def get_games(team_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    db = get_db()
    
    try:
        # Verify team belongs to user
        team = TeamService.get_team(db, team_id, user_id)
        if not team:
            return jsonify({'error': 'Team not found or unauthorized'}), 404
        
        # Get all games for this team via service
        games_list = GameService.get_games_by_team(db, team_id)
        
        # Serialize game objects
        result = [GameService.serialize_game(game) for game in games_list]
        
        return jsonify(result), 200
    except Exception as e:
        db.rollback()
        print(f"Error getting games: {str(e)}")
        return jsonify({"error": "Failed to retrieve games"}), 500
    finally:
        db.close()

@games.route('/<int:game_id>', methods=['GET'])
@jwt_required()
def get_game(game_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    db = get_db()
    
    try:
        # Get game with verification that it belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
        
        # Serialize game object
        result = GameService.serialize_game(game)
        
        return jsonify(result), 200
    except Exception as e:
        db.rollback()
        print(f"Error getting game: {str(e)}")
        return jsonify({"error": "Failed to retrieve game"}), 500
    finally:
        db.close()

@games.route('/team/<int:team_id>', methods=['POST'])
@jwt_required()
def create_game(team_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    data = request.get_json()
    
    if not data or not data.get('game_number') or not data.get('opponent'):
        return jsonify({'error': 'Game number and opponent are required'}), 400
    
    db = get_db()
    
    try:
        # Verify team belongs to user
        team = TeamService.get_team(db, team_id, user_id)
        if not team:
            return jsonify({'error': 'Team not found or unauthorized'}), 404
        
        # Process date and time if provided
        game_data = {
            'game_number': data['game_number'],
            'opponent': data['opponent'],
            'innings': data.get('innings', 6)
        }
        
        # Handle date and time if provided
        if data.get('date'):
            try:
                game_data['date'] = datetime.fromisoformat(data['date']).date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
                
        if data.get('time'):
            try:
                game_data['time'] = datetime.strptime(data['time'], '%H:%M').time()
            except ValueError:
                return jsonify({'error': 'Invalid time format. Use 24-hour format (HH:MM)'}), 400
        
        # Create new game via service
        game = GameService.create_game(db, game_data, team_id)
        
        # Return successful response
        result = GameService.serialize_game(game)
        result['message'] = 'Game created successfully'
        
        return jsonify(result), 201
    except Exception as e:
        db.rollback()
        print(f"Error creating game: {str(e)}")
        return jsonify({"error": "Failed to create game"}), 500
    finally:
        db.close()

@games.route('/<int:game_id>', methods=['PUT'])
@jwt_required()
def update_game(game_id):
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
    
    db = get_db()
    
    try:
        # Verify game belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
        
        # Process game data
        game_data = {}
        if 'game_number' in data:
            game_data['game_number'] = data['game_number']
        if 'opponent' in data:
            game_data['opponent'] = data['opponent']
        if 'innings' in data:
            game_data['innings'] = data['innings']
        
        # Handle date and time if provided
        if 'date' in data:
            if data['date']:
                try:
                    game_data['date'] = datetime.fromisoformat(data['date']).date()
                except ValueError:
                    return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
            else:
                game_data['date'] = None
                
        if 'time' in data:
            if data['time']:
                try:
                    game_data['time'] = datetime.strptime(data['time'], '%H:%M').time()
                except ValueError:
                    return jsonify({'error': 'Invalid time format. Use 24-hour format (HH:MM)'}), 400
            else:
                game_data['time'] = None
        
        # Update game via service
        updated_game = GameService.update_game(db, game, game_data)
        
        # Return successful response
        result = GameService.serialize_game(updated_game)
        result['message'] = 'Game updated successfully'
        
        return jsonify(result), 200
    except Exception as e:
        db.rollback()
        print(f"Error updating game: {str(e)}")
        return jsonify({"error": "Failed to update game"}), 500
    finally:
        db.close()

@games.route('/<int:game_id>', methods=['DELETE'])
@jwt_required()
def delete_game(game_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    db = get_db()
    
    try:
        # Verify game belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
            
        # Delete game via service
        GameService.delete_game(db, game)
        
        return jsonify({
            'message': 'Game deleted successfully'
        }), 200
    except Exception as e:
        db.rollback()
        print(f"Error deleting game: {str(e)}")
        return jsonify({"error": "Failed to delete game"}), 500
    finally:
        db.close()

# Batting Order endpoints
@games.route('/<int:game_id>/batting-order', methods=['GET'])
@jwt_required()
def get_batting_order(game_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    db = get_db()
    
    try:
        # Verify game belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
        
        # Get batting order via service
        batting_order = GameService.get_batting_order(db, game_id)
        
        if not batting_order:
            return jsonify({'error': 'Batting order not found for this game'}), 404
        
        # Serialize batting order
        result = GameService.serialize_batting_order(batting_order)
        
        return jsonify(result), 200
    except Exception as e:
        db.rollback()
        print(f"Error getting batting order: {str(e)}")
        return jsonify({"error": "Failed to retrieve batting order"}), 500
    finally:
        db.close()

@games.route('/<int:game_id>/batting-order', methods=['POST', 'PUT'])
@jwt_required()
def save_batting_order(game_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    data = request.get_json()
    
    if not data or 'order_data' not in data:
        return jsonify({'error': 'Batting order data is required'}), 400
    
    db = get_db()
    
    try:
        # Verify game belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
        
        # Check if batting order already exists to determine status code
        existing_batting_order = GameService.get_batting_order(db, game_id)
        status_code = 200 if existing_batting_order else 201
        
        # Create or update batting order via service
        batting_order = GameService.create_or_update_batting_order(db, game_id, data['order_data'])
        
        # Serialize response
        result = GameService.serialize_batting_order(batting_order)
        result['message'] = 'Batting order updated successfully' if status_code == 200 else 'Batting order created successfully'
        
        return jsonify(result), status_code
    except Exception as e:
        db.rollback()
        print(f"Error saving batting order: {str(e)}")
        return jsonify({"error": "Failed to save batting order"}), 500
    finally:
        db.close()

# Fielding Rotation endpoints
@games.route('/<int:game_id>/fielding-rotations', methods=['GET'])
@jwt_required()
def get_fielding_rotations(game_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    db = get_db()
    
    try:
        # Verify game belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
        
        # Get fielding rotations via service
        rotations = GameService.get_fielding_rotations(db, game_id)
        
        # Serialize rotation objects
        result = [GameService.serialize_fielding_rotation(rotation) for rotation in rotations]
        
        return jsonify(result), 200
    except Exception as e:
        db.rollback()
        print(f"Error getting fielding rotations: {str(e)}")
        return jsonify({"error": "Failed to retrieve fielding rotations"}), 500
    finally:
        db.close()

@games.route('/<int:game_id>/fielding-rotations/<int:inning>', methods=['POST', 'PUT'])
@jwt_required()
def save_fielding_rotation(game_id, inning):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    data = request.get_json()
    
    if not data or 'positions' not in data:
        return jsonify({'error': 'Positions data is required'}), 400
    
    db = get_db()
    
    try:
        # Verify game belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
        
        # Check if fielding rotation already exists to determine status code
        existing_rotation = GameService.get_fielding_rotation_by_inning(db, game_id, inning)
        status_code = 200 if existing_rotation else 201
        
        # Create or update fielding rotation via service
        rotation = GameService.create_or_update_fielding_rotation(db, game_id, inning, data['positions'])
        
        # Serialize response
        result = GameService.serialize_fielding_rotation(rotation)
        result['message'] = 'Fielding rotation updated successfully' if status_code == 200 else 'Fielding rotation created successfully'
        
        return jsonify(result), status_code
    except Exception as e:
        db.rollback()
        print(f"Error saving fielding rotation: {str(e)}")
        return jsonify({"error": "Failed to save fielding rotation"}), 500
    finally:
        db.close()

# Player Availability endpoints
@games.route('/<int:game_id>/player-availability', methods=['GET'])
@jwt_required()
def get_player_availability(game_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    db = get_db()
    
    try:
        # Verify game belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
        
        # Get player availability records via service
        availability_records = GameService.get_player_availability(db, game_id)
        
        # Serialize availability records with player information
        result = [GameService.serialize_player_availability(record, include_player=True) 
                  for record in availability_records]
        
        return jsonify(result), 200
    except Exception as e:
        db.rollback()
        print(f"Error getting player availability: {str(e)}")
        return jsonify({"error": "Failed to retrieve player availability"}), 500
    finally:
        db.close()

@games.route('/<int:game_id>/player-availability/<int:player_id>', methods=['POST', 'PUT'])
@jwt_required()
def save_player_availability(game_id, player_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    data = request.get_json()
    
    if not isinstance(data.get('available'), bool) or not isinstance(data.get('can_play_catcher'), bool):
        return jsonify({'error': 'Available and can_play_catcher fields are required as boolean values'}), 400
    
    db = get_db()
    
    try:
        # Verify game belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
        
        # Verify player belongs to user's team via player service
        from services.player_service import PlayerService
        player = PlayerService.get_player(db, player_id, user_id)
        if not player:
            return jsonify({'error': 'Player not found or unauthorized'}), 404
        
        # Check if availability record already exists to determine status code
        existing_availability = GameService.get_player_availability_by_player(db, game_id, player_id)
        status_code = 200 if existing_availability else 201
        
        # Set player availability via service
        availability = GameService.set_player_availability(
            db, game_id, player_id, data['available'], data['can_play_catcher']
        )
        
        # Serialize response
        result = GameService.serialize_player_availability(availability)
        result['message'] = 'Player availability updated successfully' if status_code == 200 else 'Player availability created successfully'
        
        return jsonify(result), status_code
    except Exception as e:
        db.rollback()
        print(f"Error setting player availability: {str(e)}")
        return jsonify({"error": "Failed to set player availability"}), 500
    finally:
        db.close()

@games.route('/<int:game_id>/player-availability/batch', methods=['POST'])
@jwt_required()
def batch_save_player_availability(game_id):
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    data = request.get_json()
    
    if not data or not isinstance(data, list) or len(data) == 0:
        return jsonify({'error': 'A list of player availability records is required'}), 400
    
    # Validate each record in the batch
    for idx, record in enumerate(data):
        if not isinstance(record, dict) or 'player_id' not in record or not isinstance(record.get('available'), bool):
            return jsonify({'error': f'Invalid record at index {idx}: Must contain player_id and availability status'}), 400
    
    db = get_db()
    
    try:
        # Verify game belongs to user's team via service
        game = GameService.get_game(db, game_id, user_id)
        if not game:
            return jsonify({'error': 'Game not found or unauthorized'}), 404
        
        # Verify all players belong to user's team
        from services.player_service import PlayerService
        player_ids = [record['player_id'] for record in data]
        for player_id in player_ids:
            player = PlayerService.get_player(db, player_id, user_id)
            if not player:
                return jsonify({'error': f'Player with ID {player_id} not found or unauthorized'}), 404
        
        # Batch update player availability via service
        updated_records = GameService.batch_set_player_availability(db, game_id, data)
        
        # Serialize responses
        result = [GameService.serialize_player_availability(record) for record in updated_records]
        
        return jsonify({
            'message': f'Successfully updated {len(updated_records)} player availability records',
            'records': result
        }), 200
    except Exception as e:
        db.rollback()
        print(f"Error updating player availability in batch: {str(e)}")
        return jsonify({"error": "Failed to update player availability"}), 500
    finally:
        db.close()
