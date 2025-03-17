
from flask import Flask, jsonify, send_from_directory, Blueprint, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
import importlib.util

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
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)  # Set token expiration to 30 days
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

@app.route('/<path:path>')
def static_proxy(path):
    # If path starts with 'api/', pass it through to the API
    if path.startswith('api/'):
        # Flask will handle API routes via blueprint
        return app.view_functions.get(request.endpoint)()
        
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

# API root route
@app.route('/api')
def hello():
    return jsonify({'message': 'Welcome to Lineup API'})

# Test JWT route
@app.route('/api/test-jwt')
@jwt_required()
def test_jwt():
    current_user_id = get_jwt_identity()
    auth_header = request.headers.get('Authorization', 'None')
    print(f"Authorization header: {auth_header}")
    print(f"Current user ID from JWT: {current_user_id}")
    return jsonify({'message': 'JWT is valid', 'user_id': current_user_id})

# Add explicit API endpoints for user profile
@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def app_get_user_profile():
    """Get the current user's profile information."""
    # Import needed modules within the function to avoid circular imports
    from flask_jwt_extended import get_jwt_identity
    from shared.models import User
    from shared.database import db_session
    
    user_id = get_jwt_identity()
    
    with db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "city": user.city,
            "state": user.state,
            "country": user.country,
            "zip_code": user.zip_code,
            "role": user.role,
            "subscription_tier": user.subscription_tier,
            "created_at": user.created_at.isoformat() if user.created_at else None
        })

@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def app_update_user_profile():
    """Update the current user's profile information."""
    # Import needed modules within the function to avoid circular imports
    from flask_jwt_extended import get_jwt_identity
    from shared.models import User
    from shared.database import db_session
    import logging
    
    # Log detailed information
    print("*** PROFILE UPDATE STARTED ***")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    print(f"Request headers: {dict(request.headers)}")
    
    try:
        user_id = get_jwt_identity()
        print(f"User ID from JWT: {user_id}")
        
        data = request.json
        print(f"Request data: {data}")
        
        # Validate input
        if not data:
            print("Error: No data provided")
            return jsonify({"error": "No data provided"}), 400
            
        with db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                print(f"Error: User {user_id} not found")
                return jsonify({"error": "User not found"}), 404
                
            print(f"Found user: {user.email}")
                
            # Update user fields
            if 'first_name' in data:
                user.first_name = data['first_name']
                print(f"Updated first_name to: {data['first_name']}")
            if 'last_name' in data:
                user.last_name = data['last_name']
                print(f"Updated last_name to: {data['last_name']}")
            if 'city' in data:
                user.city = data['city']
                print(f"Updated city to: {data['city']}")
            if 'state' in data:
                user.state = data['state']
                print(f"Updated state to: {data['state']}")
            if 'country' in data:
                user.country = data['country']
                print(f"Updated country to: {data['country']}")
            if 'zip_code' in data:
                user.zip_code = data['zip_code']
                print(f"Updated zip_code to: {data['zip_code']}")
            if 'email' in data:
                # Check if email is already taken
                existing_user = session.query(User).filter(
                    User.email == data['email'], 
                    User.id != user_id
                ).first()
                
                if existing_user:
                    print(f"Error: Email {data['email']} already in use by user {existing_user.id}")
                    return jsonify({"error": "Email already in use"}), 400
                    
                user.email = data['email']
                print(f"Updated email to: {data['email']}")
                
            session.commit()
            print("Database commit successful")
            
            response_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "city": user.city,
                "state": user.state,
                "country": user.country,
                "zip_code": user.zip_code,
                "role": user.role,
                "subscription_tier": user.subscription_tier,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            print(f"Response data: {response_data}")
            print("*** PROFILE UPDATE COMPLETED SUCCESSFULLY ***")
            return jsonify(response_data)
    except Exception as e:
        print(f"*** PROFILE UPDATE ERROR: {str(e)} ***")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/user/password', methods=['PUT'])
@jwt_required()
def app_update_password():
    """Update the current user's password."""
    # Import needed modules within the function to avoid circular imports
    from flask_jwt_extended import get_jwt_identity
    from shared.models import User
    from shared.database import db_session
    
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate input
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({"error": "Current password and new password required"}), 400
        
    with db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({"error": "Current password is incorrect"}), 400
            
        # Update password
        user.set_password(data['new_password'])
        session.commit()
        
        return jsonify({"message": "Password updated successfully"})

@app.route('/api/user/subscription', methods=['GET'])
@jwt_required()
def app_get_subscription():
    """Get the current user's subscription information."""
    # Import needed modules within the function to avoid circular imports
    from flask_jwt_extended import get_jwt_identity
    from shared.models import User
    from shared.database import db_session
    import logging
    
    # Log detailed information
    print("*** SUBSCRIPTION INFO REQUEST STARTED ***")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    print(f"Request headers: {dict(request.headers)}")
    
    try:
        user_id = get_jwt_identity()
        print(f"User ID from JWT: {user_id}")
        
        with db_session() as session:
            print("Database session created")
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                print(f"Error: User {user_id} not found")
                return jsonify({"error": "User not found"}), 404
                
            print(f"Found user: {user.email} with subscription tier: {user.subscription_tier}")
            
            # Define features directly in this endpoint to avoid import issues
            def get_tier_features(tier):
                """Get the features available for a subscription tier."""
                tier = str(tier).lower() if tier else "rookie"
                
                features = {
                    "rookie": {
                        "name": "Rookie",
                        "max_teams": 2,
                        "advanced_stats": False,
                        "team_collaboration": False,
                        "price": 0
                    },
                    "pro": {
                        "name": "Pro",
                        "max_teams": 999,  # Unlimited for practical purposes
                        "advanced_stats": True,
                        "team_collaboration": True,
                        "price": 9.99  # Monthly price in USD
                    }
                }
                
                return features.get(tier, features["rookie"])
            
            # For now, we're just returning basic subscription info
            response_data = {
                "tier": user.subscription_tier,
                "features": get_tier_features(user.subscription_tier)
            }
            print(f"Response data: {response_data}")
            print("*** SUBSCRIPTION INFO REQUEST COMPLETED SUCCESSFULLY ***")
            return jsonify(response_data)
    except Exception as e:
        print(f"*** SUBSCRIPTION INFO REQUEST ERROR: {str(e)} ***")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Test database endpoint
@app.route('/api/test-db')
def test_db():
    try:
        db = next(get_db())
        from models.models import User
        user_count = db.query(User).count()
        db.close()
        return jsonify({'message': 'Database connection successful', 'user_count': user_count})
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

# Initialize database before first request
def before_first_request():
    init_db()
    
with app.app_context():
    before_first_request()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
