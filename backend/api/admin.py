"""
Admin routes for managing users and application settings.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from database import db_session
from sqlalchemy import desc
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

from services.auth_service import AuthService
from models.models import User
from utils import standardize_error_response

# Placeholder until we update subscription tiers
ALL_TIERS = ["free", "basic", "pro", "team"]

admin = Blueprint('admin', __name__)

# Admin middleware to verify admin role
def admin_required(fn):
    """Decorator to verify the user has admin role.
    
    Uses standardized patterns:
    - Proper JWT verification
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Standardized error responses
    
    Similar to the new in-route feature checking pattern, but as a decorator 
    for admin-only routes where feature checks aren't needed.
    """
    @wraps(fn)  # Preserve the original function's name and metadata
    def admin_check(*args, **kwargs):
        from backend.utils import standardize_error_response
        
        try:
            # First verify JWT is present and valid
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # Convert user_id to int if it's a string
            try:
                if isinstance(user_id, str):
                    user_id = int(user_id)
            except ValueError:
                return standardize_error_response('Invalid user ID format', 400)
                
            # Using read_only mode since this is just a query operation
            with db_session(read_only=True) as session:
                user = AuthService.get_user_by_id(session, user_id)
                
                if not user:
                    return standardize_error_response('User not found', 404)
                    
                if user.role != 'admin':
                    return standardize_error_response(
                        'Admin access required', 
                        403,
                        {'required_role': 'admin', 'current_role': user.role}
                    )
                
                # Store user and user_id in Flask's g object for convenience
                from flask import g
                g.user_id = user_id
                g.user = user
                
                # Call the original function
                return fn(*args, **kwargs)
                
        except Exception as e:
            import traceback
            print(f"Error in admin_required: {str(e)}")
            print(traceback.format_exc())
            return standardize_error_response('Failed to verify admin access', 500, str(e))
            
    return admin_check

def send_email_notification(recipient_email, subject, message):
    """
    Send an email notification.
    
    Returns True if successful, False otherwise.
    """
    # Get email settings from environment variables
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    from_email = os.getenv('FROM_EMAIL', 'arstraus@gmail.com')
    
    # Skip if email settings are not configured
    if not smtp_user or not smtp_password:
        print("Email notification skipped: SMTP credentials not configured")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            
        print(f"Email notification sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email notification: {e}")
        return False

@admin.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users with optional filtering.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Structured error handling with db_error_response
    """
    status_filter = request.args.get('status', None)
    
    try:
        with db_session(read_only=True) as session:
            # Build query
            query = session.query(User)
            
            # Apply status filter if provided
            if status_filter:
                query = query.filter(User.status == status_filter)
                
            # Order by newest first
            query = query.order_by(User.created_at.desc())
            
            # Execute query
            users = query.all()
            result = [AuthService.serialize_user(user) for user in users]
            
            return jsonify(result), 200
                
    except Exception as e:
        print(f"Admin: error getting users: {e}")
        import traceback
        print(traceback.format_exc())
        # Use standardized error response
        return standardize_error_response("Failed to retrieve users", 500, str(e))

@admin.route('/approve/<int:user_id>', methods=['POST'])
@admin_required
def approve_user_legacy(user_id):
    """Legacy endpoint for approving a user. Redirects to the RESTful endpoint."""
    return approve_user(user_id)

@admin.route('/users/<int:user_id>/approve', methods=['POST'])
@admin_required
def approve_user(user_id):
    """Approve a user account.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with standardize_error_response
    """
    from backend.utils import standardize_error_response
    
    admin_id = get_jwt_identity()
    
    try:
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
    except ValueError:
        return standardize_error_response('Invalid admin ID format', 400)
        
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Get the user to approve
            user = AuthService.get_user_by_id(session, user_id)
            
            if not user:
                return standardize_error_response('User not found', 404)
                
            if user.status == 'approved':
                return jsonify({
                    'message': 'User already approved',
                    'user': AuthService.serialize_user(user)
                }), 200
                
            # Update user status
            user.status = 'approved'
            user.approved_at = datetime.now()
            user.approved_by = admin_id
            
            # Send email notification
            try:
                send_email_notification(
                    user.email,
                    'Your LineupBoss Account Has Been Approved',
                    f'Your LineupBoss account has been approved. You can now log in at {request.host_url}.'
                )
            except Exception as e:
                print(f"Failed to send approval email: {e}")
            
            return jsonify({
                'message': 'User approved successfully',
                'user': AuthService.serialize_user(user)
            }), 200
    except Exception as e:
        print(f"Error approving user: {e}")
        # Use standardized error response - no need to manually rollback
        return standardize_error_response('Failed to approve user', 500, str(e))

@admin.route('/reject/<int:user_id>', methods=['POST'])
@admin_required
def reject_user_legacy(user_id):
    """Legacy endpoint for rejecting a user. Redirects to the RESTful endpoint."""
    return reject_user(user_id)

@admin.route('/users/<int:user_id>/reject', methods=['POST'])
@admin_required
def reject_user(user_id):
    """Reject a user account.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with standardize_error_response
    """
    admin_id = get_jwt_identity()
    
    try:
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
    except ValueError:
        return standardize_error_response('Invalid admin ID format', 400)
        
    data = request.get_json() or {}
    reason = data.get('reason', 'Your account request has been rejected.')
        
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Get the user to reject
            user = AuthService.get_user_by_id(session, user_id)
            
            if not user:
                return standardize_error_response('User not found', 404)
                
            if user.status == 'rejected':
                return jsonify({
                    'message': 'User already rejected',
                    'user': AuthService.serialize_user(user)
                }), 200
                
            # Update user status
            user.status = 'rejected'
            user.approved_at = datetime.now()
            user.approved_by = admin_id
            
            # Send email notification
            try:
                send_email_notification(
                    user.email,
                    'Your LineupBoss Account Has Been Rejected',
                    f'Your LineupBoss account registration has been rejected.\n\nReason: {reason}'
                )
            except Exception as e:
                print(f"Failed to send rejection email: {e}")
            
            return jsonify({
                'message': 'User rejected successfully',
                'user': AuthService.serialize_user(user)
            }), 200
    except Exception as e:
        print(f"Error rejecting user: {e}")
        # Use standardized error response - no need to manually rollback
        return standardize_error_response("Failed to reject user", 500, str(e))

