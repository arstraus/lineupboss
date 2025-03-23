"""
Analytics module initialization.

This module exports the analytics blueprint for RESTful API endpoints.
"""
# Import the routes module to ensure all routes are defined
from api.analytics.routes import analytics_bp

# Export the blueprint for import by the main API module
__all__ = ['analytics_bp']