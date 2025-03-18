
from flask import Flask, jsonify, send_from_directory, Blueprint, request, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager
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
    return jsonify({"error": "Token has expired"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    print(f"Invalid token error: {error_string}")
    return jsonify({"error": f"Invalid token: {error_string}"}), 401

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    print(f"Missing token error: {error_string}")
    return jsonify({"error": f"Missing token: {error_string}"}), 401

@jwt.token_verification_failed_loader
def token_verification_failed_callback():
    print("Token verification failed")
    return jsonify({"error": "Token verification failed"}), 401

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
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
     expose_headers=["Authorization", "Content-Type"],
     max_age=86400)

# Register API blueprint
app.register_blueprint(api)

# Register API documentation blueprints
app.register_blueprint(docs, url_prefix='/api')
app.register_blueprint(swagger_ui_blueprint)

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
    # Check for problematic double API prefixes and handle them
    if path.startswith('api/api/'):
        print(f"WARNING: Detected double API prefix in request path: /{path}")
        
        # If it's not one of our explicitly handled auth endpoints, try generic handling
        if not path.startswith('api/api/auth/'):
            # Create a fixed path by removing one api prefix
            fixed_path = path.replace('api/api/', 'api/')
            print(f"Trying to redirect to fixed path: /{fixed_path}")
            
            # For POST requests, we need to preserve the request body
            if request.method == 'POST':
                data = request.get_json()
                headers = dict(request.headers)
                
                # Make an internal redirect by calling the correct view function if possible
                # This is better than an HTTP redirect which would lose the request body
                if fixed_path.startswith('api/auth/'):
                    # Auth-related paths
                    try:
                        from api.auth import auth
                        endpoint = fixed_path.replace('api/auth/', '')
                        if endpoint == 'login':
                            from api.auth import login
                            return login()
                        elif endpoint == 'register':
                            from api.auth import register
                            return register()
                        # Add more endpoints as needed
                    except Exception as e:
                        print(f"Error redirecting auth request: {str(e)}")
        # Continue processing to let our explicit route handlers work
    
    # If path starts with 'api/', pass it through to the API
    if path.startswith('api/'):
        # Log the API request for debugging
        print(f"API request: /{path} => {request.method} {request.endpoint or 'no endpoint'}")
        
        # Check if we have an endpoint
        if request.endpoint:
            # Flask will handle API routes via blueprint
            return app.view_functions.get(request.endpoint)()
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
# TEMPORARY EMERGENCY FIXES FOR DOUBLE API PREFIX ISSUES
# These routes will be removed once the frontend API client update is deployed
# They handle the /api/api/ prefixed URLs that may still be requested by clients
# ===================================================================

# Emergency fix for double-prefixed login/register
@app.route('/api/api/auth/login', methods=['POST'])
def fix_double_api_prefix_login():
    """TEMPORARY ROUTE - Will be removed after frontend update is deployed."""
    print("[API] EMERGENCY FIX: Handling /api/api/auth/login request")
    from api.auth import login as auth_login
    return auth_login()

@app.route('/api/api/auth/register', methods=['POST'])
def fix_double_api_prefix_register():
    """TEMPORARY ROUTE - Will be removed after frontend update is deployed."""
    print("[API] EMERGENCY FIX: Handling /api/api/auth/register request")
    from api.auth import register as auth_register
    return auth_register()

# Emergency fix for double-prefixed auth endpoints
@app.route('/api/api/auth/me', methods=['GET'])
@jwt_required()
def fix_double_api_prefix_me():
    """TEMPORARY ROUTE - Will be removed after frontend update is deployed."""
    print("[API] EMERGENCY FIX: Handling /api/api/auth/me request")
    from api.auth import get_user_info
    from flask import g
    g.user_id = get_jwt_identity()
    return get_user_info()

@app.route('/api/api/auth/refresh', methods=['POST'])
@jwt_required()
def fix_double_api_prefix_refresh():
    """TEMPORARY ROUTE - Will be removed after frontend update is deployed."""
    print("[API] EMERGENCY FIX: Handling /api/api/auth/refresh request")
    from api.auth import refresh_token
    return refresh_token()

# Emergency fix for double-prefixed user endpoints
@app.route('/api/api/user/profile', methods=['GET'])
@jwt_required()
def fix_double_api_prefix_get_profile():
    """TEMPORARY ROUTE - Will be removed after frontend update is deployed."""
    print("[API] EMERGENCY FIX: Handling /api/api/user/profile GET request")
    from api.users import get_user_profile
    from flask import g
    g.user_id = get_jwt_identity()
    return get_user_profile()

@app.route('/api/api/user/profile', methods=['PUT'])
@jwt_required()
def fix_double_api_prefix_update_profile():
    """TEMPORARY ROUTE - Will be removed after frontend update is deployed."""
    print("[API] EMERGENCY FIX: Handling /api/api/user/profile PUT request")
    from api.users import update_user_profile
    from flask import g
    g.user_id = get_jwt_identity()
    return update_user_profile()

# Emergency fix for double-prefixed teams endpoints
@app.route('/api/api/teams', methods=['GET'])
@jwt_required()
def fix_double_api_prefix_get_teams():
    """TEMPORARY ROUTE - Will be removed after frontend update is deployed."""
    print("[API] EMERGENCY FIX: Handling /api/api/teams GET request")
    from api.teams import get_teams
    from flask import g
    g.user_id = get_jwt_identity()
    return get_teams()

# ===================================================================
# DEPRECATED ENDPOINTS - WILL BE REMOVED IN A FUTURE RELEASE
# All endpoints below are deprecated and will be removed in a future release
# They are maintained for backward compatibility but should not be used
# ===================================================================

# DEPRECATED: Root API route - use system blueprint instead
@app.route('/api')
def hello():
    print("[API] WARNING: Using deprecated direct route /api")
    return jsonify({'message': 'Welcome to Lineup API'})

# DEPRECATED: Test JWT route - use system blueprint instead
@app.route('/api/test-jwt')
@jwt_required()
def test_jwt():
    print("[API] WARNING: Using deprecated direct route /api/test-jwt")
    current_user_id = get_jwt_identity()
    return jsonify({'message': 'JWT is valid', 'user_id': current_user_id})

# ===================================================================
# ROUTE ARCHITECTURE DOCUMENTATION
# ===================================================================
"""
ROUTE ARCHITECTURE
------------------
All LineupBoss API routes should be defined in their respective blueprints:
- /api/auth/... - Authentication endpoints in api/auth.py
- /api/user/... - User profile endpoints in api/users.py
- /api/teams/... - Team management in api/teams.py
- /api/players/... - Player management in api/players.py
- /api/games/... - Game management in api/games.py
- /api/admin/... - Admin functions in api/admin.py
- /api/system/... - System endpoints in api/system.py

These blueprints are registered in api/__init__.py with the appropriate prefixes.
Direct route registration in app.py should be avoided to prevent inconsistencies.
"""

# ===================================================================
# DEPRECATED ROUTES - SCHEDULED FOR REMOVAL ON MAY 1, 2025
# These endpoints are duplicates of blueprint-based routes. Use the blueprint routes instead:
# - User endpoints: api.users module with route prefix /api/user
# - System endpoints: api.system module with route prefix /api
# ===================================================================

# Helper function for deprecated route handlers
def handle_deprecated_route(path, handler_func):
    """Common handler for deprecated routes that logs a warning and forwards to the blueprint handler"""
    print(f"[API] WARNING: Deprecated direct route accessed: {path}")
    
    # Use Flask's g object to store the JWT identity, which token_required expects
    g.user_id = get_jwt_identity()
    
    return handler_func()

# DEPRECATED USER ENDPOINTS - Use /api/user/profile instead
@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def redirect_user_profile_get():
    """TO BE REMOVED - Use the users_bp blueprint endpoint /api/user/profile instead"""
    from api.users import get_user_profile
    return handle_deprecated_route('/api/user/profile [GET]', get_user_profile)

@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def redirect_user_profile_put():
    """TO BE REMOVED - Use the users_bp blueprint endpoint /api/user/profile instead"""
    from api.users import update_user_profile
    return handle_deprecated_route('/api/user/profile [PUT]', update_user_profile)

@app.route('/api/user/password', methods=['PUT'])
@jwt_required()
def redirect_user_password_put():
    """TO BE REMOVED - Use the users_bp blueprint endpoint /api/user/password instead"""
    from api.users import update_password
    return handle_deprecated_route('/api/user/password [PUT]', update_password)

@app.route('/api/user/subscription', methods=['GET'])
@jwt_required()
def redirect_user_subscription_get():
    """TO BE REMOVED - Use the users_bp blueprint endpoint /api/user/subscription instead"""
    from api.users import get_subscription
    return handle_deprecated_route('/api/user/subscription [GET]', get_subscription)

# DEPRECATED SYSTEM ENDPOINTS - Use /api/test-db instead
@app.route('/api/test-db')
def test_db():
    """TO BE REMOVED - Use the system blueprint endpoint /api/test-db instead"""
    print("[API] WARNING: Using deprecated direct route /api/test-db")
    
    # Forward to the system blueprint implementation
    from api.system import test_db as system_test_db
    return system_test_db()

# Initialize database before first request
def before_first_request():
    init_db()
    
with app.app_context():
    before_first_request()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
