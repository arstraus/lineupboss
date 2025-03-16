"""
Admin routes for managing users and application settings.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from sqlalchemy import desc
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from services.auth_service import AuthService

admin = Blueprint('admin', __name__)

# Admin middleware to verify admin role
def admin_required(fn):
    """Decorator to verify the user has admin role."""
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        
        try:
            if isinstance(user_id, str):
                user_id = int(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid user ID format'}), 400
            
        db = get_db()
        try:
            user = AuthService.get_user_by_id(db, user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            if user.role != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
                
            return fn(*args, **kwargs)
        finally:
            db.close()
            
    return wrapper

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
    """Get all users with optional filtering."""
    status_filter = request.args.get('status', None)
    
    db = get_db()
    try:
        query = db.query(AuthService.User)
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter(AuthService.User.status == status_filter)
            
        # Order by newest first
        query = query.order_by(desc(AuthService.User.created_at))
        
        users = query.all()
        result = [AuthService.serialize_user(user) for user in users]
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({'error': f'Failed to retrieve users: {str(e)}'}), 500
    finally:
        db.close()

@admin.route('/users/<int:user_id>/approve', methods=['POST'])
@admin_required
def approve_user(user_id):
    """Approve a user account."""
    admin_id = get_jwt_identity()
    
    try:
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
    except ValueError:
        return jsonify({'error': 'Invalid admin ID format'}), 400
        
    db = get_db()
    try:
        # Get the user to approve
        user = AuthService.get_user_by_id(db, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if user.status == 'approved':
            return jsonify({'message': 'User already approved'}), 200
            
        # Update user status
        user.status = 'approved'
        user.approved_at = datetime.now()
        user.approved_by = admin_id
        
        db.commit()
        
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
        db.rollback()
        print(f"Error approving user: {e}")
        return jsonify({'error': f'Failed to approve user: {str(e)}'}), 500
    finally:
        db.close()

@admin.route('/users/<int:user_id>/reject', methods=['POST'])
@admin_required
def reject_user(user_id):
    """Reject a user account."""
    admin_id = get_jwt_identity()
    
    try:
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
    except ValueError:
        return jsonify({'error': 'Invalid admin ID format'}), 400
        
    data = request.get_json() or {}
    reason = data.get('reason', 'Your account request has been rejected.')
        
    db = get_db()
    try:
        # Get the user to reject
        user = AuthService.get_user_by_id(db, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if user.status == 'rejected':
            return jsonify({'message': 'User already rejected'}), 200
            
        # Update user status
        user.status = 'rejected'
        user.approved_at = datetime.now()
        user.approved_by = admin_id
        
        db.commit()
        
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
        db.rollback()
        print(f"Error rejecting user: {e}")
        return jsonify({'error': f'Failed to reject user: {str(e)}'}), 500
    finally:
        db.close()

@admin.route('/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    """Update a user's role."""
    admin_id = get_jwt_identity()
    
    try:
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
    except ValueError:
        return jsonify({'error': 'Invalid admin ID format'}), 400
        
    data = request.get_json()
    
    if not data or not data.get('role'):
        return jsonify({'error': 'Role is required'}), 400
        
    role = data['role']
    if role not in ['admin', 'user']:
        return jsonify({'error': 'Invalid role. Must be "admin" or "user"'}), 400
        
    db = get_db()
    try:
        # Get the user to update
        user = AuthService.get_user_by_id(db, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Don't allow changing own role
        if user_id == admin_id:
            return jsonify({'error': 'Cannot change your own role'}), 403
            
        # Update user role
        user.role = role
        
        db.commit()
        
        return jsonify({
            'message': 'User role updated successfully',
            'user': AuthService.serialize_user(user)
        }), 200
    except Exception as e:
        db.rollback()
        print(f"Error updating user role: {e}")
        return jsonify({'error': f'Failed to update user role: {str(e)}'}), 500
    finally:
        db.close()

@admin.route('/pending-count', methods=['GET'])
@admin_required
def get_pending_count():
    """Get the count of pending user registrations."""
    db = get_db()
    try:
        count = db.query(AuthService.User).filter(AuthService.User.status == 'pending').count()
        
        return jsonify({
            'pending_count': count
        }), 200
    except Exception as e:
        print(f"Error getting pending count: {e}")
        return jsonify({'error': f'Failed to get pending count: {str(e)}'}), 500
    finally:
        db.close()