"""
Migration script to add role and approval status fields to User model.
"""
import sys
import os
import importlib.util
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, create_engine, text
from sqlalchemy.orm import sessionmaker

# Add both parent directory and project root to path so we can import modules
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
root_dir = os.path.abspath(os.path.join(backend_dir, '..'))
sys.path.insert(0, backend_dir)
sys.path.insert(0, root_dir)

# Import models directly
from shared.models import Base, User

# Set the database URL (using your PostgreSQL database)
DATABASE_URL = "postgresql://Lineup_owner:npg_SyQnjbA8v2Yp@ep-hidden-pond-a6lv5bdn-pooler.us-west-2.aws.neon.tech/Lineup?sslmode=require"

# Handle Postgres URL format (for Heroku)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def migrate():
    """Apply the migration to add role and status fields to the User model."""
    print("Starting migration: adding role and approval fields to User model")
    
    # Create direct database connection instead of using generator
    db = SessionLocal()
    
    try:
        # Add role column if it doesn't exist
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user' NOT NULL"))
            print("Added 'role' column to users table")
        except Exception as e:
            print(f"Error adding 'role' column: {e}")
        
        # Add status column if it doesn't exist
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'pending' NOT NULL"))
            print("Added 'status' column to users table")
        except Exception as e:
            print(f"Error adding 'status' column: {e}")
        
        # Add approved_at column if it doesn't exist
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP"))
            print("Added 'approved_at' column to users table")
        except Exception as e:
            print(f"Error adding 'approved_at' column: {e}")
        
        # Add approved_by column if it doesn't exist
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES users(id)"))
            print("Added 'approved_by' column to users table")
        except Exception as e:
            print(f"Error adding 'approved_by' column: {e}")
        
        # Set the first user to be an admin
        try:
            result = db.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
            first_user = result.fetchone()
            if first_user:
                db.execute(text(f"UPDATE users SET role = 'admin', status = 'approved' WHERE id = {first_user[0]}"))
                print(f"Set user with ID {first_user[0]} as admin")
            else:
                print("No users found, skipping admin setup")
        except Exception as e:
            print(f"Error setting admin user: {e}")
        
        db.commit()
        print("Migration completed successfully")
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()