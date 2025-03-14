
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from services.team_service import TeamService

teams = Blueprint('teams', __name__)

@teams.route('/', methods=['GET'])
@jwt_required()
def get_teams():
    user_id = get_jwt_identity()
    
    # Print token details for debugging
    print(f"JWT Token received for user ID: {user_id}")
    auth_header = request.headers.get('Authorization', 'None')
    print(f"Authorization header: {auth_header}")
    
    db = get_db()
    
    try:
        # Log for debugging
        print(f"Getting teams for user ID: {user_id}")
        
        # Get all teams for the current user via service
        teams_list = TeamService.get_teams_by_user(db, user_id)
        print(f"Found {len(teams_list)} teams")
        
        # Serialize team objects
        result = [TeamService.serialize_team(team) for team in teams_list]
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error getting teams: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to retrieve teams"}), 500
    finally:
        db.close()

@teams.route('/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team(team_id):
    user_id = get_jwt_identity()
    db = get_db()
    
    try:
        # Get the specific team via service
        team = TeamService.get_team(db, team_id, user_id)
        
        if not team:
            return jsonify({'error': 'Team not found or unauthorized'}), 404
        
        # Serialize team object
        result = TeamService.serialize_team(team)
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error getting team {team_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve team"}), 500
    finally:
        db.close()

@teams.route('/', methods=['POST'])
@jwt_required()
def create_team():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Team name is required'}), 400
    
    db = get_db()
    
    try:
        # Create new team via service
        team = TeamService.create_team(db, data, user_id)
        
        if not team:
            return jsonify({'error': 'Failed to create team'}), 500
        
        return jsonify({
            'id': team.id,
            'name': team.name,
            'message': 'Team created successfully'
        }), 201
    except Exception as e:
        db.rollback()
        print(f"Error creating team: {str(e)}")
        return jsonify({"error": "Failed to create team"}), 500
    finally:
        db.close()

@teams.route('/<int:team_id>', methods=['PUT'])
@jwt_required()
def update_team(team_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    db = next(get_db())
    
    # Check if team exists and belongs to user
    team = TeamService.get_team(db, team_id, user_id)
    
    if not team:
        return jsonify({'error': 'Team not found or unauthorized'}), 404
    
    # Update team via service
    updated_team = TeamService.update_team(db, team, data)
    
    return jsonify({
        'id': updated_team.id,
        'name': updated_team.name,
        'message': 'Team updated successfully'
    }), 200

@teams.route('/<int:team_id>', methods=['DELETE'])
@jwt_required()
def delete_team(team_id):
    user_id = get_jwt_identity()
    db = next(get_db())
    
    # Check if team exists and belongs to user
    team = TeamService.get_team(db, team_id, user_id)
    
    if not team:
        return jsonify({'error': 'Team not found or unauthorized'}), 404
    
    # Delete team via service
    TeamService.delete_team(db, team)
    
    return jsonify({
        'message': 'Team deleted successfully'
    }), 200
