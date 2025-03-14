
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models.models import Base

# Load environment variables
load_dotenv()

# Get database connection string
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("WARNING: DATABASE_URL not found in environment variables.")
    print("Please set DATABASE_URL in your .env file.")
    # Use SQLite as fallback
    DATABASE_URL = 'sqlite:///lineup.db'
    print(f"Using fallback database: {DATABASE_URL}")
else:
    # Handle postgres:// vs postgresql:// URL format for SQLAlchemy
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        print("Converted DATABASE_URL from postgres:// to postgresql:// format")
    
    # Log connection info (without credentials)
    if 'postgresql' in DATABASE_URL:
        parts = DATABASE_URL.split('@')
        if len(parts) > 1:
            host_part = parts[1].split('/')[0]
            print(f"Using PostgreSQL database at: {host_part}")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Get database session
def get_db():
    """
    Returns a database session.
    This function should be used within a try/finally block 
    to ensure the session is properly closed.
    """
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e
