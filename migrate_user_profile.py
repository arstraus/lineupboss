"""
Simple migration script to add user profile fields to the database.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('migration')

def run_migration():
    """Add profile fields to users table."""
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment")
        return False
    
    # Fix the URL if needed
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    logger.info(f"Connecting to database at {database_url.split('@')[1] if '@' in database_url else '(hidden)'}")
    
    # Create engine with SSL required for Neon database
    try:
        engine = create_engine(
            database_url,
            connect_args={"sslmode": "require"},
            echo=False
        )
        
        # Test connection
        with engine.connect() as conn:
            logger.info("Database connection successful")
            
            # Check if first_name column exists
            result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'first_name'
            """))
            rows = result.fetchall()
            has_first_name = len(rows) > 0
            
            # Check if subscription_tier column exists
            result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'subscription_tier'
            """))
            rows = result.fetchall()
            has_subscription_tier = len(rows) > 0
            
            # Add columns if they don't exist
            if not has_first_name:
                logger.info("Adding name and location fields to users table")
                conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN first_name VARCHAR,
                ADD COLUMN last_name VARCHAR,
                ADD COLUMN location VARCHAR
                """))
            else:
                logger.info("Name fields already exist, skipping")
            
            if not has_subscription_tier:
                logger.info("Adding subscription_tier field to users table")
                conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN subscription_tier VARCHAR DEFAULT 'rookie' NOT NULL
                """))
            else:
                logger.info("Subscription tier field already exists, skipping")
            
            conn.commit()
            
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)