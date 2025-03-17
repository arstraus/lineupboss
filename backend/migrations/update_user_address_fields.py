"""
Update user address fields migration script.

This script replaces the single 'location' field with more structured address fields:
- Remove: location
- Add: city, state, country, zip_code
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

def update_user_address_fields():
    """Replace location field with detailed address fields."""
    try:
        # Get database URL and create engine
        database_url = get_database_url()
        engine = create_engine_with_retry(database_url)
        
        # Create a fresh connection with autocommit mode
        connection = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
        
        try:
            # Check if location column exists in users table
            result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'location'
            """))
            
            rows = result.fetchall()
            has_location = len(rows) > 0
            logger.info(f"Location column exists: {has_location}")
            
            # Check if city column exists
            result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'city'
            """))
            
            rows = result.fetchall()
            has_city = len(rows) > 0
            logger.info(f"City column exists: {has_city}")
            
            # Process based on what we found
            if has_location and not has_city:
                # Add new columns
                logger.info("Adding city, state, country, and zip_code columns")
                connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN city VARCHAR,
                ADD COLUMN state VARCHAR,
                ADD COLUMN country VARCHAR DEFAULT 'USA',
                ADD COLUMN zip_code VARCHAR
                """))
                logger.info("Added city, state, country, and zip_code fields to users table")
                
                # Move location data to state as a temporary measure
                logger.info("Copying location data to state field")
                connection.execute(text("""
                UPDATE users 
                SET state = location
                WHERE location IS NOT NULL
                """))
                logger.info("Copied location data to state field")
                
                # Remove the old location column
                logger.info("Dropping location column")
                connection.execute(text("""
                ALTER TABLE users 
                DROP COLUMN location
                """))
                logger.info("Removed location field from users table")
            elif not has_location and not has_city:
                # Add new columns if neither location nor city exists
                logger.info("Adding city, state, country, and zip_code columns")
                connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN city VARCHAR,
                ADD COLUMN state VARCHAR,
                ADD COLUMN country VARCHAR DEFAULT 'USA',
                ADD COLUMN zip_code VARCHAR
                """))
                logger.info("Added city, state, country, and zip_code fields to users table")
            elif has_city:
                logger.info("Address fields already exist in users table")
            
            logger.info("Migration executed successfully")
        finally:
            # Always close the connection
            connection.close()
            
        return True
    except Exception as e:
        logger.error(f"Error in migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_user_address_fields()
    if success:
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
        sys.exit(1)