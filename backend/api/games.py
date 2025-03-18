
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from shared.database import db_session, db_error_response, db_get_or_404
from datetime import datetime
from services.team_service import TeamService
from services.game_service import GameService
from services.ai_service import AIService
from shared.models import Game, Team

# Main games blueprint
games = Blueprint("games", __name__)

# Nested routes blueprint for team-specific game operations
games_nested = Blueprint("games_nested", __name__)

# Keep the original route for backward compatibility
@games.route('/team/<int:team_id>', methods=['GET'])
@jwt_required()
def get_games_legacy(team_id):
    return get_games(team_id)

# Add a properly nested route
@games_nested.route('/<int:team_id>/games', methods=['GET'])
@jwt_required()
def get_games(team_id):
    """Get all games for a specific team.
    
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
            
            # Get all games for this team via service
            games_list = GameService.get_games_by_team(session, team_id)
            
            # Serialize game objects
            result = [GameService.serialize_game(game) for game in games_list]
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error getting games: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to retrieve games")

@games.route('/<int:game_id>', methods=['GET'])
@jwt_required()
def get_game(game_id):
    """Get a specific game by ID.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Structured error handling with db_error_response
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
            # Get game with verification that it belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Serialize game object
            result = GameService.serialize_game(game)
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error getting game {game_id}: {str(e)}")
        # Use standardized error response
        return db_error_response(e, "Failed to retrieve game")

@games.route('/team/<int:team_id>', methods=['POST'])
@jwt_required()
def create_game(team_id):
    """Create a new game for a specific team.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with db_error_response
    - Two-phase operation: verify team ownership, then create game
    """
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
    
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Verify team belongs to user
            team = TeamService.get_team(session, team_id, user_id)
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
            game = GameService.create_game(session, game_data, team_id)
            
            # Return successful response
            result = GameService.serialize_game(game)
            result['message'] = 'Game created successfully'
            
            return jsonify(result), 201
    except Exception as e:
        print(f"Error creating game: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to create game")

@games.route('/<int:game_id>', methods=['PUT'])
@jwt_required()
def update_game(game_id):
    """Update a specific game by ID.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with db_error_response
    - Data validation and formatting
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
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            
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
            updated_game = GameService.update_game(session, game, game_data)
            
            # Return successful response
            result = GameService.serialize_game(updated_game)
            result['message'] = 'Game updated successfully'
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error updating game: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to update game")

@games.route('/<int:game_id>', methods=['DELETE'])
@jwt_required()
def delete_game(game_id):
    """Delete a specific game by ID.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with db_error_response
    - Authorization verification
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
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
                
            # Delete game via service
            GameService.delete_game(session, game)
            
            return jsonify({
                'message': 'Game deleted successfully'
            }), 200
    except Exception as e:
        print(f"Error deleting game: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to delete game")

# Batting Order endpoints
@games.route('/<int:game_id>/batting-order', methods=['GET'])
@jwt_required()
def get_batting_order(game_id):
    """Get batting order for a specific game.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Structured error handling with db_error_response
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
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Get batting order via service
            batting_order = GameService.get_batting_order(session, game_id)
            
            if not batting_order:
                return jsonify({'error': 'Batting order not found for this game'}), 404
            
            # Serialize batting order
            result = GameService.serialize_batting_order(batting_order)
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error getting batting order: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to retrieve batting order")


@games.route('/<int:game_id>/batting-order', methods=['POST', 'PUT'])
@jwt_required()
def save_batting_order(game_id):
    """Create or update batting order for a specific game.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with db_error_response
    - Data validation and transformation
    """
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
    
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Check if batting order already exists to determine status code
            existing_batting_order = GameService.get_batting_order(session, game_id)
            status_code = 200 if existing_batting_order else 201
            
            # Create or update batting order via service
            batting_order = GameService.create_or_update_batting_order(session, game_id, data['order_data'])
            
            # Serialize response
            result = GameService.serialize_batting_order(batting_order)
            result['message'] = 'Batting order updated successfully' if status_code == 200 else 'Batting order created successfully'
            
            return jsonify(result), status_code
    except Exception as e:
        print(f"Error saving batting order: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to save batting order")


# Fielding Rotation endpoints
@games.route('/<int:game_id>/fielding-rotations', methods=['GET'])
@jwt_required()
def get_fielding_rotations(game_id):
    """Get fielding rotations for a specific game.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Structured error handling with db_error_response
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
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Get fielding rotations via service
            rotations = GameService.get_fielding_rotations(session, game_id)
            
            # Serialize rotation objects
            result = [GameService.serialize_fielding_rotation(rotation) for rotation in rotations]
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error getting fielding rotations: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to retrieve fielding rotations")


