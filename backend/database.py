
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
    Returns a generator for a database session.
    
    Instead of using 'yield' which requires a context manager,
    we're putting the session in a list and returning an iterator.
    """
    db = SessionLocal()
    try:
        return iter([db])
    except Exception as e:
        db.close()
        raise e
