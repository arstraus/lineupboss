"""
Analytics module initialization.

This module exports the analytics blueprint for RESTful API endpoints.
"""
# Import the routes module to ensure all routes are defined
from api.analytics.routes import analytics_bp

# Make sure RESTful endpoints are registered and available for import
analytics_bp.name = 'analytics_restful'

# Export the blueprint for import by the main API module
__all__ = ['analytics_bp']

# Include an additional variable to explicitly check for successful import
ANALYTICS_MODULE_LOADED = True