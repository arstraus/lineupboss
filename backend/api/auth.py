
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from flask_jwt_extended.exceptions import NoAuthorizationError
from functools import wraps
from datetime import datetime, timedelta, timezone
from shared.database import db_session, db_error_response, db_get_or_404
from services.auth_service import AuthService
from sqlalchemy import and_
from shared.models import User
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

auth = Blueprint('auth', __name__)

# Token expiration settings
ACCESS_TOKEN_EXPIRES = timedelta(days=15)  # Reduced from 30 days
REFRESH_MARGIN = timedelta(days=7)  # Refresh tokens that will expire in 7 days

def token_required(f):
    """
    A decorator that wraps the flask_jwt_extended.jwt_required decorator
    and ensures the user ID is available in the request context.
    
    This standardizes authentication across the application by:
    1. Using the flask_jwt_extended library for token validation
    2. Converting the JWT identity to an integer if necessary
    3. Storing the user ID in Flask's g object for access in route functions
    
    Usage:
        @token_required
        def my_route():
            user_id = g.user_id  # Access the user ID from the JWT token
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Convert to integer if string
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                return jsonify({"error": "Invalid user ID format"}), 400
        
        # Store in Flask's g object for the duration of the request
        g.user_id = user_id
        
        return f(*args, **kwargs)
    
    return decorated

def send_admin_notification(new_user):
    """Send email notification to admin users about new registration."""
    # Get email settings from environment variables
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    from_email = os.getenv('FROM_EMAIL', 'arstraus@gmail.com')
    admin_email = os.getenv('ADMIN_EMAIL', 'arstraus@gmail.com')
    
    # Skip if email settings are not configured
    if not smtp_user or not smtp_password or not admin_email:
        print("Admin notification skipped: Email credentials not configured")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = admin_email
        msg['Subject'] = 'New User Registration Requires Approval'
        
        # Add message body
        message = f"""
A new user has registered for LineupBoss and requires your approval:

Email: {new_user.email}
User ID: {new_user.id}
Registered: {new_user.created_at}

