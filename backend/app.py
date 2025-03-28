
from flask import Flask, jsonify, send_from_directory, Blueprint, request, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from dotenv import load_dotenv
import os
import importlib.util
import traceback

# Import API but handle missing dependencies gracefully
from database import init_db, get_db

# Import flask_jwt_extended at the module level
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

# Create a fallback docs blueprint in case the import fails
docs = Blueprint('docs', __name__)
swagger_ui_blueprint = Blueprint('swagger_ui', __name__)

# Import API with better error handling
try:
    from api import api
    # Try to import docs
    try:
        from api.docs import docs, swagger_ui_blueprint
    except ImportError as e:
        print(f"WARNING: Could not import api.docs: {e}")
        print(f"Error details: {str(e)}")
        # We'll use the fallback blueprint defined above
except ImportError as e:
    print(f"ERROR: Could not import api: {e}")
    print(f"Error details: {str(e)}")
    # Create a fallback API blueprint
    api = Blueprint('api', __name__, url_prefix='/api')

# Load environment variables
load_dotenv()

# Create Flask app
static_folder_path = '../frontend/build'
# Check if the path exists, for deployment environments
if not os.path.exists(static_folder_path):
    static_folder_path = 'frontend/build'
    if not os.path.exists(static_folder_path):
        print(f"WARNING: Frontend build directory not found: {static_folder_path}")
        # Default to a directory that's sure to exist to avoid errors
        static_folder_path = '.'

app = Flask(__name__, static_folder=static_folder_path, static_url_path='')

# Import datetime at the top level
from datetime import timedelta
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure app with secure defaults
jwt_secret = os.getenv('JWT_SECRET_KEY')
if not jwt_secret:
    import secrets
    jwt_secret = secrets.token_hex(32)  # Generate a secure random key if not provided
    print("WARNING: JWT_SECRET_KEY not found in environment. Using a temporary random key.")
    print("This is OK for development but not for production.")
    print("Set a permanent JWT_SECRET_KEY in your environment variables.")

app.config['JWT_SECRET_KEY'] = jwt_secret
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
# Import token settings from api.auth if available 
try:
    from api.auth import ACCESS_TOKEN_EXPIRES
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = ACCESS_TOKEN_EXPIRES  # Use consistent setting
except ImportError:
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=15)  # Default to 15 days
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Don't require CSRF tokens for API-only backends
app.config['PROPAGATE_EXCEPTIONS'] = True  # Propagate exceptions from JWT
app.config['JWT_ERROR_MESSAGE_KEY'] = 'error'  # Use 'error' as the key for error messages
print(f"JWT configuration complete. Secret key is {'randomly generated' if not os.getenv('JWT_SECRET_KEY') else 'from environment'}.")

# Database configuration - ALWAYS use environment variables for credentials!
# In production, DATABASE_URL should be set in Heroku config vars
# NEVER hardcode database credentials in the source code
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///lineup.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Handle both postgres:// and postgresql:// formats for any PostgreSQL provider (Heroku, Neon, etc.)
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
    print(f"Updated SQLALCHEMY_DATABASE_URI to use postgresql:// prefix")
    
# Also fix the DATABASE_URL environment variable to ensure consistent connections
if os.environ.get('DATABASE_URL', '').startswith('postgres://'):
    os.environ['DATABASE_URL'] = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
    print(f"Updated DATABASE_URL to use postgresql:// prefix")

# Log database connection for debugging (without credentials)
db_url = app.config['SQLALCHEMY_DATABASE_URI']
if 'postgresql' in db_url:
    # Extract just the host part for logging
    parts = db_url.split('@')
    if len(parts) > 1:
        host_part = parts[1].split('/')[0]
        print(f"Connecting to PostgreSQL database at: {host_part}")

# Initialize extensions
jwt = JWTManager(app)

