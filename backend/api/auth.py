
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from services.auth_service import AuthService
from sqlalchemy import and_
from shared.models import User
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

auth = Blueprint('auth', __name__)

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
        
        # Send notification to admins
        try:
            # Get admin users
            admin_users = db.query(User).filter(
                and_(
                    User.role == 'admin',
                    User.status == 'approved'
                )
            ).all()
            
            # If at least one admin exists, set status to pending
            if admin_users:
                user.status = 'pending'
                db.commit()
                send_admin_notification(user)
                message = 'User created successfully. An administrator will review your account.'
            else:
                # If no admins exist yet, automatically approve the user
                user.status = 'approved'
                db.commit()
                message = 'User created successfully.'
        except Exception as e:
            print(f"Error notifying admins: {e}")
            message = 'User created successfully.'
        
        return jsonify({
            'message': message,
            'access_token': access_token,
            'user_id': user.id,
            'status': user.status
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
        result = AuthService.login_user(db, data['email'], data['password'])
        
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
