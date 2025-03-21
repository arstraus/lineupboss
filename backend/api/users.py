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
    
    try:
        # Use read-only session for better performance
        with db_session(read_only=True) as session:
            # Use a selective query to get only the needed columns
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            # Directly serialize the user data without excess logging
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
            
            return jsonify(response_data)
    except Exception as e:
        # Simplified error handling
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@users_bp.route('/profile', methods=['PUT'])
@token_required
def update_user_profile():
    """Update the current user's profile information."""
    user_id = g.user_id
    
    # Log detailed information
    print("*** PROFILE UPDATE STARTED ***")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    print(f"User ID: {user_id}")
    
    try:
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

@users_bp.route('/password', methods=['PUT'])
@token_required
def update_password():
    """Update the current user's password."""
    user_id = g.user_id
    
    # Log detailed information
    print("*** PASSWORD UPDATE STARTED ***")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    print(f"User ID: {user_id}")
    
    try:
        data = request.json
        
        # Validate input (don't log passwords)
        if not data or 'current_password' not in data or 'new_password' not in data:
            print("Error: Missing required password fields")
            return jsonify({"error": "Current password and new password required"}), 400
            
        with db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                print(f"Error: User {user_id} not found")
                return jsonify({"error": "User not found"}), 404
                
            print(f"Found user: {user.email}")
                
            # Verify current password
            if not user.check_password(data['current_password']):
                print("Error: Current password is incorrect")
                return jsonify({"error": "Current password is incorrect"}), 400
                
            # Update password
            user.set_password(data['new_password'])
            session.commit()
            print("Password updated successfully")
            
            print("*** PASSWORD UPDATE COMPLETED SUCCESSFULLY ***")
            return jsonify({"message": "Password updated successfully"})
    except Exception as e:
        print(f"*** PASSWORD UPDATE ERROR: {str(e)} ***")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@users_bp.route('/subscription', methods=['GET'])
@token_required
def get_subscription():
    """Get the current user's subscription information."""
    user_id = g.user_id
    
    # Log detailed information
    print("*** SUBSCRIPTION INFO REQUEST STARTED ***")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    print(f"User ID: {user_id}")
    
    try:
        with db_session() as session:
            print("Database session created")
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                print(f"Error: User {user_id} not found")
                return jsonify({"error": "User not found"}), 404
                
            print(f"Found user: {user.email} with subscription tier: {user.subscription_tier}")
            
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

# Add a simple test endpoint to verify the users blueprint is registered correctly
@users_bp.route('/test', methods=['GET'])
def test_users_endpoint():
    """Test endpoint to verify users blueprint is registered correctly."""
    return jsonify({"message": "Users API is working"})