Please log in to the admin dashboard to approve or reject this user.
"""
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            
        print(f"Admin notification sent to {admin_email}")
        return True
    except Exception as e:
        print(f"Failed to send admin notification: {e}")
        return False

@auth.route('/register', methods=['POST'])
def register():
    """Register a new user.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Structured error handling
    - Clear transaction boundaries
    """
    print("Register endpoint hit")
    data = request.get_json()
    print(f"Received data: {data}")
    
    # Input validation
    if not data or not data.get('email') or not data.get('password'):
        print("Missing email or password")
        return jsonify({'error': 'Email and password are required'}), 400
    
    try:
        # Use the enhanced context manager with automatic commit
        with db_session(commit=True) as session:
            # Check if user already exists
            existing_user = AuthService.get_user_by_email(session, data['email'])
            if existing_user:
                print(f"User already exists with email: {data['email']}")
                return jsonify({'error': 'Email already registered'}), 409
            
            # Register user via service
            print(f"Registering new user with email: {data['email']}")
            user, access_token = AuthService.register_user(session, data['email'], data['password'])
            print(f"User registered successfully with ID: {user.id}")
            
            # Process user status based on admin presence
            message = 'User created successfully.'
            
            # Get admin users
            admin_users = session.query(User).filter(
                and_(
                    User.role == 'admin',
                    User.status == 'approved'
                )
            ).all()
            
            # If at least one admin exists, set status to pending
            if admin_users:
                user.status = 'pending'
                send_admin_notification(user)
                # Don't return an access token if user is pending
                access_token = None
                message = 'User created successfully. An administrator will review your account. You will receive an email when your account is approved.'
            else:
                # If no admins exist yet, automatically approve the user
                user.status = 'approved'
                
            # The commit happens automatically when exiting the context manager
            # No need for explicit commit
            
            return jsonify({
                'message': message,
                'access_token': access_token,
                'user_id': user.id,
                'status': user.status
            }), 201
            
    except Exception as e:
        print(f"Error during registration: {str(e)}")
        # Use the standardized error response utility
        from shared.database import db_error_response
        return db_error_response(e, "Registration failed. Please try again later.")

@auth.route('/login', methods=['POST'])
def login():
    """Login a user.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Structured error handling
    """
    data = request.get_json()
    
    # Input validation
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    try:
        # Using read_only mode since login is just a query operation
        with db_session(read_only=True) as session:
            # Login user via service
            result = AuthService.login_user(session, data['email'], data['password'])
            
            # Unpack result based on number of return values
            if len(result) == 3:
                user, access_token, status_message = result
                # User exists but is not approved
                return jsonify({
                    'error': status_message,
                    'status': user.status,
                    'user_id': user.id
                }), 403
            else:
                user, access_token = result
                
            if not user or not access_token:
                return jsonify({'error': 'Invalid email or password'}), 401
            
            return jsonify({
                'access_token': access_token,
                'user_id': user.id,
                'role': user.role,
                'status': user.status
            }), 200
            
    except Exception as e:
        print(f"Error during login: {str(e)}")
        # Use the standardized error response utility
        from shared.database import db_error_response
        return db_error_response(e, "Login failed. Please try again later.")

@auth.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """Refresh JWT access token if it's approaching expiration.
    
    This endpoint allows the client to proactively refresh their access token
    before it expires, providing a seamless authentication experience.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Standardized error handling
    """
    # Get the JWT data
    try:
        jwt_data = get_jwt()
        user_id = get_jwt_identity()
        
        # Convert user_id to integer if it's a string
        if isinstance(user_id, str):
            user_id = int(user_id)
            
        # Extract expiration time
        exp_timestamp = jwt_data.get('exp')
        current_time = datetime.now(timezone.utc)
        
        # Calculate when the token will expire
        if exp_timestamp:
            exp_time = datetime.fromtimestamp(exp_timestamp, timezone.utc)
            time_until_expiry = exp_time - current_time
            
            # Only refresh if token will expire within REFRESH_MARGIN
            if time_until_expiry > REFRESH_MARGIN:
                return jsonify({
                    'message': 'Token is still valid, no refresh needed',
                    'valid_until': exp_time.isoformat(),
                    'time_until_expiry_days': time_until_expiry.days
                }), 200
                
        # Verify user exists and is active before refreshing
        with db_session(read_only=True) as session:
            user = AuthService.get_user_by_id(session, user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            if user.role != "admin" and user.status != "approved":
                return jsonify({'error': f'Account is {user.status}'}), 403
            
            # Generate fresh token with same identity
            new_token = create_access_token(
                identity=str(user_id),  # Maintain string format for consistency
                expires_delta=ACCESS_TOKEN_EXPIRES
            )
            
            # Calculate new expiration for client info
            new_exp = (datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRES).isoformat()
            
            print(f"Token refreshed for user ID: {user_id}")
            return jsonify({
                'access_token': new_token,
                'expires_at': new_exp,
                'user_id': user_id
            }), 200
    except NoAuthorizationError:
        return jsonify({'error': 'Missing or invalid authorization header'}), 401
    except Exception as e:
        print(f"Error refreshing token: {str(e)}")
        return db_error_response(e, "Failed to refresh token")

@auth.route('/me', methods=['GET'])
@jwt_required()
def get_user_info():
    """Get the current user's info from JWT token.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Standardized error handling
    - Built-in JWT validation
    """
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
    
    try:
        # Using read_only mode since this is just a query operation
        with db_session(read_only=True) as session:
            # Try to use the utility function to get the user
            from shared.database import db_get_or_404
            from shared.models import User
            
            try:
                # This will automatically return 404 if user not found
                user = db_get_or_404(session, User, user_id, "User not found")
            except Exception:
                # If db_get_or_404 aborts, we need to handle it here
                # Fall back to manual checking to return proper JSON response
                user = AuthService.get_user_by_id(session, user_id)
                if not user:
                    print(f"Error: User not found with ID: {user_id}")
                    return jsonify({'error': 'User not found'}), 404
            
            # Serialize user object
            result = AuthService.serialize_user(user)
            print(f"Returning user data for ID {user_id}")
            
            # Add token refresh info
            try:
                jwt_data = get_jwt()
                exp_timestamp = jwt_data.get('exp')
                if exp_timestamp:
                    exp_time = datetime.fromtimestamp(exp_timestamp, timezone.utc)
                    current_time = datetime.now(timezone.utc)
                    time_until_expiry = exp_time - current_time
                    
                    # Add refresh hint if token will expire soon
                    if time_until_expiry <= REFRESH_MARGIN:
                        result['token_expires_soon'] = True
                        result['token_expires_at'] = exp_time.isoformat()
                    else:
                        result['token_expires_soon'] = False
            except Exception as e:
                print(f"Error calculating token expiry: {e}")
            
            return jsonify(result), 200
            
    except Exception as e:
        import traceback
        print(f"Error in get_user_info: {str(e)}")
        print(traceback.format_exc())
        
        # Use the standardized error response utility
        from shared.database import db_error_response
        return db_error_response(e, "Failed to retrieve user information.")