@games.route('/<int:game_id>/fielding-rotations/<int:inning>', methods=['POST', 'PUT'])
@jwt_required()
def save_fielding_rotation(game_id, inning):
    """Create or update fielding rotation for a specific game and inning.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with db_error_response
    - Data validation and transformation
    """
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
    
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Check if fielding rotation already exists to determine status code
            existing_rotation = GameService.get_fielding_rotation_by_inning(session, game_id, inning)
            status_code = 200 if existing_rotation else 201
            
            # Create or update fielding rotation via service
            rotation = GameService.create_or_update_fielding_rotation(session, game_id, inning, data['positions'])
            
            # Serialize response
            result = GameService.serialize_fielding_rotation(rotation)
            result['message'] = 'Fielding rotation updated successfully' if status_code == 200 else 'Fielding rotation created successfully'
            
            return jsonify(result), status_code
    except Exception as e:
        print(f"Error saving fielding rotation: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to save fielding rotation")


# Player Availability endpoints
@games.route('/<int:game_id>/player-availability', methods=['GET'])
@jwt_required()
def get_player_availability(game_id):
    """Get player availability for a specific game.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Structured error handling with db_error_response
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
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Get player availability records via service
            availability_records = GameService.get_player_availability(session, game_id)
            
            # Serialize availability records with player information
            result = [GameService.serialize_player_availability(record, include_player=True) 
                      for record in availability_records]
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error getting player availability: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to retrieve player availability")


@games.route('/<int:game_id>/player-availability/<int:player_id>', methods=['POST', 'PUT'])
@jwt_required()
def save_player_availability(game_id, player_id):
    """Create or update player availability for a specific game and player.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with db_error_response
    - Data validation and transformation
    """
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
    
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Verify player belongs to user's team via player service
            from services.player_service import PlayerService
            player = PlayerService.get_player(session, player_id, user_id)
            if not player:
                return jsonify({'error': 'Player not found or unauthorized'}), 404
            
            # Check if availability record already exists to determine status code
            existing_availability = GameService.get_player_availability_by_player(session, game_id, player_id)
            status_code = 200 if existing_availability else 201
            
            # Set player availability via service
            availability = GameService.set_player_availability(
                session, game_id, player_id, data['available'], data['can_play_catcher']
            )
            
            # Serialize response
            result = GameService.serialize_player_availability(availability)
            result['message'] = 'Player availability updated successfully' if status_code == 200 else 'Player availability created successfully'
            
            return jsonify(result), status_code
    except Exception as e:
        print(f"Error setting player availability: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to set player availability")


@games.route('/<int:game_id>/player-availability/batch', methods=['POST'])
@jwt_required()
def batch_save_player_availability(game_id):
    """Update multiple player availability records for a specific game in a single operation.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with db_error_response
    - Batch data validation and processing
    """
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
    
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Verify all players belong to user's team
            from services.player_service import PlayerService
            player_ids = [record['player_id'] for record in data]
            for player_id in player_ids:
                player = PlayerService.get_player(session, player_id, user_id)
                if not player:
                    return jsonify({'error': f'Player with ID {player_id} not found or unauthorized'}), 404
            
            # Batch update player availability via service
            updated_records = GameService.batch_set_player_availability(session, game_id, data)
            
            # Serialize responses
            result = [GameService.serialize_player_availability(record) for record in updated_records]
            
            return jsonify({
                'message': f'Successfully updated {len(updated_records)} player availability records',
                'records': result
            }), 200
    except Exception as e:
        print(f"Error updating player availability in batch: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to update player availability")


# AI Fielding Rotation endpoint
@games.route('/<int:game_id>/ai-fielding-rotation', methods=['POST'])
@jwt_required()
def generate_ai_fielding_rotation(game_id):
    """Generate AI-based fielding rotation for a specific game.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed) for verification
    - Structured error handling with db_error_response
    """
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
        
    data = request.get_json()
    
    if not data or 'players' not in data or not isinstance(data['players'], list):
        return jsonify({'error': 'Player data is required'}), 400
    
    try:
        # Using read_only mode since this is just a verification and AI computation
        with db_session(read_only=True) as session:
            # Verify game belongs to user's team via service
            game = GameService.get_game(session, game_id, user_id)
            if not game:
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Get required parameters from request data
            players = data['players']
            innings = data.get('innings', game.innings) or 6  # Default to game innings or fallback to 6
            required_positions = data.get('required_positions', [])
            infield_positions = data.get('infield_positions', [])
            outfield_positions = data.get('outfield_positions', [])
            
            # Use the AI service to generate fielding rotation
            rotation_result = AIService.generate_fielding_rotation(
                game_id, 
                players, 
                innings,
                required_positions,
                infield_positions,
                outfield_positions
            )
            
            return jsonify(rotation_result), 200
    except ValueError as e:
        print(f"Error generating AI fielding rotation: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error generating AI fielding rotation: {str(e)}")
        # Use standardized error response
        return db_error_response(e, "Failed to generate AI fielding rotation")

