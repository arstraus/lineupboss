"""
User API endpoints for LineupBoss.

This module provides API endpoints for user profile management.
"""
from flask import Blueprint, request, jsonify, g
from shared.models import User
from shared.database import db_session
from api.auth import token_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@token_required
def get_user_profile():
    """Get the current user's profile information."""
    user_id = g.user_id
    
    with db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "location": user.location,
            "role": user.role,
            "subscription_tier": user.subscription_tier,
            "created_at": user.created_at.isoformat() if user.created_at else None
        })

@users_bp.route('/profile', methods=['PUT'])
@token_required
def update_user_profile():
    """Update the current user's profile information."""
    user_id = g.user_id
    data = request.json
    
    # Validate input
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    with db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Update user fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'location' in data:
            user.location = data['location']
        if 'email' in data:
            # Check if email is already taken
            existing_user = session.query(User).filter(
                User.email == data['email'], 
                User.id != user_id
            ).first()
            
            if existing_user:
                return jsonify({"error": "Email already in use"}), 400
                
            user.email = data['email']
            
        session.commit()
        
        return jsonify({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "location": user.location,
            "role": user.role,
            "subscription_tier": user.subscription_tier,
            "created_at": user.created_at.isoformat() if user.created_at else None
        })

@users_bp.route('/password', methods=['PUT'])
@token_required
def update_password():
    """Update the current user's password."""
    user_id = g.user_id
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

@users_bp.route('/subscription', methods=['GET'])
@token_required
def get_subscription():
    """Get the current user's subscription information."""
    user_id = g.user_id
    
    with db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # For now, we're just returning basic subscription info
        return jsonify({
            "tier": user.subscription_tier,
            "features": get_tier_features(user.subscription_tier)
        })

def get_tier_features(tier):
    """Get the features available for a subscription tier."""
    tier = tier.lower()
    
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