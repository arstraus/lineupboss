
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from shared.database import db_session, db_error_response, db_get_or_404
from services.team_service import TeamService
from shared.models import Team
from backend.utils import team_limit_check

teams = Blueprint('teams', __name__)

@teams.route('/', methods=['GET'])
@jwt_required()
def get_teams():
    """Get all teams for the current user.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Structured error handling
    """
    user_id = get_jwt_identity()
    
    # Print token details for debugging
    print(f"JWT Token received for user ID: {user_id} (type: {type(user_id).__name__})")
    auth_header = request.headers.get('Authorization', 'None')
    print(f"Authorization header: {auth_header}")
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
    
    try:
        # Using read_only mode since this is just a query operation
        with db_session(read_only=True) as session:
            # Log for debugging
            print(f"Getting teams for user ID: {user_id}")
            
            # Get all teams for the current user via service
            teams_list = TeamService.get_teams_by_user(session, user_id)
            print(f"Found {len(teams_list)} teams")
            
            # Serialize team objects
            result = [TeamService.serialize_team(team) for team in teams_list]
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error getting teams: {str(e)}")
        import traceback
        traceback.print_exc()
        # Use standardized error response
        return db_error_response(e, "Failed to retrieve teams")

@teams.route('/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team(team_id):
    """Get a specific team by ID.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - db_get_or_404 utility for safe fetching
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
            # Get the specific team via service
            team = TeamService.get_team(session, team_id, user_id)
            
            if not team:
                return jsonify({'error': 'Team not found or unauthorized'}), 404
            
            # Serialize team object
            result = TeamService.serialize_team(team)
            
            return jsonify(result), 200
    except Exception as e:
        print(f"Error getting team {team_id}: {str(e)}")
        # Use standardized error response
        return db_error_response(e, "Failed to retrieve team")

@teams.route('/', methods=['POST'])
@jwt_required()
@team_limit_check
def create_team():
    """Create a new team.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling
    - Clear transaction boundaries
    """
    user_id = get_jwt_identity()
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
    
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Team name is required'}), 400
    
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Create new team via service
            team = TeamService.create_team(session, data, user_id)
            
            if not team:
                return jsonify({'error': 'Failed to create team'}), 500
            
            return jsonify({
                'id': team.id,
                'name': team.name,
                'message': 'Team created successfully'
            }), 201
    except Exception as e:
        print(f"Error creating team: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to create team")

@teams.route('/<int:team_id>', methods=['PUT'])
@jwt_required()
def update_team(team_id):
    """Update an existing team.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with db_error_response
    - Two-phase operation: read then update
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
            # Check if team exists and belongs to user
            team = TeamService.get_team(session, team_id, user_id)
            
            if not team:
                return jsonify({'error': 'Team not found or unauthorized'}), 404
            
            # Update team via service
            updated_team = TeamService.update_team(session, team, data)
            
            return jsonify({
                'id': updated_team.id,
                'name': updated_team.name,
                'message': 'Team updated successfully'
            }), 200
    except Exception as e:
        print(f"Error updating team: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to update team")

@teams.route('/<int:team_id>', methods=['DELETE'])
@jwt_required()
def delete_team(team_id):
    """Delete an existing team.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with db_error_response
    - Two-phase operation: find then delete
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
            # Check if team exists and belongs to user
            team = TeamService.get_team(session, team_id, user_id)
            
            if not team:
                return jsonify({'error': 'Team not found or unauthorized'}), 404
            
            # Delete team via service
            TeamService.delete_team(session, team)
            
            return jsonify({
                'message': 'Team deleted successfully'
            }), 200
    except Exception as e:
        print(f"Error deleting team: {str(e)}")
        # Use standardized error response - no need to manually rollback
        return db_error_response(e, "Failed to delete team")
