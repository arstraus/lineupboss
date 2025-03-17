"""
Add user profile fields migration script.

This script adds new profile and subscription fields to the users table:
- first_name: String, nullable
- last_name: String, nullable
- location: String, nullable
- subscription_tier: String, default 'rookie'
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.sql import text
from dotenv import load_dotenv

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()
load_dotenv('.env.test')  # Load test env if available

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('migrations')

def get_database_url():
    """Get database URL from environment variables."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    return database_url

def create_engine_with_retry(database_url, max_retries=3):
    """Create a database engine with retry logic."""
    connect_args = {}
    if database_url.startswith("postgresql"):
        connect_args = {
            "sslmode": "require",
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=30
    )
    
    # Test connection with retry
    retry_count = 0
    while retry_count < max_retries:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection established successfully")
                return engine
        except Exception as e:
            retry_count += 1
            logger.warning(f"Connection attempt {retry_count} failed: {str(e)}")
            if retry_count >= max_retries:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise
    
    return engine

def add_user_profile_fields():
    """Add profile fields to users table."""
    try:
        # Get database URL and create engine
        database_url = get_database_url()
        engine = create_engine_with_retry(database_url)
        
        # Get engine and connection
        with engine.connect() as conn:
            # Check if first_name column exists in users table
            result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'first_name'
            """))
            
            has_first_name = result.rowcount > 0
            
            # Check if subscription_tier column exists
            result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'subscription_tier'
            """))
            
            has_subscription_tier = result.rowcount > 0
            
            # Add columns if they don't exist
            if not has_first_name:
                conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN first_name VARCHAR,
                ADD COLUMN last_name VARCHAR,
                ADD COLUMN location VARCHAR
                """))
                logger.info("Added name and location fields to users table")
            else:
                logger.info("Name and location fields already exist in users table")
            
            if not has_subscription_tier:
                conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN subscription_tier VARCHAR DEFAULT 'rookie' NOT NULL
                """))
                logger.info("Added subscription_tier field to users table")
            else:
                logger.info("Subscription_tier field already exists in users table")
            
            conn.commit()
            
        return True
    except Exception as e:
        logger.error(f"Error in migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_user_profile_fields()
    if success:
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
        sys.exit(1)