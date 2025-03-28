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

# Load configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "development-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60 * 60 * 24 * 30  # 30 days
app.config["JWT_ALGORITHM"] = "HS256"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///lineup.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# If DATABASE_URL starts with postgres://, replace with postgresql://
# This is needed for SQLAlchemy 1.4+ with Heroku
db_url = app.config["SQLALCHEMY_DATABASE_URI"]
if db_url.startswith("postgres://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://", 1)

# Initialize JWT
jwt = JWTManager(app)

# Initialize database on startup
# Flask 3.0+ removed before_first_request, so we initialize immediately
try:
    init_db()
    print("Database initialized successfully.")
except Exception as e:
    print(f"ERROR initializing database: {e}")
    traceback.print_exc()

# Serve React App
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    """
    Serve the React frontend.
    """
    print(f"Serving path: {path}")
    # Special case for /api/ path to show API info
    if path == "api":
        return jsonify({
            "name": "Lineup Boss API",
            "version": "1.0",
            "status": "active"
        })
    
    if path != "" and os.path.exists(app.static_folder + "/" + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

@app.errorhandler(404)
def not_found(e):
    """
    Handle 404 errors.
    """
    print(f"404 error: {request.path}")
    
    # Check if this is an API request
    if request.path.startswith('/api/'):
        return jsonify({"error": "API endpoint not found"}), 404
    
    # For all other requests, return the React app
    return send_from_directory(app.static_folder, "index.html")

@app.route('/api/token-info', methods=['GET'])
def token_info():
    """
    Endpoint for debugging JWT token issues.
    """
    # Print the incoming request for debugging
    print(f"token-info request headers: {dict(request.headers)}")
    
    # Extract auth header
    auth_header = request.headers.get('Authorization')
    x_auth_header = request.headers.get('X-Authorization')
    
    if not auth_header and not x_auth_header:
        return jsonify({"error": "No authorization header found"}), 401
    
    # Use the first available header
    token_header = auth_header or x_auth_header
    
    # Extract token
    if token_header.startswith('Bearer '):
        token = token_header.split(' ')[1]
    else:
        token = token_header
        
    # Build request info
    request_info = {
        "token_length": len(token) if token else 0,
        "token_preview": token[:10] + "..." if token and len(token) > 10 else token,
        "headers": dict(request.headers),
        "path": request.path,
        "method": request.method
    }
    
    try:
        # Try to decode token without verification
        import jwt as pyjwt
        decoded = pyjwt.decode(token, options={"verify_signature": False})
        return jsonify({
            "success": True,
            "token_info": {
                "sub": decoded.get("sub"),
                "exp": decoded.get("exp"),
                "iat": decoded.get("iat"),
                "type": decoded.get("type")
            },
            "request_info": request_info
        })
    except Exception as e:
        # Token is invalid or corrupted
        print(f"Token decode error: {str(e)}")
    
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

# Keep the auth login route as it's critical for authentication
@app.route('/api/auth/login/', methods=['POST'])
def direct_auth_login():
    """Direct route for login to handle critical authentication"""
    print("Direct login route activated")
    from api.auth import login
    return login()

# Debug route to list all registered routes
@app.route('/api/debug/routes', methods=['GET'])
def debug_routes():
    """Debug endpoint to list all registered routes."""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)

# Run server if executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)