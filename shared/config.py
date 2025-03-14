"""
Configuration settings for LineupBoss.

This module provides configuration settings for the application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base configuration
class Config:
    """Base configuration class."""
    
    # API configuration
    API_URL = os.getenv("API_URL", "http://localhost:5000/api")
    
    @classmethod
    def get_api_url(cls):
        """Get API URL from environment."""
        return cls.API_URL
    
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    @classmethod
    def get_database_url(cls):
        """Get database URL from environment."""
        db_url = cls.DATABASE_URL
            
        # Handle postgres:// vs postgresql:// format
        if db_url and db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        return db_url
    
    # Application configuration
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_key_not_secure")
    
    # JWT configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 30 * 24 * 60 * 60))  # 30 days by default

# Development configuration
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
# Production configuration
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
# Test configuration
class TestConfig(Config):
    """Test configuration."""
    DEBUG = True
    TESTING = True
    
# Get the current environment
ENV = os.getenv("FLASK_ENV", "development")

# Select the appropriate configuration based on environment
if ENV == "production":
    config = ProductionConfig
elif ENV == "testing":
    config = TestConfig
else:
    config = DevelopmentConfig