# JWT error handlers for better debugging
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print(f"Expired token received: {jwt_header}")
    print(f"Token payload: {jwt_payload}")
    
    # Get request details for better debugging
    request_info = {
        "path": request.path,
        "method": request.method,
        "endpoint": request.endpoint,
        "has_auth_header": "Authorization" in request.headers,
    }
    print(f"Request info for expired token: {request_info}")
    
    # Include more details in the response
    return jsonify({
        "error": "Token has expired",
        "details": "Please log in again to get a new token"
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    print(f"Invalid token error: {error_string}")
    
    # Get request details for better debugging
    request_info = {
        "path": request.path,
        "method": request.method,
        "endpoint": request.endpoint,
        "has_auth_header": "Authorization" in request.headers,
    }
    print(f"Request info for invalid token: {request_info}")
    
    # Add more debug info if authorization header exists
    if "Authorization" in request.headers:
        auth_header = request.headers["Authorization"]
        print(f"Authorization header format: {auth_header[:10]}...")
        
        # Check token format
        parts = auth_header.split()
        if len(parts) != 2:
            print(f"Invalid Authorization header format: expected 2 parts, got {len(parts)}")
        elif parts[0] != "Bearer":
            print(f"Invalid Authorization scheme: expected 'Bearer', got '{parts[0]}'")
    
    return jsonify({
        "error": f"Invalid token: {error_string}",
        "details": "The token format is invalid or the signature is incorrect"
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    print(f"Missing token error: {error_string}")
    
    # Get request details for better debugging
    request_info = {
        "path": request.path,
        "method": request.method,
        "endpoint": request.endpoint,
        "has_auth_header": "Authorization" in request.headers,
    }
    print(f"Request info for missing token: {request_info}")
    
    # Check all headers for debugging
    print("All headers:")
    for key, value in request.headers.items():
        # Don't print the full token value if it exists
        if key.lower() == 'authorization':
            print(f"  {key}: {value[:15]}..." if value else f"  {key}: None")
        else:
            print(f"  {key}: {value}")
    
    return jsonify({
        "error": f"Missing token: {error_string}",
        "details": "No JWT token was found in the request headers"
    }), 401

@jwt.token_verification_failed_loader
def token_verification_failed_callback():
    print("Token verification failed")
    
    # Get request details for better debugging
    request_info = {
        "path": request.path,
        "method": request.method,
        "endpoint": request.endpoint,
        "has_auth_header": "Authorization" in request.headers,
    }
    print(f"Request info for verification failed: {request_info}")
    
    return jsonify({
        "error": "Token verification failed",
        "details": "The token could not be verified. It may be corrupted or tampered with."
    }), 401

# Configure CORS to allow requests from the frontend with proper headers
CORS(app, 
     resources={r"/api/*": {"origins": [
         "https://lineupboss.app",
         "https://www.lineupboss.app", 
         "https://lineupboss-7fbdffdfe200.herokuapp.com",
         "http://localhost:3000",  # For local development
         "http://127.0.0.1:3000"   # Also for local development
     ]}}, 
     supports_credentials=True,
     allow_headers=[
         "Content-Type", 
         "Authorization", 
         "Access-Control-Allow-Credentials",
         "X-Authorization",       # Our custom authorization header
         "X-Requested-With",      # For XHR detection
         "X-Source",              # For debugging request sources
         "X-Token-Length",        # For debugging token issues
         "Cache-Control"          # For cache control
     ],
     expose_headers=[
         "Authorization", 
         "Content-Type",
         "X-Authorization"        # Expose custom auth header in responses
     ],
     max_age=86400)

# Register API blueprint
app.register_blueprint(api)

# Register API documentation blueprints
app.register_blueprint(docs, url_prefix='/api')
app.register_blueprint(swagger_ui_blueprint)

# Add direct routes for key operations to bypass proxy recursion issues

# Auth routes
@app.route('/api/auth/login/', methods=['POST'])
def direct_auth_login():
    """Direct route for login to bypass proxy issues"""
    print("Direct login route activated")
    from api.auth import login
    return login()

# Team routes
@app.route('/api/teams/', methods=['POST'])
def direct_team_create():
    """Direct route for team creation to bypass proxy issues"""
    print("Direct team create route activated")
    from api.teams import create_team
    return create_team()

@app.route('/api/teams/<int:team_id>', methods=['DELETE'])
def direct_team_delete(team_id):
    """Direct route for team deletion that doesn't rely on decorators"""
    print(f"Direct team delete route activated for team {team_id}")
    
    try:
        # Manually verify JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from flask import g
        from shared.database import db_session, db_error_response
        from services.team_service import TeamService
        
        # Verify JWT token
        print(f"Verifying JWT token for team deletion: {team_id}")
        verify_jwt_in_request()
        
        # Get user ID from token
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        g.user_id = user_id
        
        print(f"Processing delete for team {team_id}, user {user_id}")
        
        # Use the same logic as the delete_team function but without relying on decorators
        with db_session(commit=True) as session:
            # Check if team exists and belongs to user
            team = TeamService.get_team(session, team_id, user_id)
            
            if not team:
                print(f"Team {team_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Team not found or unauthorized'}), 404
            
            print(f"Team {team_id} found, proceeding with deletion")
            
            # Delete team via service
            TeamService.delete_team(session, team)
            
            print(f"Team {team_id} deleted successfully")
            
            return jsonify({
                'message': 'Team deleted successfully'
            }), 200
            
    except Exception as e:
        print(f"Error in direct team delete: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to delete team: {str(e)}'}), 500
        
# Player routes
@app.route('/api/teams/<int:team_id>/players', methods=['POST'])
def direct_player_create(team_id):
    """Direct route for player creation that doesn't rely on decorators"""
    print(f"Direct player create route activated for team {team_id}")
    
    try:
        # Manually verify JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from flask import g
        from api.players import create_player
        
        # Verify JWT token
        print(f"Verifying JWT token for player creation: {team_id}")
        verify_jwt_in_request()
        
        # Get user ID from token
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        g.user_id = user_id
        
        print(f"Processing player creation for team {team_id}, user {user_id}")
        
        # Call the player creation function
        return create_player(team_id)
    except Exception as e:
        print(f"Error in direct player create: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to create player: {str(e)}'}), 500

@app.route('/api/players/<int:player_id>', methods=['DELETE'])
def direct_player_delete(player_id):
    """Direct route for player deletion that doesn't rely on decorators"""
    print(f"Direct player delete route activated for player {player_id}")
    
    try:
        # Manually verify JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from flask import g
        from shared.database import db_session, db_error_response
        from services.player_service import PlayerService
        
        # Verify JWT token
        print(f"Verifying JWT token for player deletion: {player_id}")
        verify_jwt_in_request()
        
        # Get user ID from token
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        g.user_id = user_id
        
        print(f"Processing delete for player {player_id}, user {user_id}")
        
        # Use the same logic as the delete_player function but without relying on decorators
        with db_session(commit=True) as session:
            # Verify player belongs to user's team
            player = PlayerService.get_player(session, player_id, user_id)
            
            if not player:
                print(f"Player {player_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Player not found or unauthorized'}), 404
            
            print(f"Player {player_id} found, proceeding with deletion")
            
            # Delete player via service
            PlayerService.delete_player(session, player)
            
            print(f"Player {player_id} deleted successfully")
            
            return jsonify({
                'message': 'Player deleted successfully'
            }), 200
            
    except Exception as e:
        print(f"Error in direct player delete: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to delete player: {str(e)}'}), 500

# Game routes
@app.route('/api/teams/<int:team_id>/games', methods=['POST'])
def direct_game_create(team_id):
    """Direct route for game creation that doesn't rely on decorators"""
    print(f"Direct game create route activated for team {team_id}")
    
    try:
        # Manually verify JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from flask import g
        from api.games import create_game
        
        # Verify JWT token
        print(f"Verifying JWT token for game creation: {team_id}")
        verify_jwt_in_request()
        
        # Get user ID from token
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        g.user_id = user_id
        
        print(f"Processing game creation for team {team_id}, user {user_id}")
        
        # Call the game creation function
        return create_game(team_id)
    except Exception as e:
        print(f"Error in direct game create: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to create game: {str(e)}'}), 500

@app.route('/api/games/<int:game_id>', methods=['DELETE'])
def direct_game_delete(game_id):
    """Direct route for game deletion that doesn't rely on decorators"""
    print(f"Direct game delete route activated for game {game_id}")
    
    try:
        # Manually verify JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from flask import g
        from shared.database import db_session, db_error_response
        from services.game_service import GameService
        
        # Verify JWT token
        print(f"Verifying JWT token for game deletion: {game_id}")
        verify_jwt_in_request()
        
        # Get user ID from token
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        g.user_id = user_id
        
        print(f"Processing delete for game {game_id}, user {user_id}")
        
        # Use the same logic as the delete_game function but without relying on decorators
        with db_session(commit=True) as session:
            # Verify game belongs to user's team
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                print(f"Game {game_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            print(f"Game {game_id} found, proceeding with deletion")
            
            # Delete game via service
            GameService.delete_game(session, game)
            
            print(f"Game {game_id} deleted successfully")
            
            return jsonify({
                'message': 'Game deleted successfully'
            }), 200
            
    except Exception as e:
        print(f"Error in direct game delete: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to delete game: {str(e)}'}), 500

# Game batting order route
@app.route('/api/games/<int:game_id>/batting-order', methods=['POST'])
def direct_save_batting_order(game_id):
    """Direct route for saving batting order that doesn't rely on decorators"""
    print(f"Direct batting order saving route activated for game {game_id}")
    
    try:
        # Manually verify JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from flask import g, request
        from shared.database import db_session
        from services.game_service import GameService
        
        # Verify JWT token
        print(f"Verifying JWT token for batting order save: {game_id}")
        verify_jwt_in_request()
        
        # Get user ID from token
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        g.user_id = user_id
        
        print(f"Processing batting order save for game {game_id}, user {user_id}")
        
        # Parse the request data
        data = request.get_json()
        order_data = data.get('order_data', [])
        
        with db_session(commit=True) as session:
            # Verify game belongs to user's team
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                print(f"Game {game_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Save the batting order
            GameService.save_batting_order(session, game_id, order_data)
            
            return jsonify({
                'message': 'Batting order saved successfully',
                'game_id': game_id
            }), 200
            
    except Exception as e:
        print(f"Error in direct batting order save: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to save batting order: {str(e)}'}), 500

# Game fielding rotation route
@app.route('/api/games/<int:game_id>/fielding-rotations/<int:inning>', methods=['POST'])
def direct_save_fielding_rotation(game_id, inning):
    """Direct route for saving fielding rotation that doesn't rely on decorators"""
    print(f"Direct fielding rotation saving route activated for game {game_id}, inning {inning}")
    
    try:
        # Manually verify JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from flask import g, request
        from shared.database import db_session
        from services.game_service import GameService
        
        # Verify JWT token
        print(f"Verifying JWT token for fielding rotation save: {game_id}")
        verify_jwt_in_request()
        
        # Get user ID from token
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        g.user_id = user_id
        
        print(f"Processing fielding rotation save for game {game_id}, inning {inning}, user {user_id}")
        
        # Parse the request data
        data = request.get_json()
        positions = data.get('positions', {})
        
        with db_session(commit=True) as session:
            # Verify game belongs to user's team
            game = GameService.get_game(session, game_id, user_id)
            
            if not game:
                print(f"Game {game_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Save the fielding rotation
            GameService.save_fielding_rotation(session, game_id, inning, positions)
            
            return jsonify({
                'message': 'Fielding rotation saved successfully',
                'game_id': game_id,
                'inning': inning
            }), 200
            
    except Exception as e:
        print(f"Error in direct fielding rotation save: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to save fielding rotation: {str(e)}'}), 500

# Player availability route
@app.route('/api/games/<int:game_id>/player-availability/<int:player_id>', methods=['POST'])
def direct_save_player_availability(game_id, player_id):
    """Direct route for saving player availability that doesn't rely on decorators"""
    print(f"Direct player availability saving route activated for game {game_id}, player {player_id}")
    
    try:
        # Manually verify JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from flask import g, request
        from shared.database import db_session
        from services.game_service import GameService
        from services.player_service import PlayerService
        
        # Verify JWT token
        print(f"Verifying JWT token for player availability save: {game_id}")
        verify_jwt_in_request()
        
        # Get user ID from token
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        g.user_id = user_id
        
        print(f"Processing player availability save for game {game_id}, player {player_id}, user {user_id}")
        
        # Parse the request data
        data = request.get_json()
        
        with db_session(commit=True) as session:
            # Verify game belongs to user's team
            game = GameService.get_game(session, game_id, user_id)
            if not game:
                print(f"Game {game_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Verify player belongs to user's team
            player = PlayerService.get_player(session, player_id, user_id)
            if not player:
                print(f"Player {player_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Player not found or unauthorized'}), 404
            
            # Save the player availability
            GameService.save_player_availability(session, game_id, player_id, data)
            
            return jsonify({
                'message': 'Player availability saved successfully',
                'game_id': game_id,
                'player_id': player_id
            }), 200
            
    except Exception as e:
        print(f"Error in direct player availability save: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to save player availability: {str(e)}'}), 500
        
# Batch player availability route
@app.route('/api/games/<int:game_id>/player-availability/batch', methods=['POST'])
def direct_batch_save_player_availability(game_id):
    """Direct route for batch saving player availability"""
    print(f"Direct batch player availability saving route activated for game {game_id}")
    
    try:
        # Manually verify JWT token
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from flask import g, request
        from shared.database import db_session
        from services.game_service import GameService
        from services.player_service import PlayerService
        
        # Verify JWT token
        print(f"Verifying JWT token for batch player availability save: {game_id}")
        verify_jwt_in_request()
        
        # Get user ID from token
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        g.user_id = user_id
        
        print(f"Processing batch player availability save for game {game_id}, user {user_id}")
        
        # Parse the request data
        data = request.get_json()
        
        # Validate request data
        if not data or not isinstance(data, list) or len(data) == 0:
            print(f"Invalid batch data format: {type(data)}")
            return jsonify({'error': 'A list of player availability records is required'}), 400
        
        # Validate each record in the batch
        for idx, record in enumerate(data):
            if not isinstance(record, dict) or 'player_id' not in record or not isinstance(record.get('available'), bool):
                print(f"Invalid record at index {idx}: {record}")
                return jsonify({'error': f'Invalid record at index {idx}: Must contain player_id and availability status'}), 400
        
        with db_session(commit=True) as session:
            # Verify game belongs to user's team
            game = GameService.get_game(session, game_id, user_id)
            if not game:
                print(f"Game {game_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            # Verify all players belong to user's team
            player_ids = [record['player_id'] for record in data]
            for player_id in player_ids:
                player = PlayerService.get_player(session, player_id, user_id)
                if not player:
                    print(f"Player {player_id} not found or not owned by user {user_id}")
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
        print(f"Error in direct batch player availability save: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to save player availability: {str(e)}'}), 500

# AI Fielding Rotation Route
# Import this at the module level to avoid circular imports
from services.ai_service import AIService

# IMPORTANT: AI Fielding Rotation Authentication Architecture
# We implement dual authentication endpoints for AI fielding rotation to ensure robustness:
# 1. The manual_generate_ai_fielding_rotation endpoint extracts and validates JWT tokens manually
#    to handle cases where the Authorization header might be lost in redirects or proxy handlers.
# 2. The direct_generate_ai_fielding_rotation endpoint uses the standard @jwt_required() decorator
#    which is more concise but depends on proper header propagation in all environments.
# 
# This dual-endpoint approach provides a fallback mechanism for frontend authentication, where
# the client can try both endpoints if one fails. The frontend fetches from the direct endpoint first,
# and if that fails with an authentication error, it falls back to the manual endpoint.
#
# AI Fielding Rotation Route - With manual auth for special case
@app.route('/api/games/<int:game_id>/ai-fielding-rotation-manual', methods=['POST'])
def manual_generate_ai_fielding_rotation(game_id):
    """Manual JWT validation route for generating AI fielding rotation as a fallback"""
    print(f"MANUAL AI fielding rotation generation route activated for game {game_id}")
    
    # Import required modules at the top
    from shared.database import db_session
    from flask_jwt_extended import decode_token
    from flask import g
    
    # Debug the headers with more detail
    print("REQUEST HEADERS - MANUAL AI ROTATION:")
    for key, value in request.headers.items():
        # Don't print the full token value
        if key.lower() == 'authorization':
            if value:
                print(f"  {key}: {value[:15]}... [PRESENT]")
                # Also log the token type to see if it matches what we expect
                token_parts = value.split()
                if len(token_parts) == 2:
                    print(f"  Token type: {token_parts[0]}")
                else:
                    print(f"  Token format is not as expected. Parts: {len(token_parts)}")
            else:
                print(f"  {key}: [EMPTY]")
        else:
            print(f"  {key}: {value}")
    
    try:
        # Extract and validate the token manually
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            # Try alternate headers that might have been set
            auth_header = request.headers.get('X-Authorization')
            if not auth_header:
                print("No Authorization header found in manual validation")
                return jsonify({'error': 'Authorization header is missing'}), 401
        
        # Split the header to get the token
        auth_parts = auth_header.split()
        if len(auth_parts) != 2 or auth_parts[0] != 'Bearer':
            print(f"Invalid Authorization header format: {auth_header[:15]}...")
            return jsonify({'error': 'Invalid Authorization header format. Expected: Bearer <token>'}), 401
        
        token = auth_parts[1]
        
        # Manually decode and validate the token
        try:
            decoded_token = decode_token(token)
            print(f"Token successfully decoded: {decoded_token.keys()}")
            user_id = decoded_token['sub']  # sub is where identity is stored
            
            # Convert user_id to integer if needed
            if isinstance(user_id, str):
                user_id = int(user_id)
            
            # Store in Flask g for compatibility
            g.user_id = user_id
            
            print(f"Manually validated user_id: {user_id}")
        except Exception as token_err:
            print(f"Error decoding token: {token_err}")
            return jsonify({'error': f'Invalid token: {str(token_err)}'}), 401
        
        # Now proceed with the rest of the function, same as the decorated version
        data = request.get_json()
        print(f"Request JSON data keys: {data.keys() if data else 'None'}")
        
        if not data or not isinstance(data.get('players'), list) or len(data.get('players', [])) == 0:
            print("Error: Missing required player data")
            return jsonify({'error': 'Player data is required for AI rotation generation'}), 400
        
        # Import needed modules for feature check
        from shared.models import User
        from shared.subscription_tiers import has_feature
        
        # Special check for feature requirement
        with db_session(read_only=True) as session:
            # Check if user has the AI feature
            user = session.query(User).filter(User.id == user_id).first()
            if user and user.role != 'admin':
                if not has_feature(user.subscription_tier, 'ai_lineup_generation'):
                    print(f"User {user_id} doesn't have the AI feature")
                    return jsonify({
                        'error': 'Subscription required',
                        'message': 'This feature requires a Pro subscription',
                        'current_tier': user.subscription_tier,
                        'required_feature': 'ai_lineup_generation',
                        'upgrade_url': '/account/billing'
                    }), 403
        
        # Continue with game validation and AI generation
        with db_session(read_only=True) as session:
            from services.game_service import GameService
            
            print(f"Verifying game {game_id} belongs to user {user_id}")
            game = GameService.get_game(session, game_id, user_id)
            if not game:
                print(f"Error: Game {game_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            print(f"Game {game_id} verification successful for user {user_id}")
            
            # Get required parameters from request data
            players = data['players']
            innings = data.get('innings', game.innings) or 6  # Default to game innings or fallback to 6
            required_positions = data.get('required_positions', [])
            infield_positions = data.get('infield_positions', [])
            outfield_positions = data.get('outfield_positions', [])
            
            # Get customization options with defaults
            options = data.get('options', {})
            no_consecutive_innings = options.get('noConsecutiveInnings', True)
            balance_playing_time = options.get('balancePlayingTime', True)
            allow_same_position = options.get('allowSamePositionMultipleTimes', False)
            strict_position_balance = options.get('strictPositionBalance', True)
            temperature = options.get('temperature', 0.7)  # Add temperature parameter with default
            
            print(f"AI rotation parameters: innings={innings}, players={len(players)}, temp={temperature}")
            
            try:
                print("Calling AIService.generate_fielding_rotation...")
                # Use the AI service to generate fielding rotation with timeout handling
                rotation_result = AIService.generate_fielding_rotation(
                    game_id, 
                    players, 
                    innings,
                    required_positions,
                    infield_positions,
                    outfield_positions,
                    no_consecutive_innings,
                    balance_playing_time,
                    allow_same_position,
                    strict_position_balance,
                    temperature  # Pass temperature to the AI service
                )
                
                print("AI rotation generated successfully")
                return jsonify(rotation_result), 200
            except ValueError as ve:
                if "timeout" in str(ve).lower():
                    # If timeout occurs, return an informative message with HTTP 202 Accepted
                    print(f"AI rotation generation timed out: {str(ve)}")
                    # This indicates the request was valid but could not be completed in time
                    return jsonify({
                        "message": "The AI fielding rotation could not be generated in time. Please try again later or create a manual rotation.",
                        "error": str(ve),
                        "success": False
                    }), 202
                else:
                    # For other ValueErrors, pass through to the general error handler
                    print(f"ValueError in AI rotation generation: {str(ve)}")
                    raise ve
    except Exception as e:
        print(f"Error in manual AI fielding rotation generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500

# AI Fielding Rotation Route - Using jwt_required decorator for proper auth
@app.route('/api/games/<int:game_id>/ai-fielding-rotation', methods=['POST'])
@app.route('/api/games/<int:game_id>/ai-fielding-rotation/', methods=['POST'])
@jwt_required()
def direct_generate_ai_fielding_rotation(game_id):
    """Direct route for generating AI fielding rotation using JWT decorator"""
    print(f"Direct AI fielding rotation generation route activated for game {game_id}")
    
    # Import required modules at the top
    from shared.database import db_session, db_error_response
    from shared.models import User
    from shared.subscription_tiers import has_feature
    
    # Debug the headers with more detail
    print("REQUEST HEADERS - AI FIELDING ROTATION:")
    for key, value in request.headers.items():
        # Don't print the full token value
        if key.lower() == 'authorization':
            if value:
                print(f"  {key}: {value[:15]}... [PRESENT]")
                # Also log the token type to see if it matches what we expect
                token_parts = value.split()
                if len(token_parts) == 2:
                    print(f"  Token type: {token_parts[0]}")
                else:
                    print(f"  Token format is not as expected. Parts: {len(token_parts)}")
            else:
                print(f"  {key}: [EMPTY]")
        else:
            print(f"  {key}: {value}")
    
    # Debug JWT state in current request
    from flask_jwt_extended import verify_jwt_in_request, get_jwt
    try:
        # Try to verify and get JWT manually
        print("Manually verifying JWT token...")
        verify_jwt_in_request()
        print("JWT verification successful")
        
        # Get the JWT payload
        try:
            jwt_data = get_jwt()
            print(f"JWT payload retrieved. Keys: {jwt_data.keys()}")
            if 'exp' in jwt_data:
                import datetime
                exp_time = datetime.datetime.fromtimestamp(jwt_data['exp'])
                print(f"Token expires at: {exp_time}")
            if 'sub' in jwt_data:
                print(f"Token subject (sub): {jwt_data['sub']}")
        except Exception as jwt_err:
            print(f"Error getting JWT payload: {jwt_err}")
    except Exception as verify_err:
        print(f"JWT verification failed: {verify_err}")
    
    try:
        # Get user ID from token
        user_id = get_jwt_identity()
        print(f"JWT identity retrieved: {user_id} (type: {type(user_id)})")
        
        if isinstance(user_id, str):
            user_id = int(user_id)
            print(f"Converted user_id to integer: {user_id}")
        
        print(f"Processing AI fielding rotation generation for game {game_id}, user {user_id}")
        
        # Store user_id in Flask g object for compatibility with other code
        from flask import g
        g.user_id = user_id
        print(f"Stored user_id {user_id} in Flask g object")
        
        # Grab the request data
        data = request.get_json()
        print(f"Request JSON data keys: {data.keys() if data else 'None'}")
        
        # Check for required data
        if not data or not isinstance(data.get('players'), list) or len(data.get('players', [])) == 0:
            print("Error: Missing required player data")
            return jsonify({'error': 'Player data is required for AI rotation generation'}), 400
        
        # Special check for feature requirement
        with db_session(read_only=True) as session:
            # Check if user has the AI feature
            user = session.query(User).filter(User.id == user_id).first()
            if user and user.role != 'admin':
                if not has_feature(user.subscription_tier, 'ai_lineup_generation'):
                    print(f"User {user_id} doesn't have the AI feature")
                    return jsonify({
                        'error': 'Subscription required',
                        'message': 'This feature requires a Pro subscription',
                        'current_tier': user.subscription_tier,
                        'required_feature': 'ai_lineup_generation',
                        'upgrade_url': '/account/billing'
                    }), 403
        
        # Using read_only mode since this is just a verification and AI computation
        with db_session(read_only=True) as session:
            # Verify game belongs to user's team via service
            from services.game_service import GameService
            
            print(f"Verifying game {game_id} belongs to user {user_id}")
            game = GameService.get_game(session, game_id, user_id)
            if not game:
                print(f"Error: Game {game_id} not found or not owned by user {user_id}")
                return jsonify({'error': 'Game not found or unauthorized'}), 404
            
            print(f"Game {game_id} verification successful for user {user_id}")
            
            # Get required parameters from request data
            players = data['players']
            innings = data.get('innings', game.innings) or 6  # Default to game innings or fallback to 6
            required_positions = data.get('required_positions', [])
            infield_positions = data.get('infield_positions', [])
            outfield_positions = data.get('outfield_positions', [])
            
            # Get customization options with defaults
            options = data.get('options', {})
            no_consecutive_innings = options.get('noConsecutiveInnings', True)
            balance_playing_time = options.get('balancePlayingTime', True)
            allow_same_position = options.get('allowSamePositionMultipleTimes', False)
            strict_position_balance = options.get('strictPositionBalance', True)
            temperature = options.get('temperature', 0.7)  # Add temperature parameter with default
            
            print(f"AI rotation parameters: innings={innings}, players={len(players)}, temp={temperature}")
            
            try:
                print("Calling AIService.generate_fielding_rotation...")
                # Use the AI service to generate fielding rotation with timeout handling
                rotation_result = AIService.generate_fielding_rotation(
                    game_id, 
                    players, 
                    innings,
                    required_positions,
                    infield_positions,
                    outfield_positions,
                    no_consecutive_innings,
                    balance_playing_time,
                    allow_same_position,
                    strict_position_balance,
                    temperature  # Pass temperature to the AI service
                )
                
                print("AI rotation generated successfully")
                return jsonify(rotation_result), 200
            except ValueError as ve:
                if "timeout" in str(ve).lower():
                    # If timeout occurs, return an informative message with HTTP 202 Accepted
                    print(f"AI rotation generation timed out: {str(ve)}")
                    # This indicates the request was valid but could not be completed in time
                    return jsonify({
                        "message": "The AI fielding rotation could not be generated in time. Please try again later or create a manual rotation.",
                        "error": str(ve),
                        "success": False
                    }), 202
                else:
                    # For other ValueErrors, pass through to the general error handler
                    print(f"ValueError in AI rotation generation: {str(ve)}")
                    raise ve
            
    except Exception as e:
        print(f"Error in direct AI fielding rotation generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500

# Directly register analytics blueprint with the app
try:
    from api.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    logger.info("Successfully registered analytics_bp directly with Flask app")
except ImportError as e:
    logger.error(f"Could not import analytics module for direct registration: {e}")
    logger.error(traceback.format_exc())
except Exception as e:
    logger.error(f"Error registering analytics blueprint directly: {e}")
    logger.error(traceback.format_exc())

# Direct analytics endpoints as fallback in case blueprint registration fails
@app.route('/api/analytics/status', methods=['GET'])
def analytics_direct_status():
    """Fallback endpoint to verify analytics routing"""
    logger.info("Direct analytics status endpoint called")
    return jsonify({"status": "ok", "message": "Direct analytics endpoint working", "method": "app.route"}), 200

# Direct team analytics endpoints - Legacy patterns
@app.route('/api/analytics/teams/<int:team_id>/batting-analytics', methods=['GET'])
@jwt_required()
def direct_team_batting_analytics(team_id):
    """Direct batting analytics endpoint if blueprint fails (legacy pattern)"""
    logger.info(f"Direct batting analytics endpoint called for team {team_id}")
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_player_batting_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error in direct batting analytics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get batting analytics: {str(e)}"}), 500

@app.route('/api/analytics/teams/<int:team_id>/fielding-analytics', methods=['GET'])
@jwt_required()
def direct_team_fielding_analytics(team_id):
    """Direct fielding analytics endpoint if blueprint fails (legacy pattern)"""
    logger.info(f"Direct fielding analytics endpoint called for team {team_id}")
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_player_fielding_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error in direct fielding analytics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get fielding analytics: {str(e)}"}), 500

@app.route('/api/analytics/teams/<int:team_id>/analytics', methods=['GET'])
@jwt_required()
def direct_team_analytics(team_id):
    """Direct team analytics endpoint if blueprint fails (legacy pattern)"""
    logger.info(f"Direct team analytics endpoint called for team {team_id}")
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_team_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error in direct team analytics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get team analytics: {str(e)}"}), 500
        
# Direct team analytics endpoints - RESTful patterns
@app.route('/api/analytics/teams/<int:team_id>', methods=['GET'])
@jwt_required()
def direct_team_analytics_restful(team_id):
    """Direct RESTful team analytics endpoint if blueprint fails"""
    logger.info(f"Direct RESTful team analytics endpoint called for team {team_id}")
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_team_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error in direct RESTful team analytics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get team analytics: {str(e)}"}), 500

@app.route('/api/analytics/teams/<int:team_id>/players/batting', methods=['GET'])
@jwt_required()
def direct_player_batting_analytics(team_id):
    """Direct RESTful player batting analytics endpoint if blueprint fails"""
    logger.info(f"Direct RESTful player batting analytics endpoint called for team {team_id}")
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_player_batting_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error in direct RESTful player batting analytics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get player batting analytics: {str(e)}"}), 500

@app.route('/api/analytics/teams/<int:team_id>/players/fielding', methods=['GET'])
@jwt_required()
def direct_player_fielding_analytics(team_id):
    """Direct RESTful player fielding analytics endpoint if blueprint fails"""
    logger.info(f"Direct RESTful player fielding analytics endpoint called for team {team_id}")
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_player_fielding_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error in direct RESTful player fielding analytics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get player fielding analytics: {str(e)}"}), 500

# Add enhanced diagnostic route directly to app
@app.route('/api/debug/analytics-status', methods=['GET'])
def analytics_status_debug():
    """Enhanced diagnostic endpoint to verify routing is working"""
    logger.info("Debug analytics status endpoint called")
    
    # Collect registered blueprints for debugging
    registered_blueprints = []
    analytics_registered = False
    
    for blueprint_name, blueprint in app.blueprints.items():
        registered_blueprints.append({
            'name': blueprint_name,
            'url_prefix': blueprint.url_prefix
        })
        if 'analytics' in blueprint_name:
            analytics_registered = True
    
    # Check if the analytics module and service are available
    has_analytics_service = False
    has_analytics_bp = False
    has_analytics_module = False
    analytics_routes = []
    
    try:
        from services.analytics_service import AnalyticsService
        has_analytics_service = True
    except ImportError as e:
        logger.error(f"Could not import AnalyticsService: {e}")
    
    try:
        from api.analytics import analytics_bp, ANALYTICS_MODULE_LOADED
        has_analytics_bp = True
        has_analytics_module = ANALYTICS_MODULE_LOADED
        
        # Note that we have the analytics blueprint
        analytics_routes.append("analytics_bp is available")
        
        # Try to get routes if possible
        try:
            if hasattr(analytics_bp, 'deferred_functions'):
                for rule in analytics_bp.deferred_functions:
                    if hasattr(rule, '__name__'):
                        analytics_routes.append(rule.__name__)
        except Exception as e:
            analytics_routes.append(f"Error getting routes: {str(e)}")
    except ImportError as e:
        logger.error(f"Could not import analytics_bp: {e}")
    except Exception as e:
        logger.error(f"Error checking analytics module: {e}")
    
    # Check for RESTful routes specifically
    has_restful_team = False
    has_restful_batting = False
    has_restful_fielding = False
    
    # Collect all API routes
    all_routes = []
    api_analytics_routes = []
    
    for rule in app.url_map.iter_rules():
        rule_str = str(rule)
        all_routes.append(rule_str)
        
        if '/api/analytics' in rule_str:
            api_analytics_routes.append(rule_str)
            
            # Check for RESTful endpoints
            if '/api/analytics/teams/<' in rule_str and rule_str.endswith('>'):
                has_restful_team = True
            elif '/api/analytics/teams/<' in rule_str and '/players/batting' in rule_str:
                has_restful_batting = True
            elif '/api/analytics/teams/<' in rule_str and '/players/fielding' in rule_str:
                has_restful_fielding = True
    
    # Return comprehensive diagnostic information
    return jsonify({
        'status': 'ok',
        'message': 'API diagnostics endpoint',
        'registered_blueprints': registered_blueprints,
        'analytics_registered': analytics_registered,
        'has_analytics_service': has_analytics_service,
        'has_analytics_bp': has_analytics_bp,
        'has_analytics_module': has_analytics_module,
        'analytics_routes': analytics_routes,
        'api_analytics_routes': api_analytics_routes,
        'restful_endpoints': {
            'team_analytics': has_restful_team,
            'batting_analytics': has_restful_batting,
            'fielding_analytics': has_restful_fielding
        },
        'app_version': '1.1.0',  # Increment for tracking deployment
        'environment': os.environ.get('FLASK_ENV', 'undefined'),
        'registered_endpoint_count': len(all_routes),
        'registered_analytics_count': len(api_analytics_routes)
    }), 200
    
# Add data diagnostic route for analytics data
@app.route('/api/debug/analytics-data/<int:team_id>', methods=['GET'])
@jwt_required()
def analytics_data_debug(team_id):
    """Diagnostic endpoint to verify analytics data"""
    logger.info(f"Debug analytics data endpoint called for team {team_id}")
    
    results = {
        'status': 'ok',
        'team_id': team_id,
        'data_checks': {}
    }
    
    try:
        with get_db(read_only=True) as session:
            # Check basic data availability
            from shared.models import Game, BattingOrder, FieldingRotation, Player
            
            # Count players
            player_count = session.query(Player).filter_by(team_id=team_id).count()
            results['data_checks']['player_count'] = player_count
            
            # Count games
            game_count = session.query(Game).filter_by(team_id=team_id).count()
            results['data_checks']['game_count'] = game_count
            
            # If games exist, get IDs for further checking
            if game_count > 0:
                game_ids = [g.id for g in session.query(Game.id).filter_by(team_id=team_id).all()]
                results['data_checks']['game_ids'] = game_ids
                
                # Check for batting orders
                batting_orders = session.query(BattingOrder).filter(
                    BattingOrder.game_id.in_(game_ids)
                ).count()
                results['data_checks']['batting_order_count'] = batting_orders
                
                # Check for fielding rotations
                fielding_rotations = session.query(FieldingRotation).filter(
                    FieldingRotation.game_id.in_(game_ids)
                ).count()
                results['data_checks']['fielding_rotation_count'] = fielding_rotations
                
                # Check games with dates
                games_with_dates = session.query(Game).filter(
                    Game.team_id == team_id,
                    Game.game_date != None
                ).count()
                results['data_checks']['games_with_dates'] = games_with_dates
                
                # Run the analytics methods
                from services.analytics_service import AnalyticsService
                team_analytics = AnalyticsService.get_team_analytics(team_id)
                results['data_checks']['team_analytics'] = {
                    'total_games': team_analytics.get('total_games', 0),
                    'has_data': team_analytics.get('has_data', False),
                    'month_count': len(team_analytics.get('games_by_month', {})),
                    'day_counts': team_analytics.get('games_by_day', {})
                }
            else:
                results['data_checks']['note'] = "No games found for team"
    except Exception as e:
        logger.error(f"Error in analytics data debug: {str(e)}")
        logger.error(traceback.format_exc())
        results['status'] = 'error'
        results['error'] = str(e)
    
    return jsonify(results), 200

# Serve React App
@app.route('/')
def serve():
    try:
        if os.path.exists(os.path.join(app.static_folder, 'index.html')):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return jsonify({
                'status': 'API Only Mode',
                'message': 'The Lineup Boss API is running, but the frontend is not available.',
                'api_status': 'API is available at /api',
                'api_docs': 'API documentation is available at /api/docs'
            })
    except Exception as e:
        return jsonify({
            'status': 'Error',
            'message': f'Error serving frontend: {str(e)}',
            'api_status': 'API is available at /api'
        }), 500

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def static_proxy(path):
    # If path starts with 'api/', pass it through to the API
    if path.startswith('api/'):
        # Log the API request for debugging
        print(f"API request: /{path} => {request.method} {request.endpoint or 'no endpoint'}")
        
        # Redirect requests to direct routes when available
        if 'auth/login' in path:
            print(f"Auth login request detected in proxy: {path} - redirecting to direct route")
            return jsonify({
                'error': 'Login should be handled by the direct route',
                'message': 'Please retry your login request'
            }), 307  # 307 preserves the request method and body
            
        # Team operations - redirect to direct routes
        if request.method == 'POST' and path == 'api/teams/':
            print(f"Team create request detected in proxy: {path} - redirecting to direct route")
            return jsonify({
                'error': 'Team creation should be handled by the direct route',
                'message': 'Please retry your request'
            }), 307
            
        # Game creation - direct call for RESTful path
        if request.method == 'POST' and 'teams' in path and 'games' in path:
            print(f"Game create request detected in proxy: {path}")
            
            # Extract team_id from the path
            team_id = None
            parts = path.split('/')
            for i, part in enumerate(parts):
                if part == 'teams' and i+1 < len(parts) and parts[i+1].isdigit():
                    team_id = int(parts[i+1])
                    break
                    
            if team_id:
                print(f"Redirecting to direct game creation for team {team_id}")
                from werkzeug.utils import redirect
                target_url = f"/api/teams/{team_id}/games"
                print(f"Redirecting to: {target_url}")
                return redirect(target_url, code=307)  # 307 preserves the POST method and body
            else:
                return jsonify({
                    'error': 'Invalid team ID in request path',
                    'message': 'Could not extract team ID for game creation'
                }), 400
                
        # Game batting order - direct call for RESTful path
        if request.method == 'POST' and 'games' in path and 'batting-order' in path:
            print(f"Batting order save request detected in proxy: {path}")
            
            # Extract game_id from the path
            game_id = None
            parts = path.split('/')
            for i, part in enumerate(parts):
                if part == 'games' and i+1 < len(parts) and parts[i+1].isdigit():
                    game_id = int(parts[i+1])
                    break
                    
            if game_id:
                print(f"Redirecting to direct batting order save for game {game_id}")
                from werkzeug.utils import redirect
                target_url = f"/api/games/{game_id}/batting-order"
                print(f"Redirecting to: {target_url}")
                return redirect(target_url, code=307)  # 307 preserves the POST method and body
            else:
                return jsonify({
                    'error': 'Invalid game ID in request path',
                    'message': 'Could not extract game ID for batting order save'
                }), 400
                
        # Game fielding rotation - direct call for RESTful path
        if request.method == 'POST' and 'games' in path and 'fielding-rotations' in path:
            print(f"Fielding rotation save request detected in proxy: {path}")
            
            # Extract game_id and inning from the path
            game_id = None
            inning = None
            parts = path.split('/')
            for i, part in enumerate(parts):
                if part == 'games' and i+1 < len(parts) and parts[i+1].isdigit():
                    game_id = int(parts[i+1])
                if part == 'fielding-rotations' and i+1 < len(parts) and parts[i+1].isdigit():
                    inning = int(parts[i+1])
                    
            if game_id and inning:
                print(f"Redirecting to direct fielding rotation save for game {game_id}, inning {inning}")
                from werkzeug.utils import redirect
                target_url = f"/api/games/{game_id}/fielding-rotations/{inning}"
                print(f"Redirecting to: {target_url}")
                return redirect(target_url, code=307)  # 307 preserves the POST method and body
            else:
                return jsonify({
                    'error': 'Invalid game ID or inning in request path',
                    'message': 'Could not extract game ID or inning for fielding rotation save'
                }), 400
                
        # Player availability - direct call for RESTful path
        if request.method == 'POST' and 'games' in path and 'player-availability' in path:
            print(f"Player availability save request detected in proxy: {path}")
            
            # Special handling for batch updates
            if 'batch' in path:
                print(f"Batch player availability save detected: {path}")
                
                # Extract game_id from the path
                game_id = None
                parts = path.split('/')
                for i, part in enumerate(parts):
                    if part == 'games' and i+1 < len(parts) and parts[i+1].isdigit():
                        game_id = int(parts[i+1])
                        break
                
                if game_id:
                    print(f"Calling direct batch player availability save for game {game_id}")
                    # Call the direct function instead of redirecting
                    try:
                        return direct_batch_save_player_availability(game_id)
                    except Exception as e:
                        print(f"Error in direct batch player availability call: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        return jsonify({
                            'error': f'Error processing batch player availability: {str(e)}',
                            'path': path,
                            'game_id': game_id
                        }), 500
                else:
                    return jsonify({
                        'error': 'Invalid game ID in request path',
                        'message': 'Could not extract game ID for batch player availability save'
                    }), 400
            
            # Regular (non-batch) player availability
            # Extract game_id and player_id from the path
            game_id = None
            player_id = None
            parts = path.split('/')
            for i, part in enumerate(parts):
                if part == 'games' and i+1 < len(parts) and parts[i+1].isdigit():
                    game_id = int(parts[i+1])
                if part == 'player-availability' and i+1 < len(parts) and parts[i+1].isdigit():
                    player_id = int(parts[i+1])
                    
            if game_id and player_id:
                print(f"Redirecting to direct player availability save for game {game_id}, player {player_id}")
                from werkzeug.utils import redirect
                target_url = f"/api/games/{game_id}/player-availability/{player_id}"
                print(f"Redirecting to: {target_url}")
                return redirect(target_url, code=307)  # 307 preserves the POST method and body
            else:
                return jsonify({
                    'error': 'Invalid game ID or player ID in request path',
                    'message': 'Could not extract game ID or player ID for player availability save'
                }), 400
        
        # AI Fielding Rotation - direct call instead of redirect with special auth handling
        if request.method == 'POST' and 'games' in path and 'ai-fielding-rotation' in path:
            print(f"AI fielding rotation request detected in proxy: {path}")
            
            # Enhanced debug information
            print("AI FIELDING ROTATION PROXY HANDLER - Request Headers:")
            for key, value in request.headers.items():
                # Don't print the full token value
                if key.lower() == 'authorization':
                    if value:
                        print(f"  {key}: {value[:15]}... [PRESENT]")
                        # Also log the token type to see if it matches what we expect
                        token_parts = value.split()
                        if len(token_parts) == 2:
                            print(f"  Token type: {token_parts[0]}")
                        else:
                            print(f"  Token format is not as expected. Parts: {len(token_parts)}")
                    else:
                        print(f"  {key}: [EMPTY]")
                else:
                    print(f"  {key}: {value}")
            
            # Extract game_id from the path
            game_id = None
            parts = path.split('/')
            for i, part in enumerate(parts):
                if part == 'games' and i+1 < len(parts) and parts[i+1].isdigit():
                    game_id = int(parts[i+1])
                    break
            
            if not game_id:
                print("ERROR: Could not extract game_id from path")
                return jsonify({
                    'error': 'Invalid game ID in request path',
                    'message': 'Could not extract game ID for AI fielding rotation generation'
                }), 400
            
            print(f"Direct handling AI fielding rotation for game {game_id}")
            
            # Check for authorization header
            if 'Authorization' not in request.headers:
                print("CRITICAL ERROR: No Authorization header in AI rotation request")
                auth_header = request.headers.get('X-Authorization') or request.headers.get('x-authorization')
                if auth_header:
                    print(f"Found alternative authorization header: {auth_header[:15]}...")
                    # Copy to standard header
                    from werkzeug.datastructures import Headers
                    modified_headers = Headers(request.headers)
                    modified_headers['Authorization'] = auth_header
                    request.headers = modified_headers
                    print("Copied alternative authorization header to standard header")
                else:
                    print("ERROR: No alternative authorization header found")
                    # Try to extract from cookie if present
                    jwt_cookie = request.cookies.get('jwt')
                    if jwt_cookie:
                        print(f"Found JWT cookie: {jwt_cookie[:15]}...")
                        from werkzeug.datastructures import Headers
                        modified_headers = Headers(request.headers)
                        modified_headers['Authorization'] = f"Bearer {jwt_cookie}"
                        request.headers = modified_headers
                        print("Created Authorization header from JWT cookie")
                    else:
                        print("ERROR: No JWT cookie found")
            
            # Extra option - try extracting token from query param if present
            if 'token' in request.args:
                print("Found token in query parameter")
                from werkzeug.datastructures import Headers
                modified_headers = Headers(request.headers)
                modified_headers['Authorization'] = f"Bearer {request.args.get('token')}"
                request.headers = modified_headers
                print("Created Authorization header from query parameter")
            
            # Instead of redirecting, directly call the function to preserve headers
            try:
                print("Calling direct_generate_ai_fielding_rotation directly")
                response = direct_generate_ai_fielding_rotation(game_id)
                print(f"Direct call returned response with status: {response[1] if isinstance(response, tuple) else '200'}")
                return response
            except Exception as e:
                print(f"Error in direct call to AI rotation handler: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'error': f'Error processing AI fielding rotation: {str(e)}',
                    'path': path,
                    'game_id': game_id
                }), 500
        
        # Player creation - direct call instead of redirect for RESTful path
        if request.method == 'POST' and 'teams' in path and 'players' in path:
            print(f"Player create request detected in proxy: {path}")
            
            # Extract team_id from the path
            team_id = None
            parts = path.split('/')
            for i, part in enumerate(parts):
                if part == 'teams' and i+1 < len(parts) and parts[i+1].isdigit():
                    team_id = int(parts[i+1])
                    break
                    
            if team_id:
                print(f"Redirecting to direct player creation for team {team_id}")
                from werkzeug.utils import redirect
                target_url = f"/api/teams/{team_id}/players"
                print(f"Redirecting to: {target_url}")
                return redirect(target_url, code=307)  # 307 preserves the POST method and body
            else:
                return jsonify({
                    'error': 'Invalid team ID in request path',
                    'message': 'Could not extract team ID for player creation'
                }), 400
        
        # Game deletion - redirect to direct route
        if request.method == 'DELETE' and 'games' in path:
            print(f"Game delete request detected in proxy: {path}")
            
            # Extract game_id from the path
            game_id = None
            parts = path.split('/')
            for i, part in enumerate(parts):
                if part == 'games' and i+1 < len(parts) and parts[i+1].isdigit():
                    game_id = int(parts[i+1])
                    break
                    
            if game_id:
                print(f"Redirecting to direct game deletion for game {game_id}")
                from werkzeug.utils import redirect
                target_url = f"/api/games/{game_id}"
                print(f"Redirecting to: {target_url}")
                return redirect(target_url, code=307)  # 307 preserves the DELETE method
            else:
                return jsonify({
                    'error': 'Invalid game ID in request path',
                    'message': 'Could not extract game ID for deletion'
                }), 400
        
        # Player deletion - redirect to direct route
        if request.method == 'DELETE' and 'players' in path:
            print(f"Player delete request detected in proxy: {path}")
            
            # Extract player_id from the path
            player_id = None
            parts = path.split('/')
            for i, part in enumerate(parts):
                if part == 'players' and i+1 < len(parts) and parts[i+1].isdigit():
                    player_id = int(parts[i+1])
                    break
                    
            if player_id:
                print(f"Redirecting to direct player deletion for player {player_id}")
                from werkzeug.utils import redirect
                target_url = f"/api/players/{player_id}"
                print(f"Redirecting to: {target_url}")
                return redirect(target_url, code=307)  # 307 preserves the DELETE method
            else:
                return jsonify({
                    'error': 'Invalid player ID in request path',
                    'message': 'Could not extract player ID for deletion'
                }), 400
                
        # More detailed debugging for DELETE requests
        if request.method == 'DELETE' and 'teams' in path:
            team_id = None
            
            # Improved path parsing - handle possible trailing slash
            print(f"Raw path for deletion: '{path}'")
            
            # First, strip any trailing slash
            clean_path = path.rstrip('/')
            print(f"Cleaned path: '{clean_path}'")
            
            # Now extract the ID
            parts = clean_path.split('/')
            print(f"Path parts: {parts}")
            
            # Try to get the last part as the ID
            if parts and len(parts) >= 1:
                last_part = parts[-1]
                print(f"Last part: '{last_part}'")
                
                if last_part.isdigit():
                    team_id = int(last_part)
                    print(f"Extracted team_id: {team_id}")
            
            print(f"Team delete request detected in proxy: {path}, team_id extracted: {team_id}")
            
            # Redirect to our direct deletion endpoint
            if team_id:
                from werkzeug.utils import redirect
                print(f"Redirecting DELETE request to direct_team_delete for team_id={team_id}")
                # Use 307 to preserve the DELETE method
                target_url = f"/api/teams/{team_id}"
                print(f"Redirecting to: {target_url}")
                return redirect(target_url, code=307)
            else:
                return jsonify({
                    'error': 'Invalid team ID format in DELETE request',
                    'message': f"Could not extract a valid team ID from path: {path}"
                }), 400
        
        # Check for problematic double API prefixes and warn (these should no longer happen)
        if path.startswith('api/api/'):
            print(f"WARNING: Detected obsolete double API prefix in request path: /{path}")
            return jsonify({
                'error': 'Double API prefix detected. The /api/api/ routes have been removed.',
                'message': 'Please update your client to use standard /api/ routes.'
            }), 400
        
        # Check if we have an endpoint
        if request.endpoint:
            # Flask will handle API routes via blueprint
            try:
                # For non-auth routes, follow the original logic
                endpoint_function = app.view_functions.get(request.endpoint)
                
                # Use a safer approach without recursion
                if endpoint_function.__code__.co_argcount == 0:
                    # Function takes no arguments
                    return endpoint_function()
                else:
                    # Function probably takes a path argument
                    return endpoint_function(path)
                    
            except Exception as e:
                print(f"Error calling endpoint function: {str(e)}")
                print(f"Exception type: {type(e).__name__}")
                return jsonify({'error': f'Error processing request: {str(e)}'}), 500
        else:
            # If we don't have an endpoint, this could be a routing issue
            print(f"ERROR: No endpoint found for /{path}")
            return jsonify({'error': f'No route matches: /{path}'}), 404
        
    # For all other paths (like /admin, /dashboard, etc.)
    # Return the React app's index.html to handle client-side routing
    try:
        if os.path.exists(os.path.join(app.static_folder, 'index.html')):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return jsonify({'error': 'Frontend not available'}), 404
    except Exception as e:
        print(f"Error serving static file: {str(e)}")
        return jsonify({'error': 'Not found'}), 404
    
    # If nothing else worked, try to serve as a static file
    try:
        return app.send_static_file(path)
    except Exception:
        return jsonify({'error': f'Path {path} not found'}), 404

# ===================================================================
# ROUTE ARCHITECTURE DOCUMENTATION
# ===================================================================
"""
ROUTE ARCHITECTURE
------------------
All LineupBoss API routes are defined in their respective blueprints:
- /api/auth/... - Authentication endpoints in api/auth.py
- /api/user/... - User profile endpoints in api/users.py
- /api/teams/... - Team management in api/teams.py
- /api/players/... - Player management in api/players.py
- /api/games/... - Game management in api/games.py
- /api/admin/... - Admin functions in api/admin.py
- /api/system/... - System endpoints in api/system.py

These blueprints are registered in api/__init__.py with the appropriate prefixes.
Direct route registration in app.py should be avoided to prevent inconsistencies.

NOTE: As of March 2025, all emergency routes with '/api/api/' prefixes and deprecated direct routes 
have been removed. The frontend now uses standardized RESTful routes exclusively.
"""

# Import database module directly for testing
try:
    from shared.db import db_session, db_error_response
    logger.info("Successfully imported shared.db module at app startup")
except ImportError as e:
    logger.error(f"Failed to import shared.db: {str(e)}")
    logger.error(traceback.format_exc())

# Initialize database before first request
def before_first_request():
    init_db()
    
    # Log database availability for diagnostics
    logger.info("Checking database access and modules for analytics")
    try:
        from services.analytics_service import AnalyticsService, HAS_DB_DEPENDENCIES
        logger.info(f"Analytics service imported, database dependencies available: {HAS_DB_DEPENDENCIES}")
        
        # Check if database models are accessible
        from shared.models import Game, BattingOrder, FieldingRotation
        logger.info("Database models imported successfully")
        
        # Check if API blueprints are registered
        api_routes = []
        for rule in app.url_map.iter_rules():
            if "/api/" in str(rule):
                api_routes.append(str(rule))
        logger.info(f"API routes registered: {len(api_routes)}")
        
    except ImportError as e:
        logger.error(f"Failed to import module for analytics diagnostics: {str(e)}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Error during database diagnostics: {str(e)}")
        logger.error(traceback.format_exc())
    
with app.app_context():
    before_first_request()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
