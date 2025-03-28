"""
Analytics module initialization.

This module exports the analytics blueprint for RESTful API endpoints.
"""
from flask import Blueprint

# Create the blueprint with unique name to avoid conflicts
# Use a completely different name to avoid any conflicts with existing route registrations
analytics_bp = Blueprint('analytics_v2', __name__)

# Import routes to register them with the blueprint
# This must come after the blueprint definition to avoid circular imports
from backend.api.analytics import routes