
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from shared.database import db_session, db_error_response, db_get_or_404
from services.team_service import TeamService
from services.player_service import PlayerService
from shared.models import Player, Team
import csv
import io
import os
import tempfile

# Main players blueprint
players = Blueprint("players", __name__)

# Nested routes blueprint for team-specific player operations
players_nested = Blueprint("players_nested", __name__)

@players_nested.route('/<int:team_id>/players/csv-template', methods=['GET'])
@jwt_required()
def download_csv_template(team_id):
    """Download a CSV template for player imports.
    
    Provides a template CSV file with headers that match the required fields
    for player imports.
    """
    user_id = get_jwt_identity()
    
    try:
        # Convert user_id to integer if it's a string
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
            
            # Create CSV template in memory
            csv_data = io.StringIO()
            writer = csv.writer(csv_data)
            
            # Write headers
            writer.writerow(["first_name", "last_name", "jersey_number"])
            
            # Write sample data
            writer.writerow(["John", "Smith", "7"])
            writer.writerow(["Sarah", "Johnson", "15"])
            
            # Prepare file for download
            csv_data.seek(0)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(csv_data.getvalue().encode('utf-8'))
            temp_file_path = temp_file.name
            temp_file.close()
            
            file_name = f"{team.name.replace(' ', '_')}_players_template.csv"
            
            try:
                return send_file(
                    temp_file_path,
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=file_name
                )
            finally:
                # Clean up temp file after response is sent
                os.remove(temp_file_path)
                
    except Exception as e:
        print(f"Error creating CSV template: {str(e)}")
        return db_error_response(e, "Failed to generate CSV template")

# Keep the original route for backward compatibility
@players.route('/team/<int:team_id>', methods=['GET'])
@jwt_required()
def get_players_legacy(team_id):
    return get_players(team_id)

# Add properly nested routes
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
def create_player_legacy(team_id):
    """Legacy endpoint for creating a player. Redirects to the standard RESTful endpoint."""
    return create_player(team_id)

@players_nested.route('/<int:team_id>/players', methods=['POST'])
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
    
    content_type = request.headers.get('Content-Type', '')
        
    # Handle CSV file upload
    if 'multipart/form-data' in content_type:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV file'}), 400
        
        try:
            # Parse CSV file
            csv_file = io.StringIO(file.read().decode('utf-8'))
            csv_reader = csv.DictReader(csv_file)
            
            # Check for required headers
            required_fields = ['first_name', 'last_name', 'jersey_number']
            if not all(field in csv_reader.fieldnames for field in required_fields):
                return jsonify({'error': 'CSV file must include headers: first_name, last_name, jersey_number'}), 400
            
            # Using commit=True to automatically commit successful operations
            with db_session(commit=True) as session:
                # Verify team belongs to user
                team = TeamService.get_team(session, team_id, user_id)
                if not team:
                    return jsonify({'error': 'Team not found or unauthorized'}), 404
                
                # Delete existing players if overrideExisting flag is set
                override_existing = request.form.get('overrideExisting', 'false').lower() == 'true'
                if override_existing:
                    existing_players = PlayerService.get_players_by_team(session, team_id)
                    for player in existing_players:
                        session.delete(player)
                    session.flush()
                
                players_imported = 0
                errors = []
                
                # Process each row in the CSV file
                for idx, row in enumerate(csv_reader, start=2):  # start=2 for 1-based indexing and skipping header
                    try:
                        # Validate row data
                        for field in required_fields:
                            if not row.get(field, '').strip():
                                errors.append(f"Row {idx}: Missing {field}")
                                continue
                        
                        # Create player using service
                        player = PlayerService.create_player(session, row, team_id)
                        players_imported += 1
                    except Exception as e:
                        errors.append(f"Row {idx}: {str(e)}")
                
                if not errors:
                    return jsonify({
                        'message': f'Successfully imported {players_imported} players',
                        'imported_count': players_imported
                    }), 201
                else:
                    return jsonify({
                        'message': f'Imported {players_imported} players with {len(errors)} errors',
                        'imported_count': players_imported,
                        'errors': errors
                    }), 207  # 207 Multi-Status
        except Exception as e:
            print(f"Error importing players from CSV: {str(e)}")
            return db_error_response(e, "Failed to import players from CSV")
    
    # Handle JSON requests (single player creation)
    else:
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
