
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

# Direct team analytics endpoints
@app.route('/api/analytics/teams/<int:team_id>/batting-analytics', methods=['GET'])
@jwt_required()
def direct_team_batting_analytics(team_id):
    """Direct batting analytics endpoint if blueprint fails"""
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
    """Direct fielding analytics endpoint if blueprint fails"""
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
    """Direct team analytics endpoint if blueprint fails"""
    logger.info(f"Direct team analytics endpoint called for team {team_id}")
    try:
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService.get_team_analytics(team_id)
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error in direct team analytics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get team analytics: {str(e)}"}), 500

# Add diagnostic route directly to app
@app.route('/api/debug/analytics-status', methods=['GET'])
def analytics_status_debug():
    """Diagnostic endpoint to verify routing is working"""
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
    analytics_routes = []
    
    try:
        from services.analytics_service import AnalyticsService
        has_analytics_service = True
    except ImportError:
        pass
    
    try:
        from api.analytics import analytics_bp
        has_analytics_bp = True
        
        # Note that we have the analytics blueprint
        analytics_routes.append("analytics_bp is available")
        
        # Try to get routes if possible, but this is optional
        try:
            if hasattr(analytics_bp, 'deferred_functions'):
                for rule in analytics_bp.deferred_functions:
                    if hasattr(rule, '__name__'):
                        analytics_routes.append(rule.__name__)
        except Exception as e:
            analytics_routes.append(f"Error getting routes: {str(e)}")
    except ImportError:
        pass
    
    # Collect all API routes
    all_routes = []
    for rule in app.url_map.iter_rules():
        rule_str = str(rule)
        if '/api/analytics' in rule_str:
            all_routes.append(rule_str)
    
    # Return comprehensive diagnostic information
    return jsonify({
        'status': 'ok',
        'message': 'API diagnostics endpoint',
        'registered_blueprints': registered_blueprints,
        'analytics_registered': analytics_registered,
        'has_analytics_service': has_analytics_service,
        'has_analytics_bp': has_analytics_bp,
        'analytics_routes': analytics_routes,
        'api_analytics_routes': all_routes,
        'environment': os.environ.get('FLASK_ENV', 'undefined'),
    }), 200

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
                # The endpoint function may or may not expect a path parameter
                endpoint_function = app.view_functions.get(request.endpoint)
                import inspect
                sig = inspect.signature(endpoint_function)
                if 'path' in sig.parameters:
                    # If the function expects a path parameter, pass it
                    return endpoint_function(path)
                else:
                    # Otherwise just call it with no arguments
                    return endpoint_function()
            except Exception as e:
                print(f"Error calling endpoint function: {str(e)}")
                import traceback
                traceback.print_exc()
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