@admin.route('/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    """Update a user's role.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with standardize_error_response
    - Role validation
    """
    admin_id = get_jwt_identity()
    
    try:
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
    except ValueError:
        return standardize_error_response('Invalid admin ID format', 400)
        
    data = request.get_json()
    
    if not data or not data.get('role'):
        return standardize_error_response('Role is required', 400)
        
    role = data['role']
    if role not in ['admin', 'user']:
        return standardize_error_response('Invalid role. Must be "admin" or "user"', 400, {'valid_roles': ['admin', 'user']})
        
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Get the user to update
            user = AuthService.get_user_by_id(session, user_id)
            
            if not user:
                return standardize_error_response('User not found', 404)
                
            # Don't allow changing own role
            if user_id == admin_id:
                return standardize_error_response('Cannot change your own role', 403)
                
            # Update user role
            user.role = role
            
            return jsonify({
                'message': 'User role updated successfully',
                'user': AuthService.serialize_user(user)
            }), 200
    except Exception as e:
        print(f"Error updating user role: {e}")
        # Use standardized error response - no need to manually rollback
        return standardize_error_response("Failed to update user role", 500, str(e))

@admin.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user account.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with standardize_error_response
    """
    admin_id = get_jwt_identity()
    
    try:
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
    except ValueError:
        return standardize_error_response('Invalid admin ID format', 400)
        
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Get the user to delete
            user = AuthService.get_user_by_id(session, user_id)
            
            if not user:
                return standardize_error_response('User not found', 404)
                
            # Don't allow admin to delete themselves
            if user_id == admin_id:
                return standardize_error_response('Cannot delete your own account', 403)
                
            # Delete user
            session.delete(user)
            
            return jsonify({
                'message': 'User deleted successfully',
                'user_id': user_id
            }), 200
    except Exception as e:
        print(f"Error deleting user: {e}")
        # Use standardized error response - no need to manually rollback
        return standardize_error_response("Failed to delete user", 500, str(e))


@admin.route('/pending-users', methods=['GET'])
@admin_required
def get_pending_users_legacy():
    """Legacy endpoint to get all pending users.
    
    Redirects to get_users with status=pending filter, maintaining backward compatibility.
    """
    # Construct a modified request.args with status=pending
    from werkzeug.datastructures import ImmutableMultiDict
    args = request.args.copy()
    args['status'] = 'pending'
    request.args = ImmutableMultiDict(args)
    
    return get_users()

@admin.route('/users/<int:user_id>/subscription', methods=['PUT'])
@admin_required
def update_user_subscription(user_id):
    """Update a user's subscription tier.
    
    Uses standardized database access patterns:
    - db_session context manager with automatic commit
    - Structured error handling with standardize_error_response
    - Tier validation
    """
    admin_id = get_jwt_identity()
    
    try:
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
    except ValueError:
        return standardize_error_response('Invalid admin ID format', 400)
        
    data = request.get_json()
    
    if not data or not data.get('subscription_tier'):
        return standardize_error_response('Subscription tier is required', 400)
        
    tier = data['subscription_tier']
    if tier not in ALL_TIERS:
        return standardize_error_response(
            'Invalid subscription tier',
            400,
            {'valid_tiers': ALL_TIERS}
        )
        
    try:
        # Using commit=True to automatically commit successful operations
        with db_session(commit=True) as session:
            # Get the user to update
            user = AuthService.get_user_by_id(session, user_id)
            
            if not user:
                return standardize_error_response('User not found', 404)
                
            # Update user subscription tier
            previous_tier = user.subscription_tier
            user.subscription_tier = tier
            
            # Send email notification
            try:
                send_email_notification(
                    user.email,
                    'Your LineupBoss Subscription Has Been Updated',
                    f'Your LineupBoss subscription has been updated from {previous_tier} to {tier} tier.\n\n'
                    f'Please log in to see your updated features and capabilities.'
                )
            except Exception as e:
                print(f"Failed to send subscription update email: {e}")
            
            return jsonify({
                'message': 'User subscription tier updated successfully',
                'user': AuthService.serialize_user(user),
                'previous_tier': previous_tier,
                'new_tier': tier
            }), 200
    except Exception as e:
        print(f"Error updating user subscription: {e}")
        # Use standardized error response - no need to manually rollback
        return standardize_error_response('Failed to update user subscription', 500, str(e))

@admin.route('/pending-count', methods=['GET'])
@admin_required
def get_pending_count():
    """Get the count of pending user registrations.
    
    Uses standardized database access patterns:
    - db_session context manager for automatic cleanup
    - Read-only operation (no commits needed)
    - Structured error handling with db_error_response
    - Optimized query using SQL COUNT directly
    """
    try:
        # Using read_only mode since this is just a query operation
        with db_session(read_only=True) as session:
            # Optimized: Use SQL COUNT directly with specific column to avoid full row fetch
            from sqlalchemy import func
            count = session.query(func.count(User.id)).filter(User.status == 'pending').scalar()
            
            return jsonify({
                'pending_count': count
            }), 200
    except Exception as e:
        print(f"Error getting pending count: {e}")
        # Use standardized error response
        return standardize_error_response("Failed to get pending count", 500, str(e))
