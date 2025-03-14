
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from services.auth_service import AuthService

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    print("Register endpoint hit")
    data = request.get_json()
    print(f"Received data: {data}")
    
    if not data or not data.get('email') or not data.get('password'):
        print("Missing email or password")
        return jsonify({'error': 'Email and password are required'}), 400
    
    db = get_db()
    try:
        # Check if user already exists
        existing_user = AuthService.get_user_by_email(db, data['email'])
        if existing_user:
            print(f"User already exists with email: {data['email']}")
            return jsonify({'error': 'Email already registered'}), 409
        
        # Register user via service
        print(f"Registering new user with email: {data['email']}")
        user, access_token = AuthService.register_user(db, data['email'], data['password'])
        print(f"User registered successfully with ID: {user.id}")
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user_id': user.id
        }), 201
    except Exception as e:
        print(f"Error during registration: {str(e)}")
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500
    finally:
        db.close()

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    db = get_db()
    try:
        # Login user via service
        user, access_token = AuthService.login_user(db, data['email'], data['password'])
        
        if not user or not access_token:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        return jsonify({
            'access_token': access_token,
            'user_id': user.id
        }), 200
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return jsonify({'error': f'Login failed: {str(e)}'}), 500
    finally:
        db.close()

@auth.route('/me', methods=['GET'])
@jwt_required()
def get_user_info():
    # Get user ID from JWT token
    user_id = get_jwt_identity()
    
    # Validate user ID
    if not user_id:
        return jsonify({'error': 'Invalid token: No user identity found'}), 401
    
    # Convert user_id to integer if it's a string
    try:
        if isinstance(user_id, str):
            user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
    
    # Log for debugging
    print(f"GET /me: User ID from JWT: {user_id} (type: {type(user_id).__name__})")
    
    # Get database connection
    db = get_db()
    try:
        # Get user via service
        user = AuthService.get_user_by_id(db, user_id)
        
        if not user:
            print(f"Error: User not found with ID: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        
        # Serialize user object
        result = AuthService.serialize_user(user)
        print(f"Returning user data for ID {user_id}")
        
        return jsonify(result), 200
    except Exception as e:
        import traceback
        print(f"Error in get_user_info: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Failed to retrieve user information'}), 500
    finally:
        db.close()
