
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
    
    try:
        db = next(get_db())
        
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

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    db = next(get_db())
    
    # Login user via service
    user, access_token = AuthService.login_user(db, data['email'], data['password'])
    
    if not user or not access_token:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    return jsonify({
        'access_token': access_token,
        'user_id': user.id
    }), 200

@auth.route('/me', methods=['GET'])
@jwt_required()
def get_user_info():
    try:
        print("Headers:", request.headers)
        auth_header = request.headers.get('Authorization', '')
        print(f"Auth header: {auth_header}")
        
        user_id = get_jwt_identity()
        print(f"JWT identity: {user_id}")
        
        db = next(get_db())
        
        # Get user via service
        user = AuthService.get_user_by_id(db, user_id)
        
        if not user:
            print(f"User not found with ID: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        
        # Serialize user object
        result = AuthService.serialize_user(user)
        
        return jsonify(result), 200
    except Exception as e:
        import traceback
        print(f"Error in get_user_info: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
