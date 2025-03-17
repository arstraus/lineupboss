"""
Authentication service for handling user-related business logic.
"""
from sqlalchemy.orm import Session
from flask_jwt_extended import create_access_token
from datetime import timedelta
from shared.models import User
from shared import auth as shared_auth

class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def register_user(db: Session, email: str, password: str):
        """
        Register a new user.
        
        Args:
            db: Database session
            email: User email
            password: User password
            
        Returns:
            Tuple of (user, access_token)
        """
        # Create new user
        user = User(email=email)
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create access token with 30-day expiration - convert user ID to string
        access_token = create_access_token(
            identity=str(user.id),  # Convert to string to prevent JWT validation errors
            expires_delta=timedelta(days=30)
        )
        
        print(f"Register: Generated token for user {user.id}")
        
        return user, access_token
    
    @staticmethod
    def login_user(db: Session, email: str, password: str):
        """
        Login a user.
        
        Args:
            db: Database session
            email: User email
            password: User password
            
        Returns:
            Tuple of (user, access_token) if credentials are valid, None otherwise
            Returns (user, None, "status_message") if user exists but is not approved
        """
        # Check user credentials
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"Login failed: No user found with email {email}")
            return None, None
            
        if not user.check_password(password):
            print(f"Login failed: Invalid password for user {email}")
            return None, None
            
        # Check user status (unless they're an admin)
        if user.role != "admin" and user.status != "approved":
            status_message = f"Your account is {user.status}. Please wait for administrator approval."
            print(f"Login rejected: User {email} is {user.status}")
            return user, None, status_message
        
        # Create access token with 30-day expiration - convert user ID to string
        access_token = create_access_token(
            identity=str(user.id),  # Convert to string to prevent JWT validation errors
            expires_delta=timedelta(days=30)
        )
        
        print(f"Login successful for user {user.id}, token generated")
        
        return user, access_token
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        """
        Get a user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()
        
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def serialize_user(user: User):
        """
        Serialize a user object to a dictionary.
        
        Args:
            user: User object
            
        Returns:
            Dictionary representing the user
        """
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'location': user.location,
            'role': user.role,
            'status': user.status,
            'subscription_tier': user.subscription_tier,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'approved_at': user.approved_at.isoformat() if user.approved_at else None
